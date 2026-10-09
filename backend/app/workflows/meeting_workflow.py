"""LangGraph Meeting Processing Pipeline orchestration graph and state definition."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import END, StateGraph
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
from app.repositories.workflow_repo import (
    WorkflowRepository,
    get_workflow_repository,
)
from app.schemas.analysis import AnalysisStatus
from app.schemas.transcription import TranscriptionStatus
from app.services.llm_service import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMOutputParsingError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.meeting_analysis_service import (
    MeetingAnalysisService,
    get_meeting_analysis_service,
)
from app.services.task_service import (
    ActionItemExtractionService,
    FollowUpPlanningService,
    get_action_item_extraction_service,
    get_follow_up_planning_service,
)

logger = logging.getLogger(__name__)


class MeetingWorkflowState(TypedDict, total=False):
    """TypedDict state container passed through the LangGraph meeting pipeline."""

    workflow_run_id: str
    source_type: str
    source_id: Optional[str]
    title: Optional[str]
    text: Optional[str]
    force_reanalyze: bool

    # Retrieved content
    retrieved_text: Optional[str]
    source_metadata: Dict[str, Any]

    # Analysis outputs
    existing_analysis_id: Optional[str]
    analysis_record: Optional[Dict[str, Any]]

    # Task extraction outputs
    extracted_tasks: List[Dict[str, Any]]
    persisted_tasks: List[Dict[str, Any]]

    # Follow-up plan outputs
    follow_up_plan: Optional[Dict[str, Any]]

    # Workflow tracking metadata
    current_stage: str
    status: str
    error_stage: Optional[str]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    updated_at: str
    completed_at: Optional[str]


def _update_workflow_db_stage(
    workflow_id: Optional[str],
    stage: str,
    status: Optional[str] = None,
    analysis_id: Optional[str] = None,
    error_stage: Optional[str] = None,
    error_message: Optional[str] = None,
    completed_at: Optional[datetime] = None,
) -> None:
    """Safely record real-time workflow stage progress to the database repository."""
    if not workflow_id:
        return
    try:
        repo = get_workflow_repository()
        repo.update_stage_and_status(
            workflow_id=workflow_id,
            stage=stage,
            status=status,
            analysis_id=analysis_id,
            error_stage=error_stage,
            error_message=error_message,
            completed_at=completed_at,
        )
    except Exception as e:
        logger.debug("Non-fatal: could not update stage '%s' in db for workflow '%s': %s", stage, workflow_id, str(e))


def validate_input_node(state: MeetingWorkflowState) -> Dict[str, Any]:
    """Node A: Validate input parameters, source type, and presence of required fields."""
    workflow_id = state.get("workflow_run_id")
    source_type = state.get("source_type")
    source_id = state.get("source_id")
    text = state.get("text")

    allowed_types = ["transcription", "document", "direct_text", "pasted_text"]
    if source_type not in allowed_types:
        err = f"Unsupported source type '{source_type}'. Allowed types: {', '.join(allowed_types)}."
        _update_workflow_db_stage(workflow_id, stage="input_validation", status="failed", error_stage="input_validation", error_message=err)
        return {
            "status": "failed",
            "current_stage": "input_validation",
            "error_stage": "input_validation",
            "error_message": err,
        }

    if source_type in ["transcription", "document"] and not source_id:
        err = f"source_id is required when source_type is '{source_type}'."
        _update_workflow_db_stage(workflow_id, stage="input_validation", status="failed", error_stage="input_validation", error_message=err)
        return {
            "status": "failed",
            "current_stage": "input_validation",
            "error_stage": "input_validation",
            "error_message": err,
        }

    if source_type in ["direct_text", "pasted_text"] and (not text or not text.strip()):
        err = "Meeting text is required when source_type is direct or pasted text."
        _update_workflow_db_stage(workflow_id, stage="input_validation", status="failed", error_stage="input_validation", error_message=err)
        return {
            "status": "failed",
            "current_stage": "input_validation",
            "error_stage": "input_validation",
            "error_message": err,
        }

    _update_workflow_db_stage(workflow_id, stage="source_retrieval", status="processing")
    return {
        "current_stage": "source_retrieval",
        "error_stage": None,
        "error_message": None,
    }


def retrieve_source_node(state: MeetingWorkflowState) -> Dict[str, Any]:
    """Node B: Retrieve meeting transcript or document content from repositories."""
    workflow_id = state.get("workflow_run_id")
    source_type = state.get("source_type")
    source_id = state.get("source_id")
    text = state.get("text")
    title = state.get("title")

    if source_type == "transcription":
        trans_repo = get_transcription_repository()
        record = trans_repo.get_by_id(str(source_id))
        if record is None:
            err = f"Transcription record '{source_id}' was not found."
            _update_workflow_db_stage(workflow_id, stage="source_retrieval", status="failed", error_stage="source_retrieval", error_message=err)
            return {
                "status": "failed",
                "current_stage": "source_retrieval",
                "error_stage": "source_retrieval",
                "error_message": err,
            }

        rec_status = record.get("status")
        if rec_status != TranscriptionStatus.COMPLETED.value:
            err = f"Transcription is '{rec_status}'. Must be completed before running workflow."
            _update_workflow_db_stage(workflow_id, stage="source_retrieval", status="failed", error_stage="source_retrieval", error_message=err)
            return {
                "status": "failed",
                "current_stage": "source_retrieval",
                "error_stage": "source_retrieval",
                "error_message": err,
            }

        transcript = record.get("transcript_text")
        if not transcript or not transcript.strip():
            err = f"Transcription record '{source_id}' contains no transcript text."
            _update_workflow_db_stage(workflow_id, stage="source_retrieval", status="failed", error_stage="source_retrieval", error_message=err)
            return {
                "status": "failed",
                "current_stage": "source_retrieval",
                "error_stage": "source_retrieval",
                "error_message": err,
            }

        resolved_title = title or record.get("original_filename") or "Meeting Transcription"
        _update_workflow_db_stage(workflow_id, stage="meeting_analysis", status="processing")
        return {
            "retrieved_text": transcript,
            "title": resolved_title,
            "source_metadata": {
                "whisper_model": record.get("whisper_model"),
                "detected_language": record.get("detected_language"),
                "audio_duration": record.get("audio_duration"),
            },
            "current_stage": "meeting_analysis",
        }

    elif source_type == "document":
        doc_repo = get_document_repository()
        doc = doc_repo.get_by_id(str(source_id))
        if doc is None:
            err = f"Document record '{source_id}' was not found."
            _update_workflow_db_stage(workflow_id, stage="source_retrieval", status="failed", error_stage="source_retrieval", error_message=err)
            return {
                "status": "failed",
                "current_stage": "source_retrieval",
                "error_stage": "source_retrieval",
                "error_message": err,
            }

        content = doc.get("text_content")
        if not content or not content.strip():
            err = f"Document record '{source_id}' contains no extractable text."
            _update_workflow_db_stage(workflow_id, stage="source_retrieval", status="failed", error_stage="source_retrieval", error_message=err)
            return {
                "status": "failed",
                "current_stage": "source_retrieval",
                "error_stage": "source_retrieval",
                "error_message": err,
            }

        resolved_title = title or doc.get("title") or doc.get("original_filename") or "Meeting Document"
        _update_workflow_db_stage(workflow_id, stage="meeting_analysis", status="processing")
        return {
            "retrieved_text": content,
            "title": resolved_title,
            "source_metadata": {
                "file_type": doc.get("file_type"),
                "word_count": doc.get("word_count"),
            },
            "current_stage": "meeting_analysis",
        }

    else:  # direct_text or pasted_text
        resolved_title = title or "Direct Meeting Notes"
        _update_workflow_db_stage(workflow_id, stage="meeting_analysis", status="processing")
        return {
            "retrieved_text": str(text).strip(),
            "title": resolved_title,
            "source_metadata": {
                "direct_char_count": len(str(text).strip()),
            },
            "current_stage": "meeting_analysis",
        }


def meeting_analysis_node(state: MeetingWorkflowState) -> Dict[str, Any]:
    """Node C: Generate new meeting intelligence or reuse existing cached analysis."""
    workflow_id = state.get("workflow_run_id")
    force_reanalyze = state.get("force_reanalyze", False)
    existing_analysis_id = state.get("existing_analysis_id")
    source_id = state.get("source_id")
    analysis_repo = get_analysis_repository()

    # Check for reusable analysis if not forcing reanalysis
    if not force_reanalyze:
        if existing_analysis_id:
            existing = analysis_repo.get_by_id(existing_analysis_id)
            if existing:
                logger.info("Workflow reusing existing analysis by ID '%s'", existing_analysis_id)
                _update_workflow_db_stage(workflow_id, stage="action_item_extraction", status="processing", analysis_id=existing.get("id"))
                return {
                    "analysis_record": existing,
                    "current_stage": "action_item_extraction",
                }

        if source_id:
            existing_by_src = analysis_repo.get_by_source_id(str(source_id))
            if existing_by_src:
                logger.info("Workflow reusing existing analysis for source_id '%s'", source_id)
                _update_workflow_db_stage(workflow_id, stage="action_item_extraction", status="processing", analysis_id=existing_by_src.get("id"))
                return {
                    "analysis_record": existing_by_src,
                    "current_stage": "action_item_extraction",
                }

    # Generate fresh meeting intelligence
    analysis_service = get_meeting_analysis_service()
    retrieved_text = state.get("retrieved_text", "")

    try:
        analysis_result = analysis_service.analyze_meeting(text=retrieved_text)
    except (LLMConfigurationError, LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError, LLMOutputParsingError, LLMProviderError, ValueError) as e:
        logger.error("Meeting analysis failed in workflow: %s", str(e))
        err = f"Meeting analysis generation failed: {str(e)}"
        _update_workflow_db_stage(workflow_id, stage="meeting_analysis", status="failed", error_stage="meeting_analysis", error_message=err)
        return {
            "status": "failed",
            "current_stage": "meeting_analysis",
            "error_stage": "meeting_analysis",
            "error_message": err,
        }
    except Exception as e:
        logger.error("Unexpected error in workflow meeting analysis: %s", str(e))
        err = "An unexpected error occurred during meeting analysis."
        _update_workflow_db_stage(workflow_id, stage="meeting_analysis", status="failed", error_stage="meeting_analysis", error_message=err)
        return {
            "status": "failed",
            "current_stage": "meeting_analysis",
            "error_stage": "meeting_analysis",
            "error_message": err,
        }

    # Persist analysis
    try:
        provider = analysis_service.provider
        record = analysis_repo.create({
            "source_id": state.get("source_id"),
            "source_type": state.get("source_type"),
            "title": state.get("title"),
            "executive_summary": analysis_result.executive_summary,
            "meeting_purpose": analysis_result.meeting_purpose,
            "key_discussion_points": analysis_result.key_discussion_points,
            "decisions_made": analysis_result.decisions_made,
            "risks_and_blockers": analysis_result.risks_and_blockers,
            "unresolved_questions": analysis_result.unresolved_questions,
            "topics_and_themes": analysis_result.topics_and_themes,
            "llm_provider": provider.provider_name,
            "llm_model": provider.model_name,
            "status": AnalysisStatus.COMPLETED.value,
            "error_message": None,
        })
        analysis_id = record.get("id")
        _update_workflow_db_stage(workflow_id, stage="action_item_extraction", status="processing", analysis_id=analysis_id)
        return {
            "analysis_record": record,
            "current_stage": "action_item_extraction",
        }
    except Exception as e:
        logger.error("Failed to persist analysis record in workflow: %s", str(e))
        err = f"Database failure persisting analysis: {str(e)}"
        _update_workflow_db_stage(workflow_id, stage="meeting_analysis", status="failed", error_stage="meeting_analysis", error_message=err)
        return {
            "status": "failed",
            "current_stage": "meeting_analysis",
            "error_stage": "meeting_analysis",
            "error_message": err,
        }


def action_item_extraction_node(state: MeetingWorkflowState) -> Dict[str, Any]:
    """Node D: Extract and persist structured action items from meeting content."""
    workflow_id = state.get("workflow_run_id")
    analysis_record = state.get("analysis_record")
    if not analysis_record or not analysis_record.get("id"):
        err = "Cannot extract action items without a valid parent analysis record."
        _update_workflow_db_stage(workflow_id, stage="action_item_extraction", status="failed", error_stage="action_item_extraction", error_message=err)
        return {
            "status": "failed",
            "current_stage": "action_item_extraction",
            "error_stage": "action_item_extraction",
            "error_message": err,
        }

    analysis_id = analysis_record["id"]
    task_repo = get_task_repository()
    force_reanalyze = state.get("force_reanalyze", False)

    # If reusing existing analysis and tasks already exist, reuse them
    if not force_reanalyze:
        existing_tasks = task_repo.get_by_analysis_id(analysis_id)
        if existing_tasks:
            logger.info("Workflow reusing %d existing tasks for analysis '%s'", len(existing_tasks), analysis_id)
            _update_workflow_db_stage(workflow_id, stage="follow_up_planning", status="processing", analysis_id=analysis_id)
            return {
                "persisted_tasks": existing_tasks,
                "current_stage": "follow_up_planning",
            }

    # Extract action items
    task_service = get_action_item_extraction_service()
    meeting_text = state.get("retrieved_text", "")

    try:
        extraction_result = task_service.extract_action_items(meeting_text=meeting_text)
    except (LLMConfigurationError, LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError, LLMOutputParsingError, LLMProviderError, ValueError) as e:
        logger.error("Action item extraction failed in workflow: %s", str(e))
        err = f"Action item extraction failed: {str(e)}"
        _update_workflow_db_stage(workflow_id, stage="action_item_extraction", status="failed", error_stage="action_item_extraction", error_message=err, analysis_id=analysis_id)
        return {
            "status": "failed",
            "current_stage": "action_item_extraction",
            "error_stage": "action_item_extraction",
            "error_message": err,
        }
    except Exception as e:
        logger.error("Unexpected error in workflow action item extraction: %s", str(e))
        err = "An unexpected error occurred during action item extraction."
        _update_workflow_db_stage(workflow_id, stage="action_item_extraction", status="failed", error_stage="action_item_extraction", error_message=err, analysis_id=analysis_id)
        return {
            "status": "failed",
            "current_stage": "action_item_extraction",
            "error_stage": "action_item_extraction",
            "error_message": err,
        }

    # Persist tasks with atomic replacement for regeneration
    try:
        raw_task_dicts = [t.model_dump() for t in extraction_result.tasks]
        persisted_tasks = task_repo.create_many_for_analysis(
            analysis_id=analysis_id,
            tasks_data=raw_task_dicts,
            replace=True,
        )
        _update_workflow_db_stage(workflow_id, stage="follow_up_planning", status="processing", analysis_id=analysis_id)
        return {
            "extracted_tasks": raw_task_dicts,
            "persisted_tasks": persisted_tasks,
            "current_stage": "follow_up_planning",
        }
    except Exception as e:
        logger.error("Failed to persist tasks in workflow: %s", str(e))
        err = f"Database failure persisting action items: {str(e)}"
        _update_workflow_db_stage(workflow_id, stage="action_item_extraction", status="failed", error_stage="action_item_extraction", error_message=err, analysis_id=analysis_id)
        return {
            "status": "failed",
            "current_stage": "action_item_extraction",
            "error_stage": "action_item_extraction",
            "error_message": err,
        }


def follow_up_planning_node(state: MeetingWorkflowState) -> Dict[str, Any]:
    """Node E: Generate structured follow-up plan categorized by priority, deadlines, and dependencies."""
    workflow_id = state.get("workflow_run_id")
    analysis_record = state.get("analysis_record")
    analysis_id = analysis_record["id"] if analysis_record else state.get("workflow_run_id", "")
    tasks = state.get("persisted_tasks", [])

    planning_service = get_follow_up_planning_service()

    try:
        plan_resp = planning_service.generate_plan(
            analysis_id=analysis_id,
            tasks=tasks,
            analysis_record=analysis_record,
        )
        _update_workflow_db_stage(workflow_id, stage="finalize_workflow", status="processing", analysis_id=analysis_id)
        return {
            "follow_up_plan": plan_resp.model_dump(),
            "current_stage": "finalize_workflow",
        }
    except Exception as e:
        logger.error("Follow-up planning failed in workflow: %s", str(e))
        err = f"Follow-up planning generation failed: {str(e)}"
        _update_workflow_db_stage(workflow_id, stage="follow_up_planning", status="failed", error_stage="follow_up_planning", error_message=err, analysis_id=analysis_id)
        return {
            "status": "failed",
            "current_stage": "follow_up_planning",
            "error_stage": "follow_up_planning",
            "error_message": err,
        }


def finalize_workflow_node(state: MeetingWorkflowState) -> Dict[str, Any]:
    """Node F: Validate final outputs and mark workflow completed."""
    workflow_id = state.get("workflow_run_id")
    analysis_record = state.get("analysis_record")
    analysis_id = analysis_record.get("id") if analysis_record else None
    now_dt = datetime.now(timezone.utc)
    _update_workflow_db_stage(
        workflow_id,
        stage="finalized",
        status="completed",
        analysis_id=analysis_id,
        completed_at=now_dt,
    )
    return {
        "status": "completed",
        "current_stage": "finalized",
        "completed_at": now_dt.isoformat(),
    }


def error_handler_node(state: MeetingWorkflowState) -> Dict[str, Any]:
    """Node Error: Transition workflow to failed state with diagnostic metadata."""
    workflow_id = state.get("workflow_run_id")
    now_dt = datetime.now(timezone.utc)
    _update_workflow_db_stage(
        workflow_id,
        stage="failed",
        status="failed",
        error_stage=state.get("error_stage"),
        error_message=state.get("error_message"),
        completed_at=now_dt,
    )
    return {
        "status": "failed",
        "completed_at": now_dt.isoformat(),
    }


def should_continue(state: MeetingWorkflowState) -> str:
    """Conditional edge decision function checking for errors."""
    if state.get("status") == "failed" or state.get("error_message") is not None:
        return "error"
    return "continue"


def build_meeting_workflow_graph() -> Any:
    """Construct and compile the LangGraph meeting intelligence StateGraph."""
    graph = StateGraph(MeetingWorkflowState)

    # Register graph nodes
    graph.add_node("validate_input", validate_input_node)
    graph.add_node("retrieve_source", retrieve_source_node)
    graph.add_node("meeting_analysis", meeting_analysis_node)
    graph.add_node("action_item_extraction", action_item_extraction_node)
    graph.add_node("follow_up_planning", follow_up_planning_node)
    graph.add_node("finalize_workflow", finalize_workflow_node)
    graph.add_node("error_handler", error_handler_node)

    # Set workflow entrypoint
    graph.set_entry_point("validate_input")

    # Add conditional progression edges
    graph.add_conditional_edges(
        "validate_input",
        should_continue,
        {"continue": "retrieve_source", "error": "error_handler"},
    )
    graph.add_conditional_edges(
        "retrieve_source",
        should_continue,
        {"continue": "meeting_analysis", "error": "error_handler"},
    )
    graph.add_conditional_edges(
        "meeting_analysis",
        should_continue,
        {"continue": "action_item_extraction", "error": "error_handler"},
    )
    graph.add_conditional_edges(
        "action_item_extraction",
        should_continue,
        {"continue": "follow_up_planning", "error": "error_handler"},
    )
    graph.add_conditional_edges(
        "follow_up_planning",
        should_continue,
        {"continue": "finalize_workflow", "error": "error_handler"},
    )

    graph.add_edge("finalize_workflow", END)
    graph.add_edge("error_handler", END)

    return graph.compile()
