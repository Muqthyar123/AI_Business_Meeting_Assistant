"""Tests for Transcription API routes including audio upload and validation."""

from datetime import datetime, timezone
import io
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError
from app.config import Settings, get_settings
from app.main import app
from app.repositories.transcription_repo import get_transcription_repository
from app.services.whisper_service import get_whisper_service

client = TestClient(app)


@pytest.fixture
def mock_repo():
    """Create a mock repository instance and override FastAPI dependency."""
    mock = MagicMock()
    mock_whisper = MagicMock()
    mock_whisper.model_name = "small"
    mock_whisper.transcribe.return_value = {
        "text": "Meeting transcription result",
        "language": "en",
        "duration": 30.0,
        "segments": [],
    }
    app.dependency_overrides[get_transcription_repository] = lambda: mock
    app.dependency_overrides[get_whisper_service] = lambda: mock_whisper
    yield mock
    app.dependency_overrides.clear()


# --- Upload Endpoint Tests ---


def test_upload_audio_success(mock_repo):
    """Verify POST /api/transcriptions/upload accepts valid audio and returns 202."""
    now = datetime.now(timezone.utc)
    mock_repo.create_queued.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "original_filename": "meeting.mp3",
        "status": "queued",
        "created_at": now,
        "updated_at": now,
    }

    fake_audio_content = b"fake audio payload for test"
    files = {"file": ("meeting.mp3", io.BytesIO(fake_audio_content), "audio/mpeg")}
    data = {"language": "en"}

    response = client.post("/api/transcriptions/upload", files=files, data=data)
    assert response.status_code == 202
    resp_json = response.json()
    assert resp_json["job_id"] == "651a2b3c4d5e6f7a8b9c0d1e"
    assert resp_json["status"] == "queued"
    assert resp_json["message"] == "Audio accepted for transcription"


def test_upload_audio_unsupported_extension(mock_repo):
    """Verify upload rejects unsupported file extensions (e.g. .pdf, .txt, .exe)."""
    files = {"file": ("notes.pdf", io.BytesIO(b"dummy pdf content"), "application/pdf")}
    response = client.post("/api/transcriptions/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported audio format" in response.json()["detail"]


def test_upload_audio_empty_file(mock_repo):
    """Verify upload rejects empty (0 bytes) audio files."""
    files = {"file": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    response = client.post("/api/transcriptions/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_upload_audio_exceeds_size_limit(mock_repo):
    """Verify upload rejects files larger than MAX_UPLOAD_SIZE_MB."""
    # Temporarily set max upload size to 0.0001 MB (~100 bytes) for testing
    def custom_settings():
        return Settings(MAX_UPLOAD_SIZE_MB=0.0001)

    app.dependency_overrides[get_settings] = custom_settings
    try:
        large_content = b"x" * (1024 * 50)  # 50KB > 0.0001 MB
        files = {"file": ("large.mp3", io.BytesIO(large_content), "audio/mpeg")}
        response = client.post("/api/transcriptions/upload", files=files)
        assert response.status_code == 413
        assert "exceeds maximum allowed upload size" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_upload_audio_db_unavailable(mock_repo):
    """Verify upload returns 503 when database creation fails."""
    mock_repo.create_queued.side_effect = PyMongoError("Connection lost")
    files = {"file": ("meeting.mp3", io.BytesIO(b"valid audio data"), "audio/mpeg")}
    response = client.post("/api/transcriptions/upload", files=files)
    assert response.status_code == 503
    assert "Database service is unavailable" in response.json()["detail"]


# --- CRUD Endpoint Tests ---


def test_list_transcriptions_route(mock_repo):
    """Verify GET /api/transcriptions returns paginated response."""
    now = datetime.now(timezone.utc)
    mock_repo.list_records.return_value = (
        [
            {
                "id": "651a2b3c4d5e6f7a8b9c0d1e",
                "original_filename": "meeting.mp3",
                "file_format": "mp3",
                "file_size_bytes": 1024,
                "status": "completed",
                "whisper_model": "small",
                "transcript_text": "Meeting transcript content.",
                "created_at": now,
                "updated_at": now,
            }
        ],
        1,
    )

    response = client.get("/api/transcriptions?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == "651a2b3c4d5e6f7a8b9c0d1e"


def test_get_transcription_by_id_found(mock_repo):
    """Verify GET /api/transcriptions/{id} returns record when found."""
    now = datetime.now(timezone.utc)
    mock_repo.get_by_id.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "original_filename": "meeting.mp3",
        "file_format": "mp3",
        "file_size_bytes": 1024,
        "status": "completed",
        "whisper_model": "small",
        "transcript_text": "Meeting transcript.",
        "created_at": now,
        "updated_at": now,
    }

    response = client.get("/api/transcriptions/651a2b3c4d5e6f7a8b9c0d1e")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "651a2b3c4d5e6f7a8b9c0d1e"
    assert data["status"] == "completed"


def test_get_transcription_by_id_not_found(mock_repo):
    """Verify GET /api/transcriptions/{id} returns 404 when not found or ID invalid."""
    mock_repo.get_by_id.return_value = None
    response = client.get("/api/transcriptions/nonexistent_id")
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_update_transcription_text(mock_repo):
    """Verify PATCH /api/transcriptions/{id} updates transcript text."""
    now = datetime.now(timezone.utc)
    mock_repo.get_by_id.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "original_filename": "meeting.mp3",
        "file_format": "mp3",
        "file_size_bytes": 1024,
        "status": "completed",
        "whisper_model": "small",
        "transcript_text": "Original text.",
        "created_at": now,
        "updated_at": now,
    }
    mock_repo.update.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "original_filename": "meeting.mp3",
        "file_format": "mp3",
        "file_size_bytes": 1024,
        "status": "completed",
        "whisper_model": "small",
        "transcript_text": "Corrected text.",
        "created_at": now,
        "updated_at": now,
    }

    response = client.patch(
        "/api/transcriptions/651a2b3c4d5e6f7a8b9c0d1e",
        json={"transcript_text": "Corrected text."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["transcript_text"] == "Corrected text."


def test_delete_transcription(mock_repo):
    """Verify DELETE /api/transcriptions/{id} removes record."""
    mock_repo.delete.return_value = True
    response = client.delete("/api/transcriptions/651a2b3c4d5e6f7a8b9c0d1e")
    assert response.status_code == 204

    mock_repo.delete.return_value = False
    response = client.delete("/api/transcriptions/nonexistent_id")
    assert response.status_code == 404
