"""Tests for Meeting Analysis API routes."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError
from app.main import app
from app.repositories.analysis_repo import get_analysis_repository
from app.repositories.document_repo import get_document_repository
from app.repositories.transcription_repo import get_transcription_repository
from app.schemas.analysis import MeetingAnalysisResult
from app.services.llm_service import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMOutputParsingError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.meeting_analysis_service import get_meeting_analysis_service

client = TestClient(app)


@pytest.fixture
def mock_analysis_repo():
    mock = MagicMock()
    app.dependency_overrides[get_analysis_repository] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_analysis_repository, None)


@pytest.fixture
def mock_transcription_repo():
    mock = MagicMock()
    app.dependency_overrides[get_transcription_repository] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_transcription_repository, None)


@pytest.fixture
def mock_document_repo():
    mock = MagicMock()
    app.dependency_overrides[get_document_repository] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_document_repository, None)


@pytest.fixture
def mock_analysis_service():
    mock = MagicMock()
    mock.provider.provider_name = "groq"
    mock.provider.model_name = "llama-3.3-70b-versatile"
    mock.analyze_meeting.return_value = MeetingAnalysisResult(
        executive_summary="Team aligned on cloud architecture goals and timeline.",
        meeting_purpose="Review infrastructure plan.",
        key_discussion_points=["Database read performance", "Cost modeling"],
        decisions_made=["Approved MongoDB Atlas deployment"],
        risks_and_blockers=["Potential staging migration delay"],
        unresolved_questions=["Third-party monitoring tool budget"],
        topics_and_themes=["Infrastructure", "Budget"],
    )
    app.dependency_overrides[get_meeting_analysis_service] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_meeting_analysis_service, None)


# --- Create Analysis Route Tests ---


def test_create_analysis_from_transcription_success(
    mock_analysis_repo, mock_transcription_repo, mock_analysis_service
):
    """Verify POST /api/analysis/ successfully analyzes a completed transcription."""
    now = datetime.now(timezone.utc)
    mock_transcription_repo.get_by_id.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "original_filename": "q3_planning.mp3",
        "status": "completed",
        "transcript_text": "Good morning team, let's discuss our infrastructure migration to MongoDB Atlas.",
    }
    mock_analysis_repo.create.return_value = {
        "id": "751a2b3c4d5e6f7a8b9c0d1e",
        "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "transcription",
        "title": "q3_planning.mp3",
        "executive_summary": "Team aligned on cloud architecture goals and timeline.",
        "meeting_purpose": "Review infrastructure plan.",
        "key_discussion_points": ["Database read performance", "Cost modeling"],
        "decisions_made": ["Approved MongoDB Atlas deployment"],
        "risks_and_blockers": ["Potential staging migration delay"],
        "unresolved_questions": ["Third-party monitoring tool budget"],
        "topics_and_themes": ["Infrastructure", "Budget"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    payload = {
        "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "transcription",
    }
    response = client.post("/api/analysis/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "751a2b3c4d5e6f7a8b9c0d1e"
    assert data["source_type"] == "transcription"
    assert "MongoDB Atlas" in data["decisions_made"][0]


def test_create_analysis_transcription_not_found(mock_transcription_repo, mock_analysis_service):
    """Verify 404 if source transcription record is not found."""
    mock_transcription_repo.get_by_id.return_value = None
    payload = {
        "source_id": "nonexistent_transcription",
        "source_type": "transcription",
    }
    response = client.post("/api/analysis/", json=payload)
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_create_analysis_transcription_not_completed(mock_transcription_repo, mock_analysis_service):
    """Verify 400 if source transcription is still processing or queued."""
    mock_transcription_repo.get_by_id.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "status": "processing",
        "transcript_text": None,
    }
    payload = {
        "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "transcription",
    }
    response = client.post("/api/analysis/", json=payload)
    assert response.status_code == 400
    assert "Wait for transcription to complete" in response.json()["detail"]


def test_create_analysis_transcription_failed(mock_transcription_repo, mock_analysis_service):
    """Verify 400 if source transcription failed."""
    mock_transcription_repo.get_by_id.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "status": "failed",
        "transcript_text": None,
    }
    payload = {
        "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "transcription",
    }
    response = client.post("/api/analysis/", json=payload)
    assert response.status_code == 400
    assert "Cannot analyze a failed transcription" in response.json()["detail"]


def test_create_analysis_from_document_success(
    mock_analysis_repo, mock_document_repo, mock_analysis_service
):
    """Verify POST /api/analysis/ successfully analyzes an ingested document."""
    now = datetime.now(timezone.utc)
    mock_document_repo.get_by_id.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "title": "meeting_notes.docx",
        "text_content": "Project kickoff discussion notes.",
    }
    mock_analysis_repo.create.return_value = {
        "id": "751a2b3c4d5e6f7a8b9c0d1e",
        "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "document",
        "title": "meeting_notes.docx",
        "executive_summary": "Team aligned on cloud architecture goals and timeline.",
        "meeting_purpose": "Review infrastructure plan.",
        "key_discussion_points": ["Database read performance"],
        "decisions_made": ["Approved MongoDB Atlas deployment"],
        "risks_and_blockers": [],
        "unresolved_questions": [],
        "topics_and_themes": ["Infrastructure"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    payload = {
        "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "document",
    }
    response = client.post("/api/analysis/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "document"


def test_create_analysis_from_direct_text_success(
    mock_analysis_repo, mock_analysis_service
):
    """Verify POST /api/analysis/ accepts and analyzes direct text."""
    now = datetime.now(timezone.utc)
    mock_analysis_repo.create.return_value = {
        "id": "751a2b3c4d5e6f7a8b9c0d1e",
        "source_id": None,
        "source_type": "direct_text",
        "title": "Quick Meeting Notes",
        "executive_summary": "Team aligned on cloud architecture goals and timeline.",
        "meeting_purpose": "Review infrastructure plan.",
        "key_discussion_points": ["Architecture review"],
        "decisions_made": ["Approved MongoDB Atlas deployment"],
        "risks_and_blockers": [],
        "unresolved_questions": [],
        "topics_and_themes": ["Tech"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    payload = {
        "source_type": "direct_text",
        "text": "Direct meeting transcript content here.",
        "title": "Quick Meeting Notes",
    }
    response = client.post("/api/analysis/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "direct_text"


def test_create_analysis_missing_llm_key(mock_analysis_service):
    """Verify 503 is returned when LLM API key is not configured."""
    mock_analysis_service.analyze_meeting.side_effect = LLMConfigurationError(
        "Groq API key is not configured."
    )
    payload = {
        "source_type": "direct_text",
        "text": "Meeting notes content.",
    }
    response = client.post("/api/analysis/", json=payload)
    assert response.status_code == 503
    assert "Groq API key is not configured" in response.json()["detail"]


def test_create_analysis_llm_rate_limit(mock_analysis_service):
    """Verify 503 is returned when LLM rate limit is hit."""
    mock_analysis_service.analyze_meeting.side_effect = LLMRateLimitError(
        "Groq rate limit exceeded."
    )
    payload = {
        "source_type": "direct_text",
        "text": "Meeting notes content.",
    }
    response = client.post("/api/analysis/", json=payload)
    assert response.status_code == 503
    assert "rate limit" in response.json()["detail"].lower()


def test_create_analysis_llm_timeout(mock_analysis_service):
    """Verify 504 is returned when LLM times out."""
    mock_analysis_service.analyze_meeting.side_effect = LLMTimeoutError(
        "Request timed out."
    )
    payload = {
        "source_type": "direct_text",
        "text": "Meeting notes content.",
    }
    response = client.post("/api/analysis/", json=payload)
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


def test_create_analysis_llm_malformed_output(mock_analysis_service):
    """Verify 502 is returned when LLM produces malformed output."""
    mock_analysis_service.analyze_meeting.side_effect = LLMOutputParsingError(
        "LLM returned malformed JSON."
    )
    payload = {
        "source_type": "direct_text",
        "text": "Meeting notes content.",
    }
    response = client.post("/api/analysis/", json=payload)
    assert response.status_code == 502
    assert "malformed JSON" in response.json()["detail"]


def test_create_analysis_db_error(
    mock_analysis_repo, mock_analysis_service
):
    """Verify 503 is returned when MongoDB persistence fails."""
    mock_analysis_repo.create.side_effect = PyMongoError("DB connection dropped")
    payload = {
        "source_type": "direct_text",
        "text": "Meeting notes content.",
    }
    response = client.post("/api/analysis/", json=payload)
    assert response.status_code == 503
    assert "Database service is unavailable" in response.json()["detail"]


# --- Get, List, Delete Route Tests ---


def test_get_analysis_by_id_found(mock_analysis_repo):
    """Verify GET /api/analysis/{analysis_id} returns record when found."""
    now = datetime.now(timezone.utc)
    mock_analysis_repo.get_by_id.return_value = {
        "id": "751a2b3c4d5e6f7a8b9c0d1e",
        "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "transcription",
        "title": "Strategy Review",
        "executive_summary": "Summary text.",
        "meeting_purpose": "Purpose text.",
        "key_discussion_points": ["Point 1"],
        "decisions_made": ["Decision 1"],
        "risks_and_blockers": ["Risk 1"],
        "unresolved_questions": ["Question 1"],
        "topics_and_themes": ["Theme 1"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    response = client.get("/api/analysis/751a2b3c4d5e6f7a8b9c0d1e")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "751a2b3c4d5e6f7a8b9c0d1e"
    assert data["executive_summary"] == "Summary text."


def test_get_analysis_by_id_not_found(mock_analysis_repo):
    """Verify GET /api/analysis/{analysis_id} returns 404 when not found."""
    mock_analysis_repo.get_by_id.return_value = None
    response = client.get("/api/analysis/nonexistent_analysis_id")
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_list_analyses(mock_analysis_repo):
    """Verify GET /api/analysis/ returns paginated list of analyses."""
    now = datetime.now(timezone.utc)
    mock_analysis_repo.list_records.return_value = (
        [
            {
                "id": "751a2b3c4d5e6f7a8b9c0d1e",
                "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "source_type": "transcription",
                "title": "Strategy Review",
                "executive_summary": "Summary text.",
                "meeting_purpose": "Purpose text.",
                "key_discussion_points": ["Point 1"],
                "decisions_made": ["Decision 1"],
                "risks_and_blockers": [],
                "unresolved_questions": [],
                "topics_and_themes": [],
                "llm_provider": "groq",
                "llm_model": "llama-3.3-70b-versatile",
                "status": "completed",
                "error_message": None,
                "created_at": now,
                "updated_at": now,
            }
        ],
        1,
    )

    response = client.get("/api/analysis/?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_delete_analysis(mock_analysis_repo):
    """Verify DELETE /api/analysis/{analysis_id} deletes record."""
    mock_analysis_repo.delete.return_value = True
    response = client.delete("/api/analysis/751a2b3c4d5e6f7a8b9c0d1e")
    assert response.status_code == 204

    mock_analysis_repo.delete.return_value = False
    response = client.delete("/api/analysis/nonexistent_analysis_id")
    assert response.status_code == 404
