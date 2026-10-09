import os
import re
import time
import queue
import logging
import tempfile
import wave
import threading
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List

import numpy as np

from .config import CONFIG, DesktopConfig
from .audio_capture import AudioCaptureEngine
from .api_client import MeetingApiClient, WorkflowAnalysisResult

logger = logging.getLogger(__name__)

# Try importing faster-whisper
HAVE_WHISPER = False
try:
    from faster_whisper import WhisperModel
    HAVE_WHISPER = True
except Exception as e:
    logger.warning(f"faster-whisper import error: {e}")


class MeetingTranscriptSegment:
    def __init__(self, segment_id: int, timestamp: str, text: str, duration_sec: float = 0.0):
        self.segment_id = segment_id
        self.timestamp = timestamp
        self.text = text
        self.duration_sec = duration_sec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.segment_id,
            "timestamp": self.timestamp,
            "text": self.text,
            "duration": self.duration_sec
        }


class MeetingManager:
    """
    Core orchestrator coordinating:
    - Audio capture and pause segmentation (AudioCaptureEngine)
    - Background Whisper speech-to-text worker
    - Incremental ordered transcript accumulation
    - Deduplication & punctuation preservation
    - FastAPI LangGraph meeting analysis submission
    - Thread-safe UI state updates
    """

    def __init__(
        self,
        config: Optional[DesktopConfig] = None,
        on_state_changed: Optional[Callable[[str, str], None]] = None,
        on_segment_added: Optional[Callable[[Dict[str, Any], str], None]] = None,
        on_dictation_ready: Optional[Callable[[str], None]] = None,
        on_analysis_complete: Optional[Callable[[WorkflowAnalysisResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ):
        self.config = config or CONFIG
        
        # Callbacks
        self.on_state_changed = on_state_changed
        self.on_segment_added = on_segment_added
        self.on_dictation_ready = on_dictation_ready
        self.on_analysis_complete = on_analysis_complete
        self.on_error = on_error
        self.on_audio_level = on_audio_level

        # State
        self.current_state = "loading"  # loading, idle, listening, transcribing, finalizing, analyzing, completed, error
        self.state_detail = "Initializing..."
        self.active_mode = "dictation"  # dictation or meeting
        
        # Whisper model
        self.whisper_model: Optional[Any] = None
        self._whisper_lock = threading.Lock()
        
        # Transcription queue
        self._transcription_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_worker_event = threading.Event()
        
        # Cumulative meeting transcript storage
        self.segments: List[MeetingTranscriptSegment] = []
        self._cumulative_text: str = ""
        self._segment_counter: int = 0
        self._processed_audio_hashes = set()
        self._transcript_lock = threading.Lock()
        
        # Meeting metadata
        self.meeting_title: str = ""
        self.meeting_start_time: Optional[datetime] = None
        self.last_analysis_result: Optional[WorkflowAnalysisResult] = None
        
        # Backend API Client
        self.api_client = MeetingApiClient(base_url=self.config.BACKEND_URL)
        
        # Audio capture engine
        self.audio_engine = AudioCaptureEngine(
            rate=self.config.AUDIO_RATE,
            channels=self.config.AUDIO_CHANNELS,
            block_size=self.config.AUDIO_BLOCK_SIZE,
            dictation_silence_threshold=self.config.DICTATION_SILENCE_THRESHOLD,
            dictation_pause_sec=self.config.DICTATION_PAUSE_SEC,
            meeting_silence_threshold=self.config.MEETING_SILENCE_THRESHOLD,
            meeting_pause_sec=self.config.MEETING_PAUSE_SEC,
            meeting_min_segment_sec=self.config.MEETING_MIN_SEGMENT_SEC,
            meeting_max_buffer_sec=self.config.MEETING_MAX_BUFFER_SEC,
            on_speech_segment=self._handle_incoming_speech_segment,
            on_dictation_complete=self._handle_dictation_complete,
            on_audio_level=self._handle_audio_level,
            on_error=self._handle_engine_error,
        )

    def initialize(self) -> bool:
        """Initializes Whisper STT model and starts the background transcription worker"""
        self._set_state("loading", "Loading Whisper STT model...")
        try:
            if HAVE_WHISPER:
                logger.info(f"Loading faster-whisper ({self.config.WHISPER_MODEL})...")
                with self._whisper_lock:
                    self.whisper_model = WhisperModel(
                        self.config.WHISPER_MODEL,
                        device=self.config.WHISPER_DEVICE,
                        compute_type=self.config.WHISPER_COMPUTE_TYPE
                    )
                logger.info("Whisper model loaded successfully.")
            else:
                logger.warning("faster-whisper is not available; running in mock/fallback mode.")

            # Start transcription worker thread
            self._stop_worker_event.clear()
            self._worker_thread = threading.Thread(target=self._transcription_worker_loop, daemon=True)
            self._worker_thread.start()

            self._set_state("idle", "Ready")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize meeting manager: {e}", exc_info=True)
            self._set_state("error", f"Initialization failed: {e}")
            if self.on_error:
                self.on_error(str(e))
            return False

    def shutdown(self):
        """Cleanly stops capture, worker, and temporary files"""
        logger.info("Shutting down MeetingManager...")
        self.audio_engine.stop_capture(flush=False)
        self._stop_worker_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        self._set_state("idle", "Stopped")

    def _set_state(self, state: str, detail: str = ""):
        self.current_state = state
        self.state_detail = detail
        if self.on_state_changed:
            try:
                self.on_state_changed(state, detail)
            except Exception as e:
                logger.error(f"Error in on_state_changed callback: {e}")

    # ==========================================
    # DICTATION MODE
    # ==========================================

    def start_dictation(self, source: str = "mic"):
        """Start general-purpose dictation recording"""
        if self.current_state not in ("idle", "error"):
            logger.warning(f"Cannot start dictation in state: {self.current_state}")
            return

        self.active_mode = "dictation"
        self._set_state("recording", "Recording dictation...")
        self.audio_engine.start_dictation(source=source)

    def stop_dictation(self):
        """Stop dictation recording manually"""
        if self.active_mode == "dictation":
            self.audio_engine.stop_capture(flush=False)

    def _handle_dictation_complete(self, audio_data: np.ndarray):
        """Handles completed single-utterance dictation"""
        if len(audio_data) == 0:
            logger.info("Dictation empty or silent.")
            self._set_state("idle", "Ready")
            return

        self._set_state("processing", "Transcribing dictation...")
        threading.Thread(target=self._process_dictation_transcription, args=(audio_data,), daemon=True).start()

    def _process_dictation_transcription(self, audio_data: np.ndarray):
        try:
            text = self._transcribe_audio_array(audio_data)
            cleaned_text = self._clean_and_deduplicate_text(text)
            logger.info(f"Dictation result: '{cleaned_text}'")
            if cleaned_text:
                if self.on_dictation_ready:
                    self.on_dictation_ready(cleaned_text)
                # Broadcast to web stream
                threading.Thread(
                    target=self.api_client.publish_live_segment,
                    args=(cleaned_text,),
                    kwargs={"mode": "dictation", "timestamp": datetime.now().strftime("%H:%M:%S")},
                    daemon=True
                ).start()
        except Exception as e:
            logger.error(f"Dictation transcription error: {e}")
            if self.on_error:
                self.on_error(f"Dictation failed: {e}")
        finally:
            self._set_state("idle", "Ready")

    # ==========================================
    # LIVE MEETING MODE
    # ==========================================

    def start_live_meeting(self, title: Optional[str] = None, source: str = "both"):
        """
        Starts continuous live meeting capture.
        Initializes fresh cumulative transcript unless resumed.
        """
        with self._transcript_lock:
            self.segments.clear()
            self._cumulative_text = ""
            self._segment_counter = 0
            self._processed_audio_hashes.clear()
            self.meeting_start_time = datetime.now()
            self.meeting_title = title or f"Live Meeting - {self.meeting_start_time.strftime('%Y-%m-%d %H:%M')}"
            self.last_analysis_result = None

        self.active_mode = "meeting"
        self._set_state("listening", "Listening to meeting...")
        logger.info(f"Live Meeting Mode started: '{self.meeting_title}' (source={source})")
        self.audio_engine.start_meeting(source=source)

    def pause_live_meeting(self):
        """Pauses live meeting capture without finalizing or submitting"""
        if self.active_mode == "meeting" and self.audio_engine.is_capturing:
            logger.info("Pausing live meeting capture...")
            self.audio_engine.stop_capture(flush=True)
            self._set_state("idle", "Meeting Paused")

    def resume_live_meeting(self, source: str = "both"):
        """Resumes an existing live meeting session"""
        if self.active_mode == "meeting" and not self.audio_engine.is_capturing:
            logger.info("Resuming live meeting capture...")
            self._set_state("listening", "Listening to meeting...")
            self.audio_engine.start_meeting(source=source)

    def finish_meeting_and_submit(
        self,
        custom_title: Optional[str] = None,
        auto_submit: bool = True
    ) -> bool:
        """
        Executes the full end-of-meeting flow:
        1. Stops audio capture safely.
        2. Flushes any remaining unsegmented audio buffer so the final spoken words are preserved.
        3. Waits for pending transcription queue jobs to finish.
        4. Validates final cumulative transcript.
        5. Submits once to POST /api/workflows/run-sync.
        6. Receives & dispatches analysis and action items.
        """
        logger.info("Finishing meeting...")
        self._set_state("finalizing", "Flushing final audio...")

        # Stop capture and flush final buffered speech segment
        self.audio_engine.stop_capture(flush=True)

        def finish_worker():
            try:
                # Wait for transcription worker to drain queue (timeout 15s)
                drain_start = time.time()
                while not self._transcription_queue.empty() and (time.time() - drain_start < 15.0):
                    time.sleep(0.1)

                with self._transcript_lock:
                    final_text = self._cumulative_text.strip()
                    meeting_title = custom_title or self.meeting_title or f"Live Meeting - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

                if not final_text:
                    err = "Meeting transcript is empty. No speech was transcribed."
                    logger.warning(err)
                    self._set_state("error", err)
                    if self.on_error:
                        self.on_error(err)
                    return

                if not auto_submit:
                    self._set_state("completed", "Transcript ready for review")
                    return

                # Submit to backend LangGraph workflow
                self._set_state("analyzing", "Generating AI meeting analysis with Groq...")
                result = self.api_client.submit_meeting_workflow_sync(
                    transcript_text=final_text,
                    title=meeting_title,
                    force_reanalyze=False
                )
                self.last_analysis_result = result

                if result.success and result.status == "completed":
                    self._set_state("completed", "AI Analysis Completed")
                    if self.on_analysis_complete:
                        self.on_analysis_complete(result)
                else:
                    err = result.error_message or "Backend analysis failed"
                    self._set_state("error", f"Analysis failed: {err}")
                    if self.on_error:
                        self.on_error(err)

            except Exception as e:
                logger.error(f"Error in finish_worker: {e}", exc_info=True)
                self._set_state("error", f"Finish error: {e}")
                if self.on_error:
                    self.on_error(str(e))

        threading.Thread(target=finish_worker, daemon=True).start()
        return True

    def get_cumulative_transcript(self) -> str:
        """Returns the authoritative cumulative meeting transcript"""
        with self._transcript_lock:
            return self._cumulative_text

    def set_cumulative_transcript(self, text: str):
        """Allows manual user edits to the cumulative transcript"""
        with self._transcript_lock:
            self._cumulative_text = text.strip()

    # ==========================================
    # INTERNAL TRANSCRIPTION PIPELINE
    # ==========================================

    def _handle_incoming_speech_segment(self, audio_data: np.ndarray, vol: float):
        """Callback from AudioCaptureEngine when a completed speech segment is sliced"""
        if len(audio_data) == 0:
            return

        # Deduplicate identical audio blocks by quick hash
        audio_hash = hash(audio_data.tobytes()[:2048])
        if audio_hash in self._processed_audio_hashes:
            logger.debug("Duplicate audio segment detected - skipping")
            return
        self._processed_audio_hashes.add(audio_hash)

        timestamp_str = datetime.now().strftime("%H:%M:%S")
        duration = len(audio_data) / self.config.AUDIO_RATE

        logger.info(f"Queuing speech segment for transcription ({duration:.1f}s, vol={vol:.4f})...")
        self._transcription_queue.put({
            "audio": audio_data,
            "timestamp": timestamp_str,
            "duration": duration
        })

    def _transcription_worker_loop(self):
        """Dedicated background thread transcribing completed speech segments"""
        logger.info("Background transcription worker started.")
        while not self._stop_worker_event.is_set():
            try:
                task = self._transcription_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            audio_data = task["audio"]
            timestamp_str = task["timestamp"]
            duration = task["duration"]

            try:
                if self.active_mode == "meeting" and self.current_state == "listening":
                    self._set_state("transcribing", "Transcribing speech segment...")

                raw_text = self._transcribe_audio_array(audio_data)
                cleaned_text = self._clean_and_deduplicate_text(raw_text)

                if cleaned_text and len(cleaned_text.split()) >= 1:
                    self._append_segment(timestamp_str, cleaned_text, duration)
                else:
                    logger.debug(f"Segment produced no usable text: '{raw_text}'")

            except Exception as e:
                logger.error(f"Error transcribing speech segment: {e}", exc_info=True)
            finally:
                self._transcription_queue.task_done()
                if self.active_mode == "meeting" and self.audio_engine.is_capturing:
                    self._set_state("listening", "Listening to meeting...")

    def _append_segment(self, timestamp: str, text: str, duration: float):
        """Appends a new transcribed segment to cumulative transcript in chronological order"""
        with self._transcript_lock:
            self._segment_counter += 1
            segment = MeetingTranscriptSegment(
                segment_id=self._segment_counter,
                timestamp=timestamp,
                text=text,
                duration_sec=duration
            )
            self.segments.append(segment)

            # Preserve punctuation and readable spacing
            if not self._cumulative_text:
                self._cumulative_text = text
            else:
                last_char = self._cumulative_text.rstrip()[-1] if self._cumulative_text.rstrip() else ""
                if last_char in ".?!":
                    self._cumulative_text += f" {text}"
                elif last_char in ",;:":
                    self._cumulative_text += f" {text}"
                else:
                    self._cumulative_text += f". {text}"

            full_text = self._cumulative_text
            seg_dict = segment.to_dict()

        logger.info(f"Appended Segment #{segment.segment_id} [{timestamp}]: {text}")

        # Broadcast live segment to web stream
        threading.Thread(
            target=self.api_client.publish_live_segment,
            args=(text,),
            kwargs={
                "timestamp": timestamp,
                "mode": "meeting",
                "segment_id": segment.segment_id,
            },
            daemon=True
        ).start()

        if self.on_segment_added:
            try:
                self.on_segment_added(seg_dict, full_text)
            except Exception as e:
                logger.error(f"Error in on_segment_added callback: {e}")

    def _transcribe_audio_array(self, audio_data: np.ndarray) -> str:
        """Transcribes int16 numpy array using faster-whisper or fallback"""
        if not HAVE_WHISPER or self.whisper_model is None:
            # Fallback mock for testing or environments without whisper
            return "This is a recorded live meeting speech segment."

        # Convert int16 or float audio directly to 1D float32 normalized array (-1.0 to 1.0)
        if audio_data.dtype == np.int16:
            audio_float32 = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype != np.float32:
            audio_float32 = audio_data.astype(np.float32)
        else:
            audio_float32 = audio_data

        if audio_float32.ndim > 1:
            audio_float32 = audio_float32.flatten()

        with self._whisper_lock:
            segments, info = self.whisper_model.transcribe(
                audio_float32,
                language=self.config.WHISPER_LANGUAGE,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                vad_filter=True,
                word_timestamps=False
            )
            text = " ".join(seg.text.strip() for seg in segments if seg.text).strip()
            return text

    def _clean_and_deduplicate_text(self, text: str) -> str:
        """Strips Whisper repetitive hallucination loops and trims spacing"""
        if not text:
            return ""

        # Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # Split into sentences or phrases and eliminate direct consecutive repeats
        phrases = re.split(r'(?<=[.?!])\s+', text)
        cleaned = []
        last_phrase = ""

        for p in phrases:
            p_strip = p.strip()
            if p_strip:
                p_strip = p_strip[0].upper() + p_strip[1:]
            p_lower = p_strip.lower()
            if p_lower and p_lower != last_phrase:
                cleaned.append(p_strip)
                last_phrase = p_lower

        result = " ".join(cleaned).strip()
        return result

    def _save_temp_wav(self, audio_data: np.ndarray) -> str:
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(temp.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.config.AUDIO_RATE)
            wf.writeframes(audio_data.tobytes())
        return temp.name

    def _cleanup_temp_file(self, path: str):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def _handle_audio_level(self, level: float):
        if self.on_audio_level:
            try:
                self.on_audio_level(level)
            except Exception:
                pass

    def _handle_engine_error(self, err: str):
        logger.error(f"Audio engine reported error: {err}")
        self._set_state("error", f"Audio Error: {err}")
        if self.on_error:
            self.on_error(err)
