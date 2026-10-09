"""Unit tests for WorkflowRepository using mongomock."""

from datetime import datetime, timezone
from bson import ObjectId
import mongomock
import pytest
from app.repositories.workflow_repo import (
    WorkflowRepository,
    format_workflow_record,
)


def test_format_workflow_record_helper():
    """Verify format_workflow_record handles None and converts ObjectId to string id."""
    assert format_workflow_record(None) is None

    oid = ObjectId()
    doc = {"_id": oid, "source_type": "transcription", "status": "queued"}
    formatted = format_workflow_record(doc)
    assert formatted is not None
    assert formatted["id"] == str(oid)
    assert "_id" not in formatted
    assert formatted["source_type"] == "transcription"


def test_workflow_repository_uninitialized_db_raises():
    """Verify accessing db property when uninitialized raises RuntimeError."""
    repo = WorkflowRepository(db=None)
    with pytest.raises(RuntimeError, match="Database connection is not initialized"):
        _ = repo.db


def test_workflow_repository_crud_operations():
    """Test create, get, update, stage transitions, list, and delete on WorkflowRepository."""
    mock_db = mongomock.MongoClient()["test_db"]
    repo = WorkflowRepository(db=mock_db)

    # 1. Create
    created = repo.create({
        "source_type": "transcription",
        "source_id": "trans_123",
        "title": "Quarterly Review",
    })
    assert created["id"] is not None
    assert created["status"] == "queued"
    assert created["current_stage"] == "queued"

    # 2. Get by ID
    fetched = repo.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["title"] == "Quarterly Review"

    # Invalid ID returns None
    assert repo.get_by_id("invalid-hex-id") is None
    assert repo.get_by_id(str(ObjectId())) is None

    # 3. Update stage and status
    now = datetime.now(timezone.utc)
    updated = repo.update_stage_and_status(
        workflow_id=created["id"],
        stage="finalized",
        status="completed",
        analysis_id="analysis_abc",
        completed_at=now,
    )
    assert updated is not None
    assert updated["current_stage"] == "finalized"
    assert updated["status"] == "completed"
    assert updated["analysis_id"] == "analysis_abc"

    # 4. List workflows
    items, total = repo.list_workflows(status="completed")
    assert total == 1
    assert len(items) == 1

    items_failed, total_failed = repo.list_workflows(status="failed")
    assert total_failed == 0

    # 5. Delete
    assert repo.delete(created["id"]) is True
    assert repo.delete(created["id"]) is False
    assert repo.delete("invalid-id") is False
