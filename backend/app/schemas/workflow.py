"""Pydantic schemas for LangGraph Workflow Orchestration."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.analysis import AnalysisResponse, AnalysisSourceType
from app.schemas.task import FollowUpPlanResponse, TaskResponse


class WorkflowStatus(str, Enum):
    """Lifecycle execution status of a LangGraph workflow run."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStage(str, Enum):
    """Execution stages in the end-to-end meeting processing workflow graph."""

    QUEUED = "queued"
    INPUT_VALIDATION = "input_validation"
    SOURCE_RETRIEVAL = "source_retrieval"
    MEETING_ANALYSIS = "meeting_analysis"
    ACTION_ITEM_EXTRACTION = "action_item_extraction"
    FOLLOW_UP_PLANNING = "follow_up_planning"
    FINALIZED = "finalized"
    FAILED = "failed"


class WorkflowStartRequest(BaseModel):
    """Request payload to initiate an end-to-end meeting processing workflow."""

    source_type: AnalysisSourceType = Field(
        default=AnalysisSourceType.TRANSCRIPTION,
        description="Origin of the meeting content ('transcription', 'document', 'direct_text', 'pasted_text')",
    )
    source_id: Optional[str] = Field(
        default=None,
        description="ID of the transcription or document record in MongoDB (required if source_type is transcription/document)",
    )
    text: Optional[str] = Field(
        default=None,
        description="Direct meeting notes text (required if source_type is 'direct_text' or 'pasted_text')",
    )
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional title for the meeting analysis",
    )
    force_reanalyze: bool = Field(
        default=False,
        description="If True, bypasses existing cached analysis and regenerates fresh analysis and tasks",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_type": "transcription",
                "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "title": "Quarterly Executive Alignment",
                "force_reanalyze": False,
            }
        }
    )


class WorkflowStatusResponse(BaseModel):
    """Status tracking response for a meeting processing workflow run."""

    id: str = Field(description="Unique workflow run ID (hex string)")
    source_type: AnalysisSourceType = Field(description="Source content type")
    source_id: Optional[str] = Field(default=None, description="Referenced source record ID if any")
    title: Optional[str] = Field(default=None, description="Meeting title or subject")
    current_stage: WorkflowStage = Field(
        default=WorkflowStage.QUEUED,
        description="Current processing stage in the LangGraph pipeline",
    )
    status: WorkflowStatus = Field(
        default=WorkflowStatus.QUEUED,
        description="Overall workflow status",
    )
    analysis_id: Optional[str] = Field(
        default=None,
        description="Created or reused meeting analysis ID",
    )
    error_stage: Optional[str] = Field(
        default=None,
        description="Stage name where failure occurred, if any",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Safe error description if workflow failed",
    )
    created_at: datetime = Field(description="UTC timestamp of workflow creation")
    started_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when processing began",
    )
    updated_at: datetime = Field(description="UTC timestamp of last status update")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when workflow completed or failed",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "670560a12f3e8b1d9c4e5a6c",
                "source_type": "transcription",
                "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "title": "Quarterly Executive Alignment",
                "current_stage": "finalized",
                "status": "completed",
                "analysis_id": "651a2b3c4d5e6f7a8b9c0d1f",
                "error_stage": None,
                "error_message": None,
                "created_at": "2026-10-09T14:40:00Z",
                "started_at": "2026-10-09T14:40:01Z",
                "updated_at": "2026-10-09T14:40:15Z",
                "completed_at": "2026-10-09T14:40:15Z",
            }
        },
    )


class WorkflowResultResponse(BaseModel):
    """Full consolidated end-to-end meeting workflow result."""

    id: str = Field(description="Unique workflow run ID")
    source_type: AnalysisSourceType = Field(description="Source content type")
    source_id: Optional[str] = Field(default=None, description="Referenced source record ID if any")
    title: Optional[str] = Field(default=None, description="Meeting title or subject")
    current_stage: WorkflowStage = Field(description="Finalized stage")
    status: WorkflowStatus = Field(description="Workflow execution status")
    analysis: Optional[AnalysisResponse] = Field(
        default=None,
        description="Consolidated meeting analysis intelligence report",
    )
    tasks: List[TaskResponse] = Field(
        default_factory=list,
        description="Extracted and persisted action items",
    )
    follow_up_plan: Optional[FollowUpPlanResponse] = Field(
        default=None,
        description="Structured follow-up action plan",
    )
    error_stage: Optional[str] = Field(default=None, description="Error stage if failed")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(description="UTC timestamp of workflow creation")
    started_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when processing began",
    )
    updated_at: datetime = Field(description="UTC timestamp of last status update")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when workflow completed or failed",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "670560a12f3e8b1d9c4e5a6c",
                "source_type": "transcription",
                "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "title": "Quarterly Executive Alignment",
                "current_stage": "finalized",
                "status": "completed",
                "analysis": None,
                "tasks": [],
                "follow_up_plan": None,
                "error_stage": None,
                "error_message": None,
                "created_at": "2026-10-09T14:40:00Z",
                "updated_at": "2026-10-09T14:40:15Z",
                "completed_at": "2026-10-09T14:40:15Z",
            }
        },
    )


class WorkflowListResponse(BaseModel):
    """Paginated collection of workflow run records."""

    items: List[WorkflowStatusResponse] = Field(
        default_factory=list,
        description="List of workflow runs for the current page",
    )
    total: int = Field(description="Total count of matching workflow records")
    page: int = Field(default=1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    total_pages: int = Field(default=1, description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
            }
        }
    )
