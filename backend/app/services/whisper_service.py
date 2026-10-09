"""Local OpenAI Whisper transcription service wrapper and lifecycle management."""

import logging
import os
from typing import Any, Dict, Optional
from app.schemas.transcription import WhisperModelStatus

logger = logging.getLogger(__name__)


class WhisperTranscriptionError(Exception):
    """Exception raised when an audio file cannot be transcribed by Whisper."""
    pass


VALID_WHISPER_MODELS = {
    "tiny", "tiny.en", "base", "base.en", "small", "small.en",
    "medium", "medium.en", "large", "large-v1", "large-v2",
    "large-v3", "large-v3-turbo", "turbo",
}


def normalize_whisper_model_name(raw_name: Optional[str]) -> str:
    """Sanitize and normalize Whisper model name strings to standard identifiers.

    Handles prefixes ('whisper-base' -> 'base'), trailing text, and invalid strings.
    """
    if not raw_name:
        return "base"
    clean = str(raw_name).strip().lower()
    if clean.startswith("whisper-"):
        clean = clean[len("whisper-"):]

    if clean in VALID_WHISPER_MODELS:
        return clean

    # Check if a valid prefix exists (e.g. accidental string concatenation)
    for m in sorted(VALID_WHISPER_MODELS, key=len, reverse=True):
        if clean.startswith(m):
            logger.warning("Sanitizing Whisper model string '%s' -> '%s'", raw_name, m)
            return m

    logger.warning("Unrecognized Whisper model '%s', falling back to 'base'", raw_name)
    return "base"


