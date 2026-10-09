"""Unit tests for workflow Pydantic schemas."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.analysis import AnalysisSourceType
from app.schemas.workflow import (
    WorkflowListResponse,
    WorkflowResultResponse,
    WorkflowStage,
    WorkflowStartRequest,
    WorkflowStatus,
    WorkflowStatusResponse,
)


def test_workflow_enums():
    """Verify enum values for WorkflowStatus and WorkflowStage."""
    assert WorkflowStatus.QUEUED.value == "queued"
    assert WorkflowStatus.PROCESSING.value == "processing"
    assert WorkflowStatus.COMPLETED.value == "completed"
    assert WorkflowStatus.FAILED.value == "failed"

    assert WorkflowStage.QUEUED.value == "queued"
    assert WorkflowStage.INPUT_VALIDATION.value == "input_validation"
    assert WorkflowStage.SOURCE_RETRIEVAL.value == "source_retrieval"
    assert WorkflowStage.MEETING_ANALYSIS.value == "meeting_analysis"
    assert WorkflowStage.ACTION_ITEM_EXTRACTION.value == "action_item_extraction"
    assert WorkflowStage.FOLLOW_UP_PLANNING.value == "follow_up_planning"
    assert WorkflowStage.FINALIZED.value == "finalized"
    assert WorkflowStage.FAILED.value == "failed"


def test_workflow_start_request_validation():
    """Test validation of WorkflowStartRequest."""
    req = WorkflowStartRequest(
        source_type=AnalysisSourceType.TRANSCRIPTION,
        source_id="651a2b3c4d5e6f7a8b9c0d1e",
        title="Weekly Sync",
        force_reanalyze=True,
    )
    assert req.source_type == AnalysisSourceType.TRANSCRIPTION
    assert req.source_id == "651a2b3c4d5e6f7a8b9c0d1e"
    assert req.title == "Weekly Sync"
    assert req.force_reanalyze is True

    # Test defaults
    req_default = WorkflowStartRequest()
    assert req_default.source_type == AnalysisSourceType.TRANSCRIPTION
    assert req_default.source_id is None
    assert req_default.force_reanalyze is False


def test_workflow_status_response_schema():
    """Test WorkflowStatusResponse serialization."""
    now = datetime.now(timezone.utc)
    status_resp = WorkflowStatusResponse(
        id="651a2b3c4d5e6f7a8b9c0d1e",
        source_type=AnalysisSourceType.DOCUMENT,
        source_id="doc_123",
        title="Project Plan",
        current_stage=WorkflowStage.FINALIZED,
        status=WorkflowStatus.COMPLETED,
        analysis_id="analysis_123",
        error_stage=None,
        error_message=None,
        created_at=now,
        updated_at=now,
        completed_at=now,
    )
    assert status_resp.id == "651a2b3c4d5e6f7a8b9c0d1e"
    assert status_resp.status == WorkflowStatus.COMPLETED
    assert status_resp.current_stage == WorkflowStage.FINALIZED


def test_workflow_result_response_schema():
    """Test WorkflowResultResponse serialization."""
    now = datetime.now(timezone.utc)
    res = WorkflowResultResponse(
        id="651a2b3c4d5e6f7a8b9c0d1e",
        source_type=AnalysisSourceType.DIRECT_TEXT,
        title="Direct Notes",
        current_stage=WorkflowStage.FINALIZED,
        status=WorkflowStatus.COMPLETED,
        analysis=None,
        tasks=[],
        follow_up_plan=None,
        created_at=now,
        updated_at=now,
    )
    assert res.id == "651a2b3c4d5e6f7a8b9c0d1e"
    assert res.status == WorkflowStatus.COMPLETED
    assert res.tasks == []


def test_workflow_list_response():
    """Test paginated WorkflowListResponse schema."""
    list_resp = WorkflowListResponse(
        items=[],
        total=0,
        page=1,
        page_size=20,
        total_pages=0,
    )
    assert list_resp.total == 0
    assert list_resp.items == []
