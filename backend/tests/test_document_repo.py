"""Tests for DocumentRepository managing MongoDB documents collection."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from bson import ObjectId
from app.repositories.document_repo import DocumentRepository, _format_document_record


def test_format_document_record_helper():
    """Verify _format_document_record converts _id to string id."""
    fake_id = ObjectId()
    raw = {"_id": fake_id, "title": "Doc 1"}
    formatted = _format_document_record(raw)
    assert formatted is not None
    assert formatted["id"] == str(fake_id)
    assert "_id" not in formatted

    assert _format_document_record(None) is None


def test_document_repository_uninitialized_db_raises():
    """Verify repository raises RuntimeError when database connection is None."""
    repo = DocumentRepository(db=None)
    with pytest.raises(RuntimeError, match="Database connection is not initialized"):
        _ = repo.db


def test_document_repository_crud_operations():
    """Verify CRUD operations with mock database."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    repo = DocumentRepository(db=mock_db)
    fake_id = ObjectId()

    # 1. Test create
    mock_collection.insert_one.return_value = MagicMock(inserted_id=fake_id)
    created = repo.create({
        "source_type": "pdf",
        "title": "meeting_agenda.pdf",
        "original_filename": "meeting_agenda.pdf",
        "file_format": "pdf",
        "file_size_bytes": 1024,
        "text_content": "Meeting agenda items...",
        "character_count": 22,
        "word_count": 3,
        "status": "completed",
    })
    assert created["id"] == str(fake_id)
    assert created["title"] == "meeting_agenda.pdf"
    assert created["source_type"] == "pdf"
    assert "created_at" in created

    # 2. Test get_by_id found
    mock_collection.find_one.return_value = {
        "_id": fake_id,
        "title": "meeting_agenda.pdf",
        "source_type": "pdf",
    }
    found = repo.get_by_id(str(fake_id))
    assert found is not None
    assert found["id"] == str(fake_id)

    # 3. Test get_by_id invalid hex
    assert repo.get_by_id("invalid-id") is None

    # 4. Test list_records
    mock_collection.count_documents.return_value = 1
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value.skip.return_value.limit.return_value = [
        {"_id": fake_id, "title": "meeting_agenda.pdf", "source_type": "pdf"}
    ]
    mock_collection.find.return_value = mock_cursor

    items, total = repo.list_records(skip=0, limit=20, source_type="pdf")
    assert total == 1
    assert len(items) == 1
    assert items[0]["id"] == str(fake_id)

    # 5. Test delete
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    assert repo.delete(str(fake_id)) is True

    mock_collection.delete_one.return_value = MagicMock(deleted_count=0)
    assert repo.delete(str(fake_id)) is False
