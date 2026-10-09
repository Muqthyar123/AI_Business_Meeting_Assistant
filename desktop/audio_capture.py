import threading
import time
import logging
import numpy as np
from typing import Callable, Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Try importing sound libraries
HAVE_SOUNDDEVICE = False
HAVE_SOUNDCARD = False

try:
    import sounddevice as sd
    HAVE_SOUNDDEVICE = True
except Exception as e:
    logger.warning(f"sounddevice import error: {e}")

import warnings

try:
    import soundcard as sc
    HAVE_SOUNDCARD = True
    if hasattr(sc, 'SoundcardRuntimeWarning'):
        warnings.filterwarnings("ignore", category=sc.SoundcardRuntimeWarning)
except Exception as e:
    logger.warning(f"soundcard import error: {e}")


class AudioCaptureEngine:
    """
    High-reliability audio capture engine supporting:
    - Microphone capture (sounddevice / soundcard)
    - Windows System Audio (WASAPI loopback via soundcard)
    - Mixed (Microphone + System Audio) for capturing all meeting participants
    - Live voice activity detection (VAD), pause-based speech segmentation, and flushing.
    """

    def __init__(
        self,
        rate: int = 16000,
        channels: int = 1,
        block_size: int = 512,
        dictation_silence_threshold: float = 0.003,
        dictation_pause_sec: float = 1.4,
        meeting_silence_threshold: float = 0.002,
        meeting_pause_sec: float = 2.0,
        meeting_min_segment_sec: float = 0.4,
        meeting_max_buffer_sec: float = 25.0,
        on_speech_segment: Optional[Callable[[np.ndarray, float], None]] = None,
        on_dictation_complete: Optional[Callable[[np.ndarray], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.rate = rate
        self.channels = channels
        self.block_size = block_size
        
        self.dictation_silence_threshold = dictation_silence_threshold
        self.dictation_pause_sec = dictation_pause_sec
        self.meeting_silence_threshold = meeting_silence_threshold
        self.meeting_pause_sec = meeting_pause_sec
        self.meeting_min_segment_sec = meeting_min_segment_sec
        self.meeting_max_buffer_sec = meeting_max_buffer_sec
        
        # Callbacks
        self.on_speech_segment = on_speech_segment
        self.on_dictation_complete = on_dictation_complete
        self.on_audio_level = on_audio_level
        self.on_error = on_error
        
        # State
        self.is_capturing = False
        self.capture_mode = "dictation"  # "dictation" or "meeting"
        self.audio_source = "mic"        # "mic", "system", "both"
        
        self._lock = threading.Lock()
        self._capture_thread: Optional[threading.Thread] = None
        self._system_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Speech segment buffering
        self._speech_buffer: List[float] = []
        self._speech_detected = False
        self._silence_frames = 0
        self._segment_start_time = 0.0

    @property
    def silence_threshold(self) -> float:
        if self.capture_mode == "meeting":
            return self.meeting_silence_threshold
        return self.dictation_silence_threshold

    @property
    def pause_sec(self) -> float:
        if self.capture_mode == "meeting":
            return self.meeting_pause_sec
        return self.dictation_pause_sec

    def set_pause_threshold(self, seconds: float):
        """Update the meeting pause duration threshold in seconds"""
        with self._lock:
            self.meeting_pause_sec = max(0.5, float(seconds))

    def set_silence_threshold(self, threshold: float):
        """Update the silence amplitude threshold"""
        with self._lock:
            self.meeting_silence_threshold = max(0.0001, float(threshold))

    def start_dictation(self, source: str = "mic"):
        """Start capturing a single utterance for general dictation mode"""
        with self._lock:
            if self.is_capturing:
                return
            self.capture_mode = "dictation"
            self.audio_source = source
            self.is_capturing = True
            self._stop_event.clear()
            self._reset_buffers()
            
        self._capture_thread = threading.Thread(target=self._run_capture_loop, daemon=True)
        self._capture_thread.start()

    def start_meeting(self, source: str = "both"):
        """Start continuous live meeting audio capture"""
        with self._lock:
            if self.is_capturing:
                return
            self.capture_mode = "meeting"
            self.audio_source = source
            self.is_capturing = True
            self._stop_event.clear()
            self._reset_buffers()
            
        self._capture_thread = threading.Thread(target=self._run_capture_loop, daemon=True)
        self._capture_thread.start()

    def stop_capture(self, flush: bool = True) -> Optional[np.ndarray]:
        """
        Stop audio capture cleanly.
        If flush=True in meeting mode, any remaining buffered speech is emitted.
        """
        with self._lock:
            if not self.is_capturing:
                return None
            self.is_capturing = False
            self._stop_event.set()

        # Wait for capture thread
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=1.5)

        if flush and self.capture_mode == "meeting":
            self.flush_pending_segment()
            
        return None

    def _reset_buffers(self):
        self._speech_buffer = []
        self._speech_detected = False
        self._silence_frames = 0
        self._segment_start_time = time.time()

    def flush_pending_segment(self):
        """Flush any buffered audio that has sufficient speech energy"""
        with self._lock:
            if not self._speech_buffer:
                return
            
            min_samples = int(self.rate * self.meeting_min_segment_sec)
            if len(self._speech_buffer) >= min_samples:
                arr = np.array(self._speech_buffer, dtype=np.float32)
                vol = float(np.mean(np.abs(arr)))
                if vol >= (self.meeting_silence_threshold * 0.5):
                    int16_data = (np.clip(arr, -1.0, 1.0) * 32767).astype(np.int16)
                    logger.info(f"Flushed final speech segment: {len(int16_data)} samples, vol={vol:.4f}")
                    if self.on_speech_segment:
                        try:
                            self.on_speech_segment(int16_data, vol)
                        except Exception as e:
                            logger.error(f"Error in on_speech_segment callback during flush: {e}")
            self._reset_buffers()

    def _process_audio_chunk(self, samples: np.ndarray):
        """Processes an incoming float32 mono block from any audio source"""
        if not self.is_capturing:
            return

        vol = float(np.mean(np.abs(samples)))
        if self.on_audio_level:
            try:
                self.on_audio_level(vol)
            except Exception:
                pass

        if self.capture_mode == "dictation":
            self._process_dictation_chunk(samples, vol)
        else:
            self._process_meeting_chunk(samples, vol)

    def _process_dictation_chunk(self, samples: np.ndarray, vol: float):
        """Handles single utterance capture with auto-stop on silence"""
        self._speech_buffer.extend(samples)
        silence_threshold_frames = int(self.rate / len(samples) * self.dictation_pause_sec)

        if vol > self.dictation_silence_threshold:
            self._speech_detected = True
            self._silence_frames = 0
        elif self._speech_detected:
            self._silence_frames += 1
            if self._silence_frames >= silence_threshold_frames:
                logger.info("Dictation silence detected - auto-stopping...")
                self.is_capturing = False
                self._stop_event.set()

    def _process_meeting_chunk(self, samples: np.ndarray, vol: float):
        """
        Handles continuous meeting segmentation:
        1. Accumulates speech frames when volume > threshold.
        2. Slices out completed speech segment when pause >= pause_sec.
        3. Forces chunk slice if continuous speech exceeds max_buffer_sec.
        """
        silence_threshold_frames = int(self.rate / len(samples) * self.meeting_pause_sec)
        max_buffer_samples = int(self.rate * self.meeting_max_buffer_sec)
        min_segment_samples = int(self.rate * self.meeting_min_segment_sec)

        if vol > self.meeting_silence_threshold:
            if not self._speech_detected:
                self._speech_detected = True
                self._segment_start_time = time.time()
            self._speech_buffer.extend(samples)
            self._silence_frames = 0

            # Check if buffer grew too large during continuous non-stop speech
            if len(self._speech_buffer) >= max_buffer_samples:
                logger.info("Max speech segment length reached - forcing segment split...")
                self._emit_current_segment()

        elif self._speech_detected:
            self._speech_buffer.extend(samples)
            self._silence_frames += 1

            if self._silence_frames >= silence_threshold_frames:
                logger.info(f"Meeting pause detected ({self.meeting_pause_sec}s) - emitting segment...")
                self._emit_current_segment()

    def _emit_current_segment(self):
        """Converts accumulated speech buffer into int16 and calls on_speech_segment"""
        min_samples = int(self.rate * self.meeting_min_segment_sec)
        if len(self._speech_buffer) >= min_samples:
            arr = np.array(self._speech_buffer, dtype=np.float32)
            vol = float(np.mean(np.abs(arr)))
            int16_data = (np.clip(arr, -1.0, 1.0) * 32767).astype(np.int16)
            
            if self.on_speech_segment:
                try:
                    self.on_speech_segment(int16_data, vol)
                except Exception as e:
                    logger.error(f"Error in on_speech_segment callback: {e}")
        self._reset_buffers()

    def _run_capture_loop(self):
        """Main capture worker thread routing to appropriate capture implementation"""
        source = self.audio_source
        logger.info(f"Starting audio capture thread (mode={self.capture_mode}, source={source})...")

        com_initialized = False
        try:
            import ctypes
            ctypes.windll.ole32.CoInitialize(None)
            com_initialized = True
        except Exception:
            pass

        try:
            if source == "both" and HAVE_SOUNDCARD:
                self._run_soundcard_mixed_capture()
            elif source == "system" and HAVE_SOUNDCARD:
                self._run_soundcard_system_capture()
            elif HAVE_SOUNDDEVICE:
                self._run_sounddevice_mic_capture()
            elif HAVE_SOUNDCARD:
                self._run_soundcard_mic_capture()
            else:
                err = "No supported audio capture library available (sounddevice or soundcard required)"
                logger.error(err)
                if self.on_error:
                    self.on_error(err)
        except Exception as e:
            logger.error(f"Audio capture loop error: {e}", exc_info=True)
            if self.on_error:
                self.on_error(str(e))
        finally:
            if self.capture_mode == "dictation" and self._speech_buffer:
                arr = np.array(self._speech_buffer, dtype=np.float32)
                vol = float(np.mean(np.abs(arr)))
                if vol > 0.001 and len(arr) > self.rate * 0.2:
                    int16_data = (np.clip(arr, -1.0, 1.0) * 32767).astype(np.int16)
                    if self.on_dictation_complete:
                        self.on_dictation_complete(int16_data)
                elif self.on_dictation_complete:
                    self.on_dictation_complete(np.array([], dtype=np.int16))

            if com_initialized:
                try:
                    import ctypes
                    ctypes.windll.ole32.CoUninitialize()
                except Exception:
                    pass

    def _run_sounddevice_mic_capture(self):
        """Captures microphone using sounddevice InputStream callback"""
        def callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"sounddevice status: {status}")
            if not self.is_capturing:
                return
            samples = indata[:, 0].copy()
            self._process_audio_chunk(samples)

        with sd.InputStream(
            samplerate=self.rate,
            channels=self.channels,
            callback=callback,
            dtype='float32',
            blocksize=self.block_size
        ):
            while self.is_capturing and not self._stop_event.is_set():
                time.sleep(0.02)

    def _run_soundcard_mic_capture(self):
        """Captures microphone using soundcard"""
        mic = sc.default_microphone()
        with mic.recorder(samplerate=self.rate, channels=1, blocksize=self.block_size) as rec:
            while self.is_capturing and not self._stop_event.is_set():
                data = rec.record(numframes=self.block_size)
                samples = data[:, 0].astype(np.float32)
                self._process_audio_chunk(samples)

    def _run_soundcard_system_capture(self):
        """Captures Windows system audio (WASAPI Loopback) using soundcard"""
        spk = sc.default_speaker()
        loopback = sc.get_microphone(id=str(spk.name), include_loopback=True)
        if not loopback:
            raise RuntimeError("Windows WASAPI Loopback device not found")

        with loopback.recorder(samplerate=self.rate, channels=1, blocksize=self.block_size) as rec:
            while self.is_capturing and not self._stop_event.is_set():
                data = rec.record(numframes=self.block_size)
                samples = data[:, 0].astype(np.float32)
                self._process_audio_chunk(samples)

    def _run_soundcard_mixed_capture(self):
        """
        Captures both Microphone (local user) and System Audio Loopback (remote participants),
        mixing them cleanly without clipping.
        """
        spk = sc.default_speaker()
        try:
            loopback = sc.get_microphone(id=str(spk.name), include_loopback=True)
        except Exception:
            loopback = None

        mic = sc.default_microphone()

        if not loopback:
            logger.warning("WASAPI Loopback unavailable - falling back to microphone only")
            self._run_soundcard_mic_capture()
            return

        # Use two queues or dual record
        mic_rec = mic.recorder(samplerate=self.rate, channels=1, blocksize=self.block_size)
        loop_rec = loopback.recorder(samplerate=self.rate, channels=1, blocksize=self.block_size)

        with mic_rec, loop_rec:
            while self.is_capturing and not self._stop_event.is_set():
                m_data = mic_rec.record(numframes=self.block_size)[:, 0].astype(np.float32)
                l_data = loop_rec.record(numframes=self.block_size)[:, 0].astype(np.float32)

                # Smart mix: 0.6 * mic + 0.6 * loopback, soft-clipped
                mixed = np.clip(0.6 * m_data + 0.6 * l_data, -1.0, 1.0)
                self._process_audio_chunk(mixed)
