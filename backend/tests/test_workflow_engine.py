"""Unit tests for WorkflowEngine execution and error handling."""

from unittest.mock import MagicMock
import mongomock
import pytest
from app.repositories.workflow_repo import WorkflowRepository
from app.workflows.workflow_engine import (
    WorkflowEngine,
    get_compiled_workflow_graph,
    get_workflow_engine,
)


def test_workflow_engine_singleton():
    """Verify get_workflow_engine and get_compiled_workflow_graph singletons."""
    engine = get_workflow_engine()
    assert isinstance(engine, WorkflowEngine)

    graph = get_compiled_workflow_graph()
    assert graph is not None


def test_workflow_engine_execute_unsupported_source_type():
    """Test executing workflow with invalid source type fails at input_validation stage."""
    mock_db = mongomock.MongoClient()["test_db"]
    repo = WorkflowRepository(db=mock_db)
    engine = WorkflowEngine(workflow_repo=repo)

    doc = repo.create({"source_type": "invalid_type"})
    result = engine.execute_workflow(
        workflow_id=doc["id"],
        initial_input={"source_type": "invalid_type"},
    )

    assert result["status"] == "failed"
    assert result["error_stage"] == "input_validation"
    assert "Unsupported source type" in result["error_message"]

    # Verify MongoDB record updated
    updated = repo.get_by_id(doc["id"])
    assert updated["status"] == "failed"
    assert updated["error_stage"] == "input_validation"
