"""Action items, persistent task management, and follow-up planning API routes."""

import logging
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.errors import PyMongoError
from app.repositories.analysis_repo import (
    AnalysisRepository,
    get_analysis_repository,
)
from app.repositories.document_repo import (
    DocumentRepository,
    get_document_repository,
)
from app.repositories.task_repo import (
    TaskRepository,
    get_task_repository,
)
from app.repositories.transcription_repo import (
    TranscriptionRepository,
    get_transcription_repository,
)
from app.schemas.task import (
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
from app.services.export_service import (
    TaskExportService,
    get_task_export_service,
)
from app.services.llm_service import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMOutputParsingError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.task_service import (
    ActionItemExtractionService,
    FollowUpPlanningService,
    get_action_item_extraction_service,
    get_follow_up_planning_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tasks"])


@router.post(
    "/extract/{analysis_id}",
    response_model=List[TaskResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Extract action items from meeting analysis",
    description=(
        "Analyze meeting content using LLM to extract actionable commitments, assignees, "
        "deadlines, priorities, and evidence excerpts. Automatically replaces previously extracted tasks if replace=True."
    ),
)
def extract_action_items_from_analysis(
    analysis_id: str,
    replace: bool = Query(
        default=True,
        description="If True, removes previously extracted tasks for this analysis to prevent duplication",
    ),
    task_service: ActionItemExtractionService = Depends(get_action_item_extraction_service),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
    transcription_repo: TranscriptionRepository = Depends(get_transcription_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> List[TaskResponse]:
    """Extract structured action items from the parent meeting source or analysis record."""
    # 1. Locate parent analysis
    analysis_doc = analysis_repo.get_by_id(analysis_id)
    if analysis_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting analysis record '{analysis_id}' was not found.",
        )

    # 2. Reconstruct original source text or synthesized text
    source_type = analysis_doc.get("source_type")
    source_id = analysis_doc.get("source_id")
    meeting_text = ""

    if source_type == "transcription" and source_id:
        trans_rec = transcription_repo.get_by_id(source_id)
        if trans_rec and trans_rec.get("transcript_text"):
            meeting_text = trans_rec["transcript_text"]
    elif source_type == "document" and source_id:
        doc_rec = document_repo.get_by_id(source_id)
        if doc_rec and doc_rec.get("text_content"):
            meeting_text = doc_rec["text_content"]

    if not meeting_text or not meeting_text.strip():
        # Fallback to analysis content if source text not found or direct text
        summary = analysis_doc.get("executive_summary", "")
        points = "\n".join(f"- {p}" for p in analysis_doc.get("key_discussion_points", []))
        decisions = "\n".join(f"- {d}" for d in analysis_doc.get("decisions_made", []))
        risks = "\n".join(f"- {r}" for r in analysis_doc.get("risks_and_blockers", []))
        questions = "\n".join(f"- {q}" for q in analysis_doc.get("unresolved_questions", []))

        meeting_text = (
            f"Executive Summary:\n{summary}\n\n"
            f"Discussion Points:\n{points}\n\n"
            f"Decisions Made:\n{decisions}\n\n"
            f"Risks and Blockers:\n{risks}\n\n"
            f"Unresolved Questions:\n{questions}"
        )

    # 3. Call LLM Action Item Extraction
    try:
        extraction_result = task_service.extract_action_items(meeting_text=meeting_text)
    except LLMConfigurationError as e:
        logger.error("LLM configuration error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except LLMAuthenticationError as e:
        logger.error("LLM authentication error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except LLMRateLimitError as e:
        logger.warning("LLM rate limit: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except LLMTimeoutError as e:
        logger.error("LLM timeout: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e),
        )
    except LLMOutputParsingError as e:
        logger.error("LLM output parsing error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except (LLMProviderError, ValueError) as e:
        logger.error("Action item extraction error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Action item extraction failed: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error during action item extraction: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during action item extraction.",
        )

    # 4. Save extracted tasks into MongoDB
    try:
        raw_task_dicts = [task.model_dump() for task in extraction_result.tasks]
        persisted_records = task_repo.create_many_for_analysis(
            analysis_id=analysis_id,
            tasks_data=raw_task_dicts,
            replace=replace,
        )
    except PyMongoError as e:
        logger.error("Database persistence failure for tasks: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable. Could not persist action items.",
        )

    return [TaskResponse(**doc) for doc in persisted_records]


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create action item manually",
    description="Manually create a new action item associated with an existing meeting analysis.",
)
def create_task(
    payload: TaskCreateRequest,
    analysis_repo: AnalysisRepository = Depends(get_analysis_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskResponse:
    """Manually add an action item."""
    parent = analysis_repo.get_by_id(payload.analysis_id)
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting analysis '{payload.analysis_id}' was not found.",
        )

    try:
        doc = task_repo.create(payload.model_dump())
    except PyMongoError as e:
        logger.error("Database error while creating task: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable.",
        )

    return TaskResponse(**doc)


@router.get(
    "/",
    response_model=TaskListResponse,
    summary="List action items",
    description="Retrieve a paginated list of action items with optional filters by analysis ID, status, priority, or assignee.",
)
def list_tasks(
    analysis_id: Optional[str] = Query(default=None, description="Filter by parent analysis ID"),
    status: Optional[TaskStatus] = Query(default=None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(default=None, description="Filter by priority"),
    assignee: Optional[str] = Query(default=None, description="Filter by assignee name"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskListResponse:
    """Fetch paginated action items with filtering."""
    skip = (page - 1) * page_size
    items_raw, total = task_repo.list_tasks(
        skip=skip,
        limit=page_size,
        analysis_id=analysis_id,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        assignee=assignee,
    )

    items = [TaskResponse(**item) for item in items_raw]
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/export",
    summary="Export action items and follow-up plan",
    description="Export meeting tasks in JSON, CSV, or Markdown format with proper MIME types and download headers.",
)
def export_tasks(
    format: TaskExportFormat = Query(
        default=TaskExportFormat.JSON,
        description="Target export format ('json', 'csv', 'markdown')",
    ),
    analysis_id: Optional[str] = Query(
        default=None,
        description="Optional filter by analysis ID for scoped export",
    ),
    export_service: TaskExportService = Depends(get_task_export_service),
    planning_service: FollowUpPlanningService = Depends(get_follow_up_planning_service),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> Response:
    """Export action items into downloadable JSON, CSV, or Markdown format."""
    analysis_doc: Optional[dict] = None
    plan_dict: Optional[dict] = None

    if analysis_id:
        analysis_doc = analysis_repo.get_by_id(analysis_id)
        if analysis_doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meeting analysis '{analysis_id}' was not found.",
            )
        tasks = task_repo.get_by_analysis_id(analysis_id)
        plan_resp = planning_service.generate_plan(
            analysis_id=analysis_id,
            tasks=tasks,
            analysis_record=analysis_doc,
        )
        plan_dict = plan_resp.model_dump()
    else:
        tasks, _ = task_repo.list_tasks(limit=1000)

    if format == TaskExportFormat.CSV:
        content = export_service.export_to_csv(tasks=tasks)
        media_type = "text/csv; charset=utf-8"
        filename = f"tasks_{analysis_id or 'all'}.csv"
    elif format == TaskExportFormat.MARKDOWN:
        content = export_service.export_to_markdown(
            tasks=tasks,
            plan=plan_dict,
            analysis_meta=analysis_doc,
        )
        media_type = "text/markdown; charset=utf-8"
        filename = f"tasks_plan_{analysis_id or 'all'}.md"
    else:  # JSON
        content = export_service.export_to_json(
            tasks=tasks,
            plan=plan_dict,
            analysis_meta=analysis_doc,
        )
        media_type = "application/json; charset=utf-8"
        filename = f"tasks_{analysis_id or 'all'}.json"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return Response(
        content=content,
        media_type=media_type,
        headers=headers,
    )


@router.get(
    "/analysis/{analysis_id}/plan",
    response_model=FollowUpPlanResponse,
    summary="Get follow-up plan for meeting",
    description="Generate a categorized follow-up plan with immediate actions, upcoming deadlines, blockers, pending decisions, and AI suggestions.",
)
def get_follow_up_plan(
    analysis_id: str,
    planning_service: FollowUpPlanningService = Depends(get_follow_up_planning_service),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> FollowUpPlanResponse:
    """Generate structured follow-up plan for a meeting analysis."""
    analysis_doc = analysis_repo.get_by_id(analysis_id)
    if analysis_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting analysis '{analysis_id}' was not found.",
        )

    tasks = task_repo.get_by_analysis_id(analysis_id)
    return planning_service.generate_plan(
        analysis_id=analysis_id,
        tasks=tasks,
        analysis_record=analysis_doc,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get action item details",
    description="Retrieve details of a single action item by its ID.",
)
def get_task(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskResponse:
    """Fetch a single task record by ID."""
    doc = task_repo.get_by_id(task_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item '{task_id}' was not found.",
        )
    return TaskResponse(**doc)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update action item",
    description="Update fields of an existing action item (description, assignee, due date, priority, status, dependencies).",
)
def update_task(
    task_id: str,
    payload: TaskUpdateRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskResponse:
    """Update fields of an action item."""
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        doc = task_repo.get_by_id(task_id)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action item '{task_id}' was not found.",
            )
        return TaskResponse(**doc)

    # Convert Enums to string values for database storage
    if "status" in update_data and isinstance(update_data["status"], TaskStatus):
        update_data["status"] = update_data["status"].value
    if "priority" in update_data and isinstance(update_data["priority"], TaskPriority):
        update_data["priority"] = update_data["priority"].value

    # Auto-adjust has_missing_assignee if assignee is modified without explicit flag
    if "assignee" in update_data and "has_missing_assignee" not in update_data:
        update_data["has_missing_assignee"] = update_data["assignee"] is None

    doc = task_repo.update(task_id, update_data)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item '{task_id}' was not found.",
        )
    return TaskResponse(**doc)


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Update action item status",
    description="Quickly update the execution status of an action item ('pending', 'in_progress', 'completed', 'cancelled').",
)
def update_task_status(
    task_id: str,
    payload: TaskStatusUpdateRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskResponse:
    """Update only the status of an action item."""
    doc = task_repo.update_status(task_id, payload.status.value)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item '{task_id}' was not found.",
        )
    return TaskResponse(**doc)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete action item",
    description="Remove an action item from the database.",
)
def delete_task(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> None:
    """Delete a task by ID."""
    deleted = task_repo.delete(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item '{task_id}' was not found.",
        )
    return None
