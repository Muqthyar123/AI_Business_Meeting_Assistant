"""Tests for AnalysisRepository managing MongoDB meeting_analyses collection."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from bson import ObjectId
from app.repositories.analysis_repo import AnalysisRepository, _format_analysis_record


def test_format_analysis_record_helper():
    """Verify _format_analysis_record converts _id to string id."""
    fake_id = ObjectId()
    raw = {"_id": fake_id, "title": "Analysis 1"}
    formatted = _format_analysis_record(raw)
    assert formatted is not None
    assert formatted["id"] == str(fake_id)
    assert "_id" not in formatted

    assert _format_analysis_record(None) is None


def test_analysis_repository_uninitialized_db_raises():
    """Verify repository raises RuntimeError when db is None."""
    repo = AnalysisRepository(db=None)
    with pytest.raises(RuntimeError, match="Database connection is not initialized"):
        _ = repo.db


def test_analysis_repository_crud_operations():
    """Verify CRUD operations on AnalysisRepository with mock database."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    repo = AnalysisRepository(db=mock_db)
    fake_id = ObjectId()
    fake_source_id = str(ObjectId())

    # 1. Test create
    mock_collection.insert_one.return_value = MagicMock(inserted_id=fake_id)
    created = repo.create({
        "source_id": fake_source_id,
        "source_type": "transcription",
        "title": "Strategy Meeting",
        "executive_summary": "Executive summary content.",
        "meeting_purpose": "Quarterly planning.",
        "key_discussion_points": ["Point 1"],
        "decisions_made": ["Decision 1"],
        "risks_and_blockers": ["Risk 1"],
        "unresolved_questions": ["Question 1"],
        "topics_and_themes": ["Planning"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "status": "completed",
    })
    assert created["id"] == str(fake_id)
    assert created["source_id"] == fake_source_id
    assert created["status"] == "completed"
    assert "created_at" in created

    # 2. Test get_by_id found
    mock_collection.find_one.return_value = {
        "_id": fake_id,
        "source_id": fake_source_id,
        "title": "Strategy Meeting",
    }
    found = repo.get_by_id(str(fake_id))
    assert found is not None
    assert found["id"] == str(fake_id)

    # 3. Test get_by_id invalid hex
    assert repo.get_by_id("invalid-hex") is None

    # 4. Test get_by_source_id found
    found_by_source = repo.get_by_source_id(fake_source_id)
    assert found_by_source is not None
    assert found_by_source["id"] == str(fake_id)

    # 5. Test list_records
    mock_collection.count_documents.return_value = 1
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value.skip.return_value.limit.return_value = [
        {"_id": fake_id, "title": "Strategy Meeting", "source_type": "transcription"}
    ]
    mock_collection.find.return_value = mock_cursor

    items, total = repo.list_records(skip=0, limit=20, source_type="transcription")
    assert total == 1
    assert len(items) == 1

    # 6. Test delete
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    assert repo.delete(str(fake_id)) is True

    mock_collection.delete_one.return_value = MagicMock(deleted_count=0)
    assert repo.delete(str(fake_id)) is False
