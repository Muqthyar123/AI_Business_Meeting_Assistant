"""Shared Pydantic schemas for the Transcription API and Health checks."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TranscriptionStatus(str, Enum):
    """Transcription processing lifecycle statuses."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DatabaseStatus(str, Enum):
    """Database connectivity status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class ApiStatus(str, Enum):
    """API overall service status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class WhisperModelStatus(str, Enum):
    """Whisper engine status."""

    LOADED = "loaded"
    NOT_LOADED = "not_loaded"
    UNAVAILABLE = "unavailable"


# --- Health Schemas ---


class HealthResponse(BaseModel):
    """Structured health check response."""

    status: ApiStatus = Field(description="Overall API health state")
    api_status: str = Field(default="running", description="Status of the FastAPI server")
    database_status: DatabaseStatus = Field(description="Status of MongoDB connection")
    whisper_status: WhisperModelStatus = Field(description="Status of Whisper model loading")
    whisper_model: Optional[str] = Field(default=None, description="Configured Whisper model name")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "api_status": "running",
                "database_status": "connected",
                "whisper_status": "loaded",
                "whisper_model": "small",
                "version": "0.1.0",
                "timestamp": "2026-10-09T14:00:00Z",
            }
        }
    )


# --- Transcription Schemas ---


class TranscriptionCreateRequest(BaseModel):
    """Parameters submitted when requesting a new transcription."""

    requested_language: Optional[str] = Field(
        default=None,
        description="Optional ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'te') to guide transcription",
        max_length=10,
    )


class TranscriptionCreateResponse(BaseModel):
    """Response returned upon initial transcription job creation."""

    job_id: str = Field(description="Unique transcription record / job ID (hex string)")
    status: TranscriptionStatus = Field(
        default=TranscriptionStatus.QUEUED,
        description="Initial status of the transcription job",
    )
    message: str = Field(
        default="Audio accepted for transcription",
        description="Informational status message",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "job_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "status": "queued",
                "message": "Audio accepted for transcription",
            }
        },
    )


class TranscriptionUpdateRequest(BaseModel):
    """Payload for editing a transcription record (e.g., user edits to the text)."""

    transcript_text: Optional[str] = Field(
        default=None,
        description="Updated transcript text content",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transcript_text": "Updated transcript text after manual corrections.",
            }
        }
    )


class TranscriptionResponse(BaseModel):
    """Full transcription record details."""

    id: str = Field(description="Unique transcription record identifier")
    original_filename: str = Field(description="Original filename of the recorded audio")
    file_format: str = Field(description="Audio format/extension (e.g., mp3, wav, m4a)")
    file_size_bytes: int = Field(description="Audio file size in bytes")
    status: TranscriptionStatus = Field(description="Current processing status")
    audio_duration: Optional[float] = Field(
        default=None,
        description="Audio duration in seconds",
    )
    requested_language: Optional[str] = Field(
        default=None,
        description="Language code requested by user if any",
    )
    detected_language: Optional[str] = Field(
        default=None,
        description="Language detected by Whisper during transcription",
    )
    whisper_model: str = Field(
        description="Whisper model name used (e.g., small, base, medium)",
    )
    transcript_text: Optional[str] = Field(
        default=None,
        description="Full generated or edited transcript text",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if the transcription job failed",
    )
    created_at: datetime = Field(
        description="UTC creation timestamp",
    )
    updated_at: datetime = Field(
        description="UTC last update timestamp",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "651a2b3c4d5e6f7a8b9c0d1e",
                "original_filename": "team_sync.mp3",
                "file_format": "mp3",
                "file_size_bytes": 1048576,
                "status": "completed",
                "audio_duration": 124.5,
                "requested_language": "en",
                "detected_language": "en",
                "whisper_model": "small",
                "transcript_text": "Good morning everyone, let's start with our quarterly review...",
                "error_message": None,
                "created_at": "2026-10-09T14:00:00Z",
                "updated_at": "2026-10-09T14:02:15Z",
            }
        },
    )


class TranscriptionListResponse(BaseModel):
    """Paginated collection of transcription records."""

    items: List[TranscriptionResponse] = Field(
        default_factory=list,
        description="List of transcription records for the current page",
    )
    total: int = Field(description="Total count of matching transcription records")
    page: int = Field(default=1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    total_pages: int = Field(default=1, description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
            }
        }
    )
