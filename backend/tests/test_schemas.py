"""Tests for Pydantic schemas and serialization."""

from datetime import datetime, timezone
import pytest
from app.schemas.transcription import (
    ApiStatus,
    DatabaseStatus,
    HealthResponse,
    TranscriptionCreateResponse,
    TranscriptionListResponse,
    TranscriptionResponse,
    TranscriptionStatus,
    TranscriptionUpdateRequest,
    WhisperModelStatus,
)


def test_transcription_status_enum_values():
    """Verify all expected transcription status values exist."""
    assert TranscriptionStatus.QUEUED.value == "queued"
    assert TranscriptionStatus.PROCESSING.value == "processing"
    assert TranscriptionStatus.COMPLETED.value == "completed"
    assert TranscriptionStatus.FAILED.value == "failed"


def test_health_response_schema():
    """Verify HealthResponse model serialization."""
    now = datetime.now(timezone.utc)
    health = HealthResponse(
        status=ApiStatus.HEALTHY,
        api_status="running",
        database_status=DatabaseStatus.CONNECTED,
        whisper_status=WhisperModelStatus.LOADED,
        whisper_model="small",
        version="0.1.0",
        timestamp=now,
    )
    data = health.model_dump()
    assert data["status"] == "healthy"
    assert data["database_status"] == "connected"
    assert data["whisper_status"] == "loaded"
    assert data["whisper_model"] == "small"
    assert data["version"] == "0.1.0"


def test_transcription_create_response_schema():
    """Verify TranscriptionCreateResponse matches Prompt 2 job_id structure."""
    resp = TranscriptionCreateResponse(
        job_id="651a2b3c4d5e6f7a8b9c0d1e",
        status=TranscriptionStatus.QUEUED,
        message="Audio accepted for transcription",
    )
    data = resp.model_dump()
    assert data["job_id"] == "651a2b3c4d5e6f7a8b9c0d1e"
    assert data["status"] == "queued"
    assert data["message"] == "Audio accepted for transcription"


def test_transcription_response_schema():
    """Verify TranscriptionResponse serialization with full fields."""
    now = datetime.now(timezone.utc)
    record = TranscriptionResponse(
        id="651a2b3c4d5e6f7a8b9c0d1e",
        original_filename="meeting.mp3",
        file_format="mp3",
        file_size_bytes=2048500,
        status=TranscriptionStatus.COMPLETED,
        audio_duration=180.5,
        requested_language="en",
        detected_language="en",
        whisper_model="small",
        transcript_text="This is a test transcript.",
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    dumped = record.model_dump()
    assert dumped["id"] == "651a2b3c4d5e6f7a8b9c0d1e"
    assert dumped["status"] == "completed"
    assert dumped["audio_duration"] == 180.5
    assert dumped["transcript_text"] == "This is a test transcript."


def test_transcription_list_response():
    """Verify TranscriptionListResponse pagination calculations."""
    now = datetime.now(timezone.utc)
    item = TranscriptionResponse(
        id="651a2b3c4d5e6f7a8b9c0d1e",
        original_filename="meeting.mp3",
        file_format="mp3",
        file_size_bytes=1000,
        status=TranscriptionStatus.QUEUED,
        whisper_model="small",
        created_at=now,
        updated_at=now,
    )
    list_resp = TranscriptionListResponse(
        items=[item],
        total=1,
        page=1,
        page_size=20,
        total_pages=1,
    )
    assert len(list_resp.items) == 1
    assert list_resp.total == 1
    assert list_resp.page == 1


def test_transcription_update_request():
    """Verify TranscriptionUpdateRequest payload validation."""
    update = TranscriptionUpdateRequest(transcript_text="Corrected text")
    assert update.transcript_text == "Corrected text"
