"""Tests for Document and Pasted Text Ingestion API routes."""

from datetime import datetime, timezone
import io
import os
from unittest.mock import MagicMock, patch
import docx
import pytest
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError
from app.config import Settings, get_settings
from app.main import app
from app.repositories.document_repo import get_document_repository

client = TestClient(app)


@pytest.fixture
def mock_doc_repo():
    """Override DocumentRepository dependency with a mock."""
    mock = MagicMock()
    app.dependency_overrides[get_document_repository] = lambda: mock
    yield mock
    app.dependency_overrides.clear()


# --- Upload Document Endpoint Tests ---


def test_upload_txt_success(mock_doc_repo):
    """Verify POST /api/documents/upload accepts valid TXT and returns 201."""
    now = datetime.now(timezone.utc)
    mock_doc_repo.create.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "txt",
        "title": "meeting_notes.txt",
        "original_filename": "meeting_notes.txt",
        "file_format": "txt",
        "file_size_bytes": 120,
        "text_content": "Sprint Review:\nAll tasks completed.",
        "character_count": 35,
        "word_count": 5,
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    content = b"Sprint Review:\nAll tasks completed."
    files = {"file": ("meeting_notes.txt", io.BytesIO(content), "text/plain")}
    response = client.post("/api/documents/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "651a2b3c4d5e6f7a8b9c0d1e"
    assert data["source_type"] == "txt"
    assert "Sprint Review" in data["text_content"]


def test_upload_docx_success(mock_doc_repo):
    """Verify POST /api/documents/upload extracts and persists valid DOCX content."""
    doc = docx.Document()
    doc.add_heading("Client Meeting", 0)
    doc.add_paragraph("Agreed on project scope and deliverables.")
    stream = io.BytesIO()
    doc.save(stream)
    docx_bytes = stream.getvalue()

    now = datetime.now(timezone.utc)
    mock_doc_repo.create.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "docx",
        "title": "client_meeting.docx",
        "original_filename": "client_meeting.docx",
        "file_format": "docx",
        "file_size_bytes": len(docx_bytes),
        "text_content": "Client Meeting\n\nAgreed on project scope and deliverables.",
        "character_count": 58,
        "word_count": 8,
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    files = {"file": ("client_meeting.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    response = client.post("/api/documents/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "docx"
    assert "Client Meeting" in data["text_content"]


def test_upload_pdf_success_mocked(mock_doc_repo):
    """Verify POST /api/documents/upload extracts digital PDF text."""
    now = datetime.now(timezone.utc)
    mock_doc_repo.create.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "pdf",
        "title": "board_minutes.pdf",
        "original_filename": "board_minutes.pdf",
        "file_format": "pdf",
        "file_size_bytes": 1024,
        "text_content": "Board Meeting Minutes\n\nApproved budget.",
        "character_count": 38,
        "word_count": 5,
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Board Meeting Minutes\n\nApproved budget."
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("pypdf.PdfReader", return_value=mock_reader):
        files = {"file": ("board_minutes.pdf", io.BytesIO(b"%PDF-1.4 dummy pdf"), "application/pdf")}
        response = client.post("/api/documents/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "pdf"
    assert "Board Meeting Minutes" in data["text_content"]


def test_upload_document_unsupported_extension(mock_doc_repo):
    """Verify upload rejects unsupported document formats like .xlsx, .pptx, .png."""
    files = {"file": ("sheet.xlsx", io.BytesIO(b"excel content"), "application/vnd.ms-excel")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported document format" in response.json()["detail"]


def test_upload_document_empty_file(mock_doc_repo):
    """Verify upload rejects empty 0-byte files."""
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_upload_document_scanned_pdf_rejection(mock_doc_repo):
    """Verify scanned/image-only PDF with no digital text is rejected with 422."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "   "  # No extractable text
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("pypdf.PdfReader", return_value=mock_reader):
        files = {"file": ("scanned.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")}
        response = client.post("/api/documents/upload", files=files)

    assert response.status_code == 422
    assert "No extractable text found in the PDF" in response.json()["detail"]


def test_upload_document_corrupt_file(mock_doc_repo):
    """Verify corrupt document returns 422 Unprocessable Entity."""
    files = {"file": ("damaged.docx", io.BytesIO(b"not a real docx archive"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 422
    assert "corrupt" in response.json()["detail"].lower()


def test_upload_document_size_limit(mock_doc_repo):
    """Verify upload rejects document exceeding MAX_UPLOAD_SIZE_MB with 413."""
    def custom_settings():
        return Settings(MAX_UPLOAD_SIZE_MB=0.0001)

    app.dependency_overrides[get_settings] = custom_settings
    try:
        large_content = b"x" * (1024 * 50)
        files = {"file": ("large.txt", io.BytesIO(large_content), "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 413
        assert "exceeds maximum allowed upload size" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_upload_document_db_error(mock_doc_repo):
    """Verify 503 is returned when database persistence fails."""
    mock_doc_repo.create.side_effect = PyMongoError("Connection lost")
    files = {"file": ("notes.txt", io.BytesIO(b"valid notes content"), "text/plain")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 503
    assert "Database service is unavailable" in response.json()["detail"]


# --- Pasted Text Endpoint Tests ---


def test_submit_pasted_text_success(mock_doc_repo):
    """Verify POST /api/documents/text persists pasted meeting notes."""
    now = datetime.now(timezone.utc)
    mock_doc_repo.create.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "pasted_text",
        "title": "Quick Standup Notes",
        "original_filename": None,
        "file_format": None,
        "file_size_bytes": 45,
        "text_content": "Bob completed ticket 123. Alice testing.",
        "character_count": 40,
        "word_count": 6,
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    payload = {
        "title": "Quick Standup Notes",
        "text": "Bob completed ticket 123. Alice testing.",
    }
    response = client.post("/api/documents/text", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "651a2b3c4d5e6f7a8b9c0d1e"
    assert data["source_type"] == "pasted_text"
    assert data["title"] == "Quick Standup Notes"


def test_submit_pasted_text_empty_rejected(mock_doc_repo):
    """Verify empty or whitespace-only pasted text is rejected with 400 or 422."""
    response = client.post("/api/documents/text", json={"text": "   \n\n\t  "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


# --- List, Get, and Delete Document Tests ---


def test_list_documents_route(mock_doc_repo):
    """Verify GET /api/documents/ returns paginated documents."""
    now = datetime.now(timezone.utc)
    mock_doc_repo.list_records.return_value = (
        [
            {
                "id": "651a2b3c4d5e6f7a8b9c0d1e",
                "source_type": "txt",
                "title": "notes.txt",
                "original_filename": "notes.txt",
                "file_format": "txt",
                "file_size_bytes": 100,
                "text_content": "Meeting notes content.",
                "character_count": 22,
                "word_count": 3,
                "status": "completed",
                "error_message": None,
                "created_at": now,
                "updated_at": now,
            }
        ],
        1,
    )

    response = client.get("/api/documents/?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == "651a2b3c4d5e6f7a8b9c0d1e"


def test_get_document_by_id_found(mock_doc_repo):
    """Verify GET /api/documents/{id} returns document when found."""
    now = datetime.now(timezone.utc)
    mock_doc_repo.get_by_id.return_value = {
        "id": "651a2b3c4d5e6f7a8b9c0d1e",
        "source_type": "pdf",
        "title": "spec.pdf",
        "original_filename": "spec.pdf",
        "file_format": "pdf",
        "file_size_bytes": 5000,
        "text_content": "Specification content.",
        "character_count": 22,
        "word_count": 2,
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    response = client.get("/api/documents/651a2b3c4d5e6f7a8b9c0d1e")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "651a2b3c4d5e6f7a8b9c0d1e"
    assert data["source_type"] == "pdf"


def test_get_document_by_id_not_found(mock_doc_repo):
    """Verify GET /api/documents/{id} returns 404 when document does not exist."""
    mock_doc_repo.get_by_id.return_value = None
    response = client.get("/api/documents/nonexistent_doc_id")
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_delete_document(mock_doc_repo):
    """Verify DELETE /api/documents/{id} removes document."""
    mock_doc_repo.delete.return_value = True
    response = client.delete("/api/documents/651a2b3c4d5e6f7a8b9c0d1e")
    assert response.status_code == 204

    mock_doc_repo.delete.return_value = False
    response = client.delete("/api/documents/nonexistent_doc_id")
    assert response.status_code == 404
