"""LangGraph Meeting Processing Pipeline API routes."""

import logging
import math
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pymongo.errors import PyMongoError
from app.repositories.analysis_repo import (
    AnalysisRepository,
    get_analysis_repository,
)
from app.repositories.task_repo import (
    TaskRepository,
    get_task_repository,
)
from app.repositories.workflow_repo import (
    WorkflowRepository,
    get_workflow_repository,
)
from app.schemas.analysis import AnalysisResponse, AnalysisSourceType
from app.schemas.task import FollowUpPlanResponse, TaskResponse
from app.schemas.workflow import (
    WorkflowListResponse,
    WorkflowResultResponse,
    WorkflowStartRequest,
    WorkflowStatus,
    WorkflowStatusResponse,
)
from app.services.task_service import (
    FollowUpPlanningService,
    get_follow_up_planning_service,
)
from app.workflows.workflow_engine import (
    WorkflowEngine,
    get_workflow_engine,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["workflows"])


@router.post(
    "/start",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start end-to-end meeting workflow",
    description=(
        "Initiate an asynchronous LangGraph meeting intelligence workflow covering source retrieval, "
        "meeting intelligence analysis, action item extraction, and follow-up planning."
    ),
)
def start_meeting_workflow(
    payload: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowStatusResponse:
    """Create a new workflow execution record and launch background processing."""
    # 1. Create initial workflow tracking record in MongoDB
    try:
        workflow_doc = workflow_repo.create({
            "source_type": payload.source_type.value,
            "source_id": payload.source_id,
            "title": payload.title,
            "status": WorkflowStatus.QUEUED.value,
            "current_stage": "queued",
            "force_reanalyze": payload.force_reanalyze,
        })
    except PyMongoError as e:
        logger.error("Failed to create workflow record: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Could not queue workflow.",
        )

    # 2. Dispatch background execution
    background_tasks.add_task(
        workflow_engine.execute_workflow,
        workflow_id=workflow_doc["id"],
        initial_input=payload.model_dump(),
    )

    return WorkflowStatusResponse(**workflow_doc)


@router.post(
    "/run-sync",
    response_model=WorkflowResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute meeting workflow synchronously",
    description="Execute the complete LangGraph pipeline synchronously and return the consolidated result in a single response.",
)
def run_meeting_workflow_sync(
    payload: WorkflowStartRequest,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
    planning_service: FollowUpPlanningService = Depends(get_follow_up_planning_service),
) -> WorkflowResultResponse:
    """Synchronously execute the full meeting workflow."""
    workflow_doc = workflow_repo.create({
        "source_type": payload.source_type.value,
        "source_id": payload.source_id,
        "title": payload.title,
        "status": WorkflowStatus.QUEUED.value,
        "current_stage": "queued",
        "force_reanalyze": payload.force_reanalyze,
    })

    final_state = workflow_engine.execute_workflow(
        workflow_id=workflow_doc["id"],
        initial_input=payload.model_dump(),
    )

    # Retrieve updated document
    updated_doc = workflow_repo.get_by_id(workflow_doc["id"]) or workflow_doc

    # Assemble full result
    analysis_resp: Optional[AnalysisResponse] = None
    tasks_resp = []
    follow_up_resp: Optional[FollowUpPlanResponse] = None

    analysis_id = updated_doc.get("analysis_id")
    if analysis_id:
        raw_analysis = analysis_repo.get_by_id(analysis_id)
        if raw_analysis:
            analysis_resp = AnalysisResponse(**raw_analysis)
        raw_tasks = task_repo.get_by_analysis_id(analysis_id)
        tasks_resp = [TaskResponse(**t) for t in raw_tasks]
        if raw_analysis:
            plan = planning_service.generate_plan(
                analysis_id=analysis_id,
                tasks=raw_tasks,
                analysis_record=raw_analysis,
            )
            follow_up_resp = plan

    return WorkflowResultResponse(
        id=updated_doc["id"],
        source_type=updated_doc["source_type"],
        source_id=updated_doc.get("source_id"),
        title=updated_doc.get("title"),
        current_stage=updated_doc["current_stage"],
        status=updated_doc["status"],
        analysis=analysis_resp,
        tasks=tasks_resp,
        follow_up_plan=follow_up_resp,
        error_stage=updated_doc.get("error_stage"),
        error_message=updated_doc.get("error_message"),
        created_at=updated_doc["created_at"],
        updated_at=updated_doc["updated_at"],
        completed_at=updated_doc.get("completed_at"),
    )


@router.get(
    "/",
    response_model=WorkflowListResponse,
    summary="List workflow runs",
    description="Retrieve a paginated list of workflow runs with optional filters by status or source type.",
)
def list_workflows(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: Optional[WorkflowStatus] = Query(default=None, description="Filter by status"),
    source_type: Optional[AnalysisSourceType] = Query(default=None, description="Filter by source type"),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowListResponse:
    """List paginated workflow execution runs."""
    skip = (page - 1) * page_size
    items_raw, total = workflow_repo.list_workflows(
        skip=skip,
        limit=page_size,
        status=status.value if status else None,
        source_type=source_type.value if source_type else None,
    )

    items = [WorkflowStatusResponse(**item) for item in items_raw]
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return WorkflowListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowStatusResponse,
    summary="Get workflow status and progress",
    description="Poll current execution progress, status, and diagnostic error states of a workflow run.",
)
def get_workflow_status(
    workflow_id: str,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowStatusResponse:
    """Retrieve status details for a workflow ID."""
    doc = workflow_repo.get_by_id(workflow_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{workflow_id}' was not found.",
        )
    return WorkflowStatusResponse(**doc)


@router.get(
    "/{workflow_id}/result",
    response_model=WorkflowResultResponse,
    summary="Get consolidated workflow result",
    description="Retrieve the complete end-to-end result (analysis, extracted tasks, and follow-up plan) for a completed workflow run.",
)
def get_workflow_result(
    workflow_id: str,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
    planning_service: FollowUpPlanningService = Depends(get_follow_up_planning_service),
) -> WorkflowResultResponse:
    """Retrieve consolidated result for a completed workflow run."""
    doc = workflow_repo.get_by_id(workflow_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{workflow_id}' was not found.",
        )

    analysis_resp: Optional[AnalysisResponse] = None
    tasks_resp = []
    follow_up_resp: Optional[FollowUpPlanResponse] = None

    analysis_id = doc.get("analysis_id")
    if analysis_id:
        raw_analysis = analysis_repo.get_by_id(analysis_id)
        if raw_analysis:
            analysis_resp = AnalysisResponse(**raw_analysis)
        raw_tasks = task_repo.get_by_analysis_id(analysis_id)
        tasks_resp = [TaskResponse(**t) for t in raw_tasks]
        if raw_analysis:
            plan = planning_service.generate_plan(
                analysis_id=analysis_id,
                tasks=raw_tasks,
                analysis_record=raw_analysis,
            )
            follow_up_resp = plan

    return WorkflowResultResponse(
        id=doc["id"],
        source_type=doc["source_type"],
        source_id=doc.get("source_id"),
        title=doc.get("title"),
        current_stage=doc["current_stage"],
        status=doc["status"],
        analysis=analysis_resp,
        tasks=tasks_resp,
        follow_up_plan=follow_up_resp,
        error_stage=doc.get("error_stage"),
        error_message=doc.get("error_message"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        completed_at=doc.get("completed_at"),
    )


@router.post(
    "/{workflow_id}/retry",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry a failed workflow run",
    description="Safely restart a failed workflow run from the beginning.",
)
def retry_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowStatusResponse:
    """Retry a failed workflow run."""
    doc = workflow_repo.get_by_id(workflow_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{workflow_id}' was not found.",
        )

    if doc.get("status") == WorkflowStatus.PROCESSING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retry a workflow run that is currently processing.",
        )

    # Reset status
    updated_doc = workflow_repo.update_stage_and_status(
        workflow_id=workflow_id,
        stage="queued",
        status=WorkflowStatus.QUEUED.value,
        error_stage=None,
        error_message=None,
        completed_at=None,
    )

    initial_input = {
        "source_type": doc["source_type"],
        "source_id": doc.get("source_id"),
        "title": doc.get("title"),
        "force_reanalyze": doc.get("force_reanalyze", False),
    }

    background_tasks.add_task(
        workflow_engine.execute_workflow,
        workflow_id=workflow_id,
        initial_input=initial_input,
    )

    return WorkflowStatusResponse(**(updated_doc or doc))


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workflow run record",
    description="Remove a workflow execution record from the database.",
)
def delete_workflow(
    workflow_id: str,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> None:
    """Delete a workflow record by ID."""
    deleted = workflow_repo.delete(workflow_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{workflow_id}' was not found.",
        )
    return None
