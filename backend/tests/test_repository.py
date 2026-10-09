"""Tests for Transcription MongoDB Repository."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from bson import ObjectId
from app.repositories.transcription_repo import TranscriptionRepository, _format_record
from app.schemas.transcription import TranscriptionStatus


def test_format_record_helper():
    """Verify _format_record converts _id to string id and removes _id."""
    obj_id = ObjectId()
    raw = {"_id": obj_id, "filename": "sample.mp3"}
    formatted = _format_record(raw)
    assert formatted is not None
    assert formatted["id"] == str(obj_id)
    assert "_id" not in formatted

    assert _format_record(None) is None


def test_repository_uninitialized_db_raises():
    """Verify repository raises RuntimeError if database is not connected."""
    repo = TranscriptionRepository(db=None)
    with pytest.raises(RuntimeError, match="Database connection is not initialized"):
        _ = repo.db


def test_repository_create_queued_and_status_transitions():
    """Verify create_queued, mark_processing, mark_completed, and mark_failed."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    repo = TranscriptionRepository(db=mock_db)
    fake_id = ObjectId()

    # 1. Test create_queued
    mock_collection.insert_one.return_value = MagicMock(inserted_id=fake_id)
    created = repo.create_queued(
        filename="meeting.mp3",
        file_format="mp3",
        file_size_bytes=1048576,
        whisper_model="small",
        requested_language="en",
    )
    assert created["id"] == str(fake_id)
    assert created["original_filename"] == "meeting.mp3"
    assert created["status"] == TranscriptionStatus.QUEUED.value
    assert created["requested_language"] == "en"

    # 2. Test mark_processing
    mock_collection.find_one_and_update.return_value = {
        "_id": fake_id,
        "status": TranscriptionStatus.PROCESSING.value,
    }
    processing_doc = repo.mark_processing(str(fake_id))
    assert processing_doc is not None
    assert processing_doc["status"] == "processing"

    # 3. Test mark_completed
    mock_collection.find_one_and_update.return_value = {
        "_id": fake_id,
        "status": TranscriptionStatus.COMPLETED.value,
        "transcript_text": "Meeting notes content.",
        "detected_language": "en",
        "audio_duration": 45.0,
    }
    completed_doc = repo.mark_completed(
        record_id=str(fake_id),
        transcript_text="Meeting notes content.",
        detected_language="en",
        audio_duration=45.0,
        whisper_model="small",
    )
    assert completed_doc is not None
    assert completed_doc["status"] == "completed"
    assert completed_doc["transcript_text"] == "Meeting notes content."
    assert completed_doc["detected_language"] == "en"

    # 4. Test mark_failed
    mock_collection.find_one_and_update.return_value = {
        "_id": fake_id,
        "status": TranscriptionStatus.FAILED.value,
        "error_message": "Audio format was corrupted.",
    }
    failed_doc = repo.mark_failed(
        record_id=str(fake_id),
        error_message="Audio format was corrupted.",
    )
    assert failed_doc is not None
    assert failed_doc["status"] == "failed"
    assert failed_doc["error_message"] == "Audio format was corrupted."


def test_repository_get_by_id_and_delete():
    """Verify get_by_id and delete handling."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    repo = TranscriptionRepository(db=mock_db)

    fake_id = ObjectId()
    mock_collection.find_one.return_value = {
        "_id": fake_id,
        "original_filename": "strategy.wav",
        "status": "completed",
    }
    found = repo.get_by_id(str(fake_id))
    assert found is not None
    assert found["id"] == str(fake_id)

    # Invalid ID
    assert repo.get_by_id("invalid-hex") is None

    # Delete
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    assert repo.delete(str(fake_id)) is True

    mock_collection.delete_one.return_value = MagicMock(deleted_count=0)
    assert repo.delete(str(fake_id)) is False
