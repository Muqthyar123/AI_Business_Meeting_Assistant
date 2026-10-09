"""Unit tests for task, action-item, and follow-up plan Pydantic schemas."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.task import (
    ActionItemExtractionResult,
    ExtractedTaskItem,
    FollowUpPlanResponse,
    TaskCreateRequest,
    TaskExportFormat,
    TaskListResponse,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)


def test_task_enums():
    """Verify enum values for task priorities, statuses, and export formats."""
    assert TaskPriority.LOW.value == "low"
    assert TaskPriority.MEDIUM.value == "medium"
    assert TaskPriority.HIGH.value == "high"
    assert TaskPriority.UNKNOWN.value == "unknown"

    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.CANCELLED.value == "cancelled"

    assert TaskExportFormat.JSON.value == "json"
    assert TaskExportFormat.CSV.value == "csv"
    assert TaskExportFormat.MARKDOWN.value == "markdown"


def test_extracted_task_item_schema():
    """Test validation of raw LLM extracted task items."""
    item = ExtractedTaskItem(
        description="Set up CI/CD pipeline",
        assignee="DevOps Team",
        has_missing_assignee=False,
        due_date="Next Monday",
        priority=TaskPriority.HIGH,
        dependencies=["Provision cloud runner"],
        evidence_excerpt="DevOps Team will set up CI/CD pipeline by next Monday.",
    )
    assert item.description == "Set up CI/CD pipeline"
    assert item.assignee == "DevOps Team"
    assert not item.has_missing_assignee
    assert item.priority == TaskPriority.HIGH
    assert item.dependencies == ["Provision cloud runner"]

    # Test defaults
    item_default = ExtractedTaskItem(description="Unassigned task")
    assert item_default.assignee is None
    assert not item_default.has_missing_assignee
    assert item_default.due_date is None
    assert item_default.priority == TaskPriority.UNKNOWN
    assert item_default.dependencies == []


def test_action_item_extraction_result_schema():
    """Test container schema for extracted action items."""
    result = ActionItemExtractionResult(
        tasks=[
            ExtractedTaskItem(
                description="Draft contract",
                assignee="Legal",
                priority=TaskPriority.MEDIUM,
            )
        ]
    )
    assert len(result.tasks) == 1
    assert result.tasks[0].description == "Draft contract"


def test_task_create_request_validation():
    """Test TaskCreateRequest validation rules."""
    req = TaskCreateRequest(
        analysis_id="651a2b3c4d5e6f7a8b9c0d1e",
        description="Review security findings",
        assignee="Sarah",
        priority=TaskPriority.HIGH,
    )
    assert req.analysis_id == "651a2b3c4d5e6f7a8b9c0d1e"
    assert req.description == "Review security findings"
    assert req.status == TaskStatus.PENDING

    # Empty description should fail
    with pytest.raises(ValidationError):
        TaskCreateRequest(analysis_id="123", description="")


def test_task_update_request():
    """Test partial TaskUpdateRequest fields."""
    req = TaskUpdateRequest(
        status=TaskStatus.COMPLETED,
        assignee="Alex",
    )
    dumped = req.model_dump(exclude_unset=True)
    assert dumped == {"status": TaskStatus.COMPLETED, "assignee": "Alex"}


def test_task_status_update_request():
    """Test TaskStatusUpdateRequest schema."""
    req = TaskStatusUpdateRequest(status=TaskStatus.IN_PROGRESS)
    assert req.status == TaskStatus.IN_PROGRESS


def test_task_response_and_list_response():
    """Test full TaskResponse and paginated TaskListResponse serialization."""
    now = datetime.now(timezone.utc)
    task_resp = TaskResponse(
        id="651a2b3c4d5e6f7a8b9c0d1e",
        analysis_id="651a2b3c4d5e6f7a8b9c0d1f",
        description="Fix bug in auth middleware",
        assignee="David",
        has_missing_assignee=False,
        due_date="2026-10-15",
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        dependencies=["Auth redesign doc"],
        evidence_excerpt="David will fix the auth middleware bug.",
        created_at=now,
        updated_at=now,
    )
    assert task_resp.id == "651a2b3c4d5e6f7a8b9c0d1e"
    assert task_resp.priority == TaskPriority.HIGH

    list_resp = TaskListResponse(
        items=[task_resp],
        total=1,
        page=1,
        page_size=50,
        total_pages=1,
    )
    assert list_resp.total == 1
    assert len(list_resp.items) == 1


def test_follow_up_plan_response_schema():
    """Test FollowUpPlanResponse structure."""
    now = datetime.now(timezone.utc)
    plan = FollowUpPlanResponse(
        analysis_id="651a2b3c4d5e6f7a8b9c0d1e",
        immediate_actions=[],
        upcoming_tasks=[],
        clarification_needed=[],
        blockers_and_dependencies=[],
        pending_decisions=["Decide on cloud provider"],
        ai_suggestions=["Assign owners to unassigned tasks."],
        total_tasks=0,
        generated_at=now,
    )
    assert plan.analysis_id == "651a2b3c4d5e6f7a8b9c0d1e"
    assert plan.pending_decisions == ["Decide on cloud provider"]
    assert len(plan.ai_suggestions) == 1