class WhisperService:
    """Service handling local OpenAI Whisper model loading, status tracking, and transcription."""

    def __init__(self, model_name: str = "base", device: str = "cpu") -> None:
        """Initialize the Whisper service with configuration parameters.

        Args:
            model_name: Whisper model size name ('tiny', 'base', 'small', 'medium', 'large').
            device: Target execution device ('cpu' or 'cuda').
        """
        self.model_name = normalize_whisper_model_name(model_name)
        self.device = device
        self._model: Optional[Any] = None
        self._backend_type: Optional[str] = None
        self._status: WhisperModelStatus = WhisperModelStatus.NOT_LOADED
        self._load_error: Optional[str] = None

    @property
    def status(self) -> WhisperModelStatus:
        """Return the current model loading status."""
        return self._status

    @property
    def is_loaded(self) -> bool:
        """Check if the Whisper model is currently loaded in memory."""
        return self._status == WhisperModelStatus.LOADED and self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        """Return error message if model loading failed."""
        return self._load_error

    def load_model(self) -> bool:
        """Load the Whisper model (preferring faster-whisper with openai-whisper fallback) into memory.

        Returns:
            True if model loaded successfully, False otherwise.
        """
        if self.is_loaded:
            logger.info("Whisper model '%s' is already loaded.", self.model_name)
            return True

        logger.info(
            "Loading Whisper model '%s' on device '%s'...",
            self.model_name,
            self.device,
        )

        # 1. Try faster-whisper first (embedded PyAV decoding, 4x faster, no ffmpeg binary requirement)
        try:
            from faster_whisper import WhisperModel  # type: ignore

            compute_type = "int8" if self.device == "cpu" else "float16"
            self._model = WhisperModel(self.model_name, device=self.device, compute_type=compute_type)
            self._backend_type = "faster_whisper"
            self._status = WhisperModelStatus.LOADED
            self._load_error = None
            logger.info("faster-whisper model '%s' successfully loaded into memory.", self.model_name)
            return True
        except Exception as fw_err:
            logger.warning("faster-whisper load attempted but failed: %s. Trying openai-whisper...", str(fw_err))

        # 2. Fallback to standard openai-whisper
        try:
            import whisper  # type: ignore

            self._model = whisper.load_model(self.model_name, device=self.device)
            self._backend_type = "whisper"
            self._status = WhisperModelStatus.LOADED
            self._load_error = None
            logger.info("openai-whisper model '%s' successfully loaded into memory.", self.model_name)
            return True
        except ImportError as e:
            self._status = WhisperModelStatus.UNAVAILABLE
            self._load_error = "Neither faster-whisper nor openai-whisper package is available."
            logger.error("Whisper import failed: %s", str(e))
            return False
        except Exception as e:
            self._status = WhisperModelStatus.UNAVAILABLE
            self._load_error = f"Failed to load Whisper model '{self.model_name}': {str(e)}"
            logger.error("Whisper model load failed: %s", str(e))
            return False

    def unload_model(self) -> None:
        """Unload the Whisper model and release memory."""
        self._model = None
        self._backend_type = None
        self._status = WhisperModelStatus.NOT_LOADED
        self._load_error = None
        logger.info("Whisper model unloaded.")

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        fp16: bool = False,
    ) -> Dict[str, Any]:
        """Transcribe an audio file using the loaded Whisper model.

        Args:
            audio_path: Path to the recorded audio file on disk.
            language: Optional ISO 639-1 language code (e.g., 'en', 'es', 'te').
            fp16: Use half-precision float (enforced to False on CPU).

        Returns:
            Dictionary containing:
                - text: Complete transcribed text
                - language: Detected or requested language code
                - duration: Approximate audio duration in seconds
                - segments: List of transcript segments with timestamps

        Raises:
            FileNotFoundError: If audio file does not exist on disk.
            RuntimeError: If Whisper model cannot be loaded.
            WhisperTranscriptionError: If Whisper inference or audio decoding fails.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file '{audio_path}' does not exist.")

        if not self.is_loaded:
            loaded = self.load_model()
            if not loaded or self._model is None:
                raise RuntimeError(
                    f"Whisper model '{self.model_name}' could not be loaded: {self.load_error}"
                )

        # Enforce CPU-compatible inference with fp16=False when running on CPU
        effective_fp16 = fp16 if self.device != "cpu" else False

        try:
            logger.info(
                "Starting Whisper transcription for '%s' (language=%s, fp16=%s)...",
                audio_path,
                language or "auto-detect",
                effective_fp16,
            )

            # Check if this is a faster-whisper model or standard whisper/mock
            is_faster_whisper = (
                self._backend_type == "faster_whisper"
                or (hasattr(self._model, "__class__") and "WhisperModel" in self._model.__class__.__name__)
            )

            if is_faster_whisper and not isinstance(self._model, (dict, list)):
                transcribe_kwargs: Dict[str, Any] = {}
                if language:
                    transcribe_kwargs["language"] = language

                raw_res = self._model.transcribe(audio_path, **transcribe_kwargs)
                if isinstance(raw_res, tuple) and len(raw_res) == 2:
                    segments_gen, info = raw_res
                    segments_list = []
                    for seg in segments_gen:
                        segments_list.append({
                            "id": getattr(seg, "id", len(segments_list)),
                            "start": getattr(seg, "start", 0.0),
                            "end": getattr(seg, "end", 0.0),
                            "text": getattr(seg, "text", "").strip(),
                        })
                    transcript_text = " ".join(s["text"] for s in segments_list if s["text"]).strip()
                    detected_language = getattr(info, "language", language or "en")
                    duration = getattr(info, "duration", None)
                    logger.info(
                        "faster-whisper transcription completed successfully. Detected language: %s, duration: %s",
                        detected_language,
                        duration,
                    )
                    return {
                        "text": transcript_text,
                        "language": detected_language,
                        "duration": duration,
                        "segments": segments_list,
                    }
                elif isinstance(raw_res, dict):
                    # Mocked object returning dictionary
                    result = raw_res
                else:
                    result = dict(raw_res)
            else:
                transcribe_kwargs = {
                    "fp16": effective_fp16,
                }
                if language:
                    transcribe_kwargs["language"] = language

                result = self._model.transcribe(audio_path, **transcribe_kwargs)

            transcript_text = result.get("text", "").strip()
            detected_language = result.get("language")
            segments = result.get("segments", [])

            # Extract audio duration from the end of the last segment if available
            duration: Optional[float] = None
            if segments and isinstance(segments, list) and len(segments) > 0:
                last_segment = segments[-1]
                if isinstance(last_segment, dict) and "end" in last_segment:
                    try:
                        duration = float(last_segment["end"])
                    except (ValueError, TypeError):
                        duration = None

            logger.info(
                "Transcription completed successfully. Detected language: %s, duration: %s",
                detected_language,
                duration,
            )
            return {
                "text": transcript_text,
                "language": detected_language,
                "duration": duration,
                "segments": segments,
            }
        except Exception as e:
            logger.error("Whisper inference failed on audio file '%s': %s", audio_path, str(e))
            raise WhisperTranscriptionError(
                f"Audio transcription failed: {str(e)}"
            ) from e


# Global singleton instance holder for WhisperService
_whisper_service_instance: Optional[WhisperService] = None


def get_whisper_service(model_name: Optional[str] = None) -> WhisperService:
    """Retrieve or initialize the global WhisperService singleton.

    Args:
        model_name: Optional model name to override default configuration.

    Returns:
        WhisperService singleton instance.
    """
    global _whisper_service_instance
    if _whisper_service_instance is None:
        from app.config import get_settings

        settings = get_settings()
        target_model = model_name or settings.WHISPER_MODEL
        _whisper_service_instance = WhisperService(model_name=target_model)
    elif model_name and normalize_whisper_model_name(model_name) != _whisper_service_instance.model_name:
        _whisper_service_instance = WhisperService(model_name=model_name)
    return _whisper_service_instance
