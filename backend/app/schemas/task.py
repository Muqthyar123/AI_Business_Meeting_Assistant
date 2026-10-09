"""Pydantic schemas for Action-Item Extraction, Persistent Task Management, and Follow-up Planning."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TaskPriority(str, Enum):
    """Priority level for meeting action items."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class TaskStatus(str, Enum):
    """Execution status for meeting action items."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskExportFormat(str, Enum):
    """Supported export formats for action items and follow-up plans."""

    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class ExtractedTaskItem(BaseModel):
    """Raw action item extracted directly by the LLM from meeting notes or transcripts."""

    description: str = Field(
        description="Clear, actionable task description beginning with an action verb",
        min_length=1,
    )
    assignee: Optional[str] = Field(
        default=None,
        description="Explicitly named individual or role responsible for the task",
    )
    has_missing_assignee: bool = Field(
        default=False,
        description="True if no explicit owner was identified in the meeting content",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Explicit deadline or timeframe stated in the meeting notes",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.UNKNOWN,
        description="Task priority based strictly on urgency/importance stated in meeting",
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Prerequisite tasks, blockers, or dependencies explicitly mentioned",
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        description="Direct quote or excerpt from the meeting text justifying the action item",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Deploy MongoDB Atlas production cluster configuration",
                "assignee": "Sarah Chen",
                "has_missing_assignee": False,
                "due_date": "by Friday 5 PM",
                "priority": "high",
                "dependencies": ["Finalize network subnet allocation"],
                "evidence_excerpt": "Sarah agreed to deploy the Atlas cluster by Friday 5 PM once network subnets are allocated.",
            }
        }
    )


class ActionItemExtractionResult(BaseModel):
    """Validated structured intelligence output containing all extracted meeting action items."""

    tasks: List[ExtractedTaskItem] = Field(
        default_factory=list,
        description="List of action items extracted from the meeting content",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tasks": [
                    {
                        "description": "Send updated budget spreadsheet to executive committee",
                        "assignee": "Alex Rivera",
                        "has_missing_assignee": False,
                        "due_date": "by Oct 15",
                        "priority": "medium",
                        "dependencies": [],
                        "evidence_excerpt": "Alex will circulate the updated budget by October 15th.",
                    }
                ]
            }
        }
    )


class TaskCreateRequest(BaseModel):
    """Request payload for manually creating an action item."""

    analysis_id: str = Field(
        description="Associated meeting analysis ID",
    )
    description: str = Field(
        min_length=1,
        max_length=1000,
        description="Clear, actionable task description",
    )
    assignee: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Assignee name or role",
    )
    has_missing_assignee: bool = Field(
        default=False,
        description="Flag indicating if the task still requires an owner assignment",
    )
    due_date: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Target deadline or timeframe",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.UNKNOWN,
        description="Task priority level",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Initial lifecycle status",
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of prerequisite task descriptions or blockers",
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Source excerpt or context for the task",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "description": "Review API security audit findings with lead architect",
                "assignee": "Devon Vance",
                "has_missing_assignee": False,
                "due_date": "2026-10-20",
                "priority": "high",
                "status": "pending",
                "dependencies": ["Security audit report publication"],
                "evidence_excerpt": "Devon to review audit findings as soon as the report is published.",
            }
        }
    )


class TaskUpdateRequest(BaseModel):
    """Request payload for updating editable action item fields."""

    description: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Updated task description",
    )
    assignee: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Updated assignee name or role",
    )
    has_missing_assignee: Optional[bool] = Field(
        default=None,
        description="Updated missing assignee status flag",
    )
    due_date: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Updated deadline or timeframe",
    )
    priority: Optional[TaskPriority] = Field(
        default=None,
        description="Updated priority level",
    )
    status: Optional[TaskStatus] = Field(
        default=None,
        description="Updated task status",
    )
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="Updated list of dependencies",
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Updated supporting excerpt",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "assignee": "Jordan Miller",
                "has_missing_assignee": False,
                "due_date": "2026-10-25",
                "status": "in_progress",
            }
        }
    )


class TaskStatusUpdateRequest(BaseModel):
    """Request payload for updating only the execution status of a task."""

    status: TaskStatus = Field(
        description="New lifecycle status for the task",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "completed",
            }
        }
    )


class TaskResponse(BaseModel):
    """Full persisted action item record schema."""

    id: str = Field(description="Unique task identifier (hex string)")
    analysis_id: str = Field(description="Associated meeting analysis ID")
    description: str = Field(description="Actionable task description")
    assignee: Optional[str] = Field(default=None, description="Assigned owner or role")
    has_missing_assignee: bool = Field(
        default=False,
        description="True if task lacks an assigned owner",
    )
    due_date: Optional[str] = Field(default=None, description="Explicit deadline or timeframe")
    priority: TaskPriority = Field(
        default=TaskPriority.UNKNOWN,
        description="Task priority",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current execution status",
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of prerequisite dependencies",
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        description="Source excerpt justifying the task",
    )
    created_at: datetime = Field(description="UTC timestamp of task creation")
    updated_at: datetime = Field(description="UTC timestamp of last update")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "670560a12f3e8b1d9c4e5a6b",
                "analysis_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "description": "Deploy MongoDB Atlas production cluster configuration",
                "assignee": "Sarah Chen",
                "has_missing_assignee": False,
                "due_date": "by Friday 5 PM",
                "priority": "high",
                "status": "pending",
                "dependencies": ["Finalize network subnet allocation"],
                "evidence_excerpt": "Sarah agreed to deploy the Atlas cluster by Friday 5 PM once network subnets are allocated.",
                "created_at": "2026-10-09T14:40:00Z",
                "updated_at": "2026-10-09T14:40:00Z",
            }
        },
    )


class TaskListResponse(BaseModel):
    """Paginated collection of action items."""

    items: List[TaskResponse] = Field(
        default_factory=list,
        description="List of action items for the current page",
    )
    total: int = Field(description="Total count of matching tasks")
    page: int = Field(default=1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=200, description="Items per page")
    total_pages: int = Field(default=1, description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 50,
                "total_pages": 0,
            }
        }
    )


class FollowUpPlanResponse(BaseModel):
    """Categorized follow-up plan consolidating meeting commitments, blockers, and recommendations."""

    analysis_id: str = Field(description="Associated meeting analysis ID")
    immediate_actions: List[TaskResponse] = Field(
        default_factory=list,
        description="High-priority or urgent action items requiring immediate execution",
    )
    upcoming_tasks: List[TaskResponse] = Field(
        default_factory=list,
        description="Tasks with explicit deadlines scheduled for future delivery",
    )
    clarification_needed: List[TaskResponse] = Field(
        default_factory=list,
        description="Action items requiring owner assignment or deadline clarification",
    )
    blockers_and_dependencies: List[TaskResponse] = Field(
        default_factory=list,
        description="Tasks currently blocked or dependent on prerequisite outcomes",
    )
    pending_decisions: List[str] = Field(
        default_factory=list,
        description="Unresolved questions, risks, or tentative decisions requiring stakeholder follow-up",
    )
    ai_suggestions: List[str] = Field(
        default_factory=list,
        description="Contextual AI recommendations to unblock progress and drive execution",
    )
    total_tasks: int = Field(
        default=0,
        description="Total number of active action items in this follow-up plan",
    )
    generated_at: datetime = Field(
        description="UTC timestamp when the follow-up plan was generated",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "immediate_actions": [],
                "upcoming_tasks": [],
                "clarification_needed": [],
                "blockers_and_dependencies": [],
                "pending_decisions": ["Confirm staging cutover date"],
                "ai_suggestions": ["Assign an owner to the 2 unassigned tasks."],
                "total_tasks": 0,
                "generated_at": "2026-10-09T14:40:00Z",
            }
        }
    )
