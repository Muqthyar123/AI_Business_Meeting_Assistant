import os
from dataclasses import dataclass, field

@dataclass
class DesktopConfig:
    # Audio capture configuration
    AUDIO_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    AUDIO_BLOCK_SIZE: int = 512
    
    # Dictation mode thresholds
    DICTATION_SILENCE_THRESHOLD: float = 0.003
    DICTATION_PAUSE_SEC: float = 1.4
    
    # Live Meeting mode thresholds (tuned for natural pauses)
    MEETING_SILENCE_THRESHOLD: float = 0.002
    MEETING_PAUSE_SEC: float = 2.0
    MEETING_MIN_SEGMENT_SEC: float = 0.4
    MEETING_MAX_BUFFER_SEC: float = 25.0
    
    # Audio Sources: "mic", "system", "both"
    DEFAULT_AUDIO_SOURCE: str = os.environ.get("AUDIO_SOURCE", "mic")
    
    # Whisper STT model configuration
    WHISPER_MODEL: str = os.environ.get("WHISPER_MODEL", "base")
    WHISPER_DEVICE: str = os.environ.get("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
    WHISPER_LANGUAGE: str = os.environ.get("WHISPER_LANGUAGE", "en")
    
    # Backend API configuration
    BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
    WORKFLOW_SYNC_PATH: str = "/api/workflows/run-sync"
    HEALTH_PATH: str = "/api/health"
    REQUEST_TIMEOUT_SEC: float = 120.0
    
    # Text to Speech configuration
    TTS_RATE: int = 180
    TTS_VOLUME: float = 0.9
    ENABLE_TTS: bool = True

    # Local transcript recovery directory
    RECOVERY_DIR: str = os.path.join(os.path.expanduser("~"), ".ai_meeting_assistant_transcripts")

    @property
    def workflow_sync_url(self) -> str:
        return f"{self.BACKEND_URL.rstrip('/')}{self.WORKFLOW_SYNC_PATH}"

    @property
    def health_url(self) -> str:
        return f"{self.BACKEND_URL.rstrip('/')}{self.HEALTH_PATH}"

CONFIG = DesktopConfig()
