"""Unit tests for TaskRepository using mongomock."""

from datetime import datetime, timezone
from bson import ObjectId
import mongomock
import pytest
from app.repositories.task_repo import (
    TaskRepository,
    format_task_record,
)


def test_format_task_record_helper():
    """Verify format_task_record handles None, ObjectId conversion, and preserves fields."""
    assert format_task_record(None) is None

    oid = ObjectId()
    doc = {
        "_id": oid,
        "description": "Prepare quarterly review",
        "assignee": "Alex",
    }
    formatted = format_task_record(doc)
    assert formatted is not None
    assert formatted["id"] == str(oid)
    assert "_id" not in formatted
    assert formatted["description"] == "Prepare quarterly review"


def test_task_repository_uninitialized_db_raises():
    """Verify accessing db property when no connection exists raises RuntimeError."""
    repo = TaskRepository(db=None)
    with pytest.raises(RuntimeError, match="Database connection is not initialized"):
        _ = repo.db


def test_task_repository_create_and_get():
    """Test creating a single task and retrieving it by ID."""
    mock_db = mongomock.MongoClient()["test_db"]
    repo = TaskRepository(db=mock_db)

    task_data = {
        "analysis_id": "651a2b3c4d5e6f7a8b9c0d1e",
        "description": "Configure SSL certificates",
        "assignee": "Ops Team",
        "priority": "high",
        "due_date": "by Friday",
    }
    created = repo.create(task_data)
    assert created["id"] is not None
    assert created["analysis_id"] == "651a2b3c4d5e6f7a8b9c0d1e"
    assert created["description"] == "Configure SSL certificates"
    assert created["status"] == "pending"
    assert not created["has_missing_assignee"]

    fetched = repo.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["assignee"] == "Ops Team"

    # Invalid ID retrieval returns None
    assert repo.get_by_id("invalid-hex-id") is None
    assert repo.get_by_id(str(ObjectId())) is None


def test_task_repository_create_many_with_regeneration_replacement():
    """Test batch creating tasks for an analysis with replace=True removing existing tasks."""
    mock_db = mongomock.MongoClient()["test_db"]
    repo = TaskRepository(db=mock_db)
    analysis_id = "651a2b3c4d5e6f7a8b9c0d1e"

    # Initial extraction
    initial_tasks = [
        {"description": "Old Task 1", "assignee": "Dev 1"},
        {"description": "Old Task 2", "assignee": "Dev 2"},
    ]
    repo.create_many_for_analysis(analysis_id, initial_tasks, replace=True)

    records, total = repo.list_tasks(analysis_id=analysis_id)
    assert total == 2
    assert len(records) == 2

    # Regeneration with new tasks replacing previous ones
    new_tasks = [
        {"description": "New Task A", "assignee": "Dev 3", "priority": "high"},
        {"description": "New Task B", "assignee": None, "has_missing_assignee": True},
        {"description": "New Task C", "assignee": "Dev 4", "due_date": "2026-10-30"},
    ]
    created_new = repo.create_many_for_analysis(analysis_id, new_tasks, replace=True)
    assert len(created_new) == 3

    # Verify old tasks were wiped out and only 3 new tasks exist
    records, total = repo.list_tasks(analysis_id=analysis_id)
    assert total == 3
    descriptions = [t["description"] for t in records]
    assert "Old Task 1" not in descriptions
    assert "New Task A" in descriptions
    assert "New Task B" in descriptions


def test_task_repository_list_and_filters():
    """Test listing tasks with various filter combinations and pagination."""
    mock_db = mongomock.MongoClient()["test_db"]
    repo = TaskRepository(db=mock_db)
    analysis_id = "analysis_123"

    tasks = [
        {"analysis_id": analysis_id, "description": "Task 1", "status": "pending", "priority": "high", "assignee": "Alice"},
        {"analysis_id": analysis_id, "description": "Task 2", "status": "in_progress", "priority": "medium", "assignee": "Bob"},
        {"analysis_id": analysis_id, "description": "Task 3", "status": "completed", "priority": "low", "assignee": "Alice"},
        {"analysis_id": "other_analysis", "description": "Task 4", "status": "pending", "priority": "high", "assignee": "Charlie"},
    ]
    for t in tasks:
        repo.create(t)

    # Filter by analysis_id
    items, total = repo.list_tasks(analysis_id=analysis_id)
    assert total == 3

    # Filter by status
    items, total = repo.list_tasks(status="pending")
    assert total == 2

    # Filter by priority
    items, total = repo.list_tasks(priority="high")
    assert total == 2

    # Filter by assignee
    items, total = repo.list_tasks(assignee="Alice")
    assert total == 2

    # Test get_by_analysis_id helper
    by_analysis = repo.get_by_analysis_id(analysis_id)
    assert len(by_analysis) == 3


def test_task_repository_update_and_status():
    """Test updating task fields and updating status specifically."""
    mock_db = mongomock.MongoClient()["test_db"]
    repo = TaskRepository(db=mock_db)

    task = repo.create({"analysis_id": "123", "description": "Original description", "status": "pending"})
    task_id = task["id"]

    # Partial update
    updated = repo.update(task_id, {"description": "Updated description", "assignee": "Eve"})
    assert updated is not None
    assert updated["description"] == "Updated description"
    assert updated["assignee"] == "Eve"

    # Status update
    status_updated = repo.update_status(task_id, "completed")
    assert status_updated is not None
    assert status_updated["status"] == "completed"

    # Update invalid id returns None
    assert repo.update("invalid-id", {"description": "X"}) is None


def test_task_repository_delete():
    """Test deleting single task and deleting by analysis ID."""
    mock_db = mongomock.MongoClient()["test_db"]
    repo = TaskRepository(db=mock_db)

    task1 = repo.create({"analysis_id": "delete_test", "description": "Task to delete"})
    task2 = repo.create({"analysis_id": "delete_test", "description": "Task to delete 2"})

    # Delete single
    assert repo.delete(task1["id"]) is True
    assert repo.delete(task1["id"]) is False  # Second delete should return False
    assert repo.delete("invalid-id") is False

    # Delete by analysis
    deleted_count = repo.delete_by_analysis_id("delete_test")
    assert deleted_count == 1  # only task2 was left
