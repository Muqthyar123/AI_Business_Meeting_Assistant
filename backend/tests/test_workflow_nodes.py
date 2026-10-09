"""Unit tests for LangGraph meeting pipeline nodes and state transitions."""

import json
from unittest.mock import MagicMock
import mongomock
import pytest
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
from app.schemas.analysis import MeetingAnalysisResult
from app.schemas.task import (
    ActionItemExtractionResult,
    ExtractedTaskItem,
    TaskPriority,
)
from app.services.llm_service import LLMProviderError
from app.services.meeting_analysis_service import (
    MeetingAnalysisService,
    get_meeting_analysis_service,
)
from app.services.task_service import (
    ActionItemExtractionService,
    get_action_item_extraction_service,
)
from app.workflows.meeting_workflow import (
    MeetingWorkflowState,
    action_item_extraction_node,
    build_meeting_workflow_graph,
    error_handler_node,
    finalize_workflow_node,
    follow_up_planning_node,
    meeting_analysis_node,
    retrieve_source_node,
    should_continue,
    validate_input_node,
)


@pytest.fixture
def mock_db_repos(monkeypatch):
    """Set up mocked in-memory repositories for node testing."""
    mock_db = mongomock.MongoClient()["test_db"]
    analysis_repo = AnalysisRepository(db=mock_db)
    task_repo = TaskRepository(db=mock_db)
    transcription_repo = TranscriptionRepository(db=mock_db)
    document_repo = DocumentRepository(db=mock_db)

    monkeypatch.setattr("app.workflows.meeting_workflow.get_analysis_repository", lambda: analysis_repo)
    monkeypatch.setattr("app.workflows.meeting_workflow.get_task_repository", lambda: task_repo)
    monkeypatch.setattr("app.workflows.meeting_workflow.get_transcription_repository", lambda: transcription_repo)
    monkeypatch.setattr("app.workflows.meeting_workflow.get_document_repository", lambda: document_repo)

    return {
        "analysis_repo": analysis_repo,
        "task_repo": task_repo,
        "transcription_repo": transcription_repo,
        "document_repo": document_repo,
    }


def test_validate_input_node_success_and_errors():
    """Test validation node with valid inputs and various missing/unsupported inputs."""
    # Valid transcription
    state_valid: MeetingWorkflowState = {
        "source_type": "transcription",
        "source_id": "trans_123",
    }
    res = validate_input_node(state_valid)
    assert res["current_stage"] == "source_retrieval"
    assert res["error_message"] is None

    # Unsupported source type
    state_bad_type: MeetingWorkflowState = {
        "source_type": "unsupported_video",
    }
    res = validate_input_node(state_bad_type)
    assert res["status"] == "failed"
    assert "Unsupported source type" in res["error_message"]

    # Missing source_id for transcription
    state_missing_id: MeetingWorkflowState = {
        "source_type": "transcription",
    }
    res = validate_input_node(state_missing_id)
    assert res["status"] == "failed"
    assert "source_id is required" in res["error_message"]

    # Missing text for direct_text
    state_missing_text: MeetingWorkflowState = {
        "source_type": "direct_text",
        "text": "   ",
    }
    res = validate_input_node(state_missing_text)
    assert res["status"] == "failed"
    assert "Meeting text is required" in res["error_message"]


def test_retrieve_source_node_transcription(mock_db_repos):
    """Test retrieving source text from completed transcription."""
    trans_repo = mock_db_repos["transcription_repo"]
    trans_doc = trans_repo.create_queued(
        filename="meeting.mp3",
        file_format="mp3",
        file_size_bytes=1000,
        whisper_model="base",
    )
    trans_repo.mark_completed(trans_doc["id"], transcript_text="We agreed to launch the beta.")

    state: MeetingWorkflowState = {
        "source_type": "transcription",
        "source_id": trans_doc["id"],
    }
    res = retrieve_source_node(state)
    assert res["retrieved_text"] == "We agreed to launch the beta."
    assert res["current_stage"] == "meeting_analysis"


def test_retrieve_source_node_document_and_direct_text(mock_db_repos):
    """Test retrieving source text from document record and direct text."""
    doc_repo = mock_db_repos["document_repo"]
    doc = doc_repo.create({
        "source_type": "document",
        "title": "Roadmap Doc",
        "text_content": "Roadmap review content.",
        "status": "completed",
    })

    # Document retrieval
    state_doc: MeetingWorkflowState = {
        "source_type": "document",
        "source_id": doc["id"],
    }
    res_doc = retrieve_source_node(state_doc)
    assert res_doc["retrieved_text"] == "Roadmap review content."

    # Direct text retrieval
    state_direct: MeetingWorkflowState = {
        "source_type": "direct_text",
        "text": "Pasted notes directly.",
        "title": "Notes",
    }
    res_direct = retrieve_source_node(state_direct)
    assert res_direct["retrieved_text"] == "Pasted notes directly."
    assert res_direct["title"] == "Notes"


def test_meeting_analysis_node_fresh_and_reuse(mock_db_repos, monkeypatch):
    """Test meeting analysis node generating fresh analysis or reusing existing analysis."""
    analysis_repo = mock_db_repos["analysis_repo"]

    # 1. Fresh analysis generation
    mock_analysis_service = MagicMock(spec=MeetingAnalysisService)
    mock_provider = MagicMock()
    mock_provider.provider_name = "groq"
    mock_provider.model_name = "llama-3.3-70b-versatile"
    mock_analysis_service.provider = mock_provider
    mock_analysis_service.analyze_meeting.return_value = MeetingAnalysisResult(
        executive_summary="Executive summary test",
        meeting_purpose="Meeting purpose test",
        key_discussion_points=["Point 1"],
        decisions_made=["Decision 1"],
        risks_and_blockers=[],
        unresolved_questions=[],
        topics_and_themes=["Strategy"],
    )
    monkeypatch.setattr("app.workflows.meeting_workflow.get_meeting_analysis_service", lambda: mock_analysis_service)

    state_fresh: MeetingWorkflowState = {
        "source_type": "direct_text",
        "retrieved_text": "Meeting discussion text.",
        "title": "Fresh Meeting",
        "force_reanalyze": True,
    }
    res_fresh = meeting_analysis_node(state_fresh)
    assert res_fresh["analysis_record"]["executive_summary"] == "Executive summary test"

    # 2. Reusing existing analysis
    existing_id = res_fresh["analysis_record"]["id"]
    state_reuse: MeetingWorkflowState = {
        "source_type": "direct_text",
        "existing_analysis_id": existing_id,
        "force_reanalyze": False,
    }
    res_reuse = meeting_analysis_node(state_reuse)
    assert res_reuse["analysis_record"]["id"] == existing_id


def test_action_item_extraction_node_and_planning(mock_db_repos, monkeypatch):
    """Test extracting action items and follow-up planning nodes."""
    analysis_repo = mock_db_repos["analysis_repo"]
    analysis_doc = analysis_repo.create({
        "source_type": "direct_text",
        "title": "Planning Session",
        "executive_summary": "Summary",
        "meeting_purpose": "Purpose",
        "key_discussion_points": [],
        "decisions_made": [],
        "risks_and_blockers": [],
        "unresolved_questions": ["Budget cap?"],
        "topics_and_themes": [],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
    })

    mock_task_service = MagicMock(spec=ActionItemExtractionService)
    mock_task_service.extract_action_items.return_value = ActionItemExtractionResult(
        tasks=[
            ExtractedTaskItem(
                description="Deploy to staging",
                assignee="Alice",
                due_date="Tomorrow",
                priority=TaskPriority.HIGH,
            )
        ]
    )
    monkeypatch.setattr("app.workflows.meeting_workflow.get_action_item_extraction_service", lambda: mock_task_service)

    # Action items node
    state_task: MeetingWorkflowState = {
        "analysis_record": analysis_doc,
        "retrieved_text": "Alice will deploy to staging tomorrow.",
        "force_reanalyze": True,
    }
    res_task = action_item_extraction_node(state_task)
    assert len(res_task["persisted_tasks"]) == 1
    assert res_task["persisted_tasks"][0]["assignee"] == "Alice"

    # Follow-up planning node
    state_plan: MeetingWorkflowState = {
        "analysis_record": analysis_doc,
        "persisted_tasks": res_task["persisted_tasks"],
    }
    res_plan = follow_up_planning_node(state_plan)
    assert len(res_plan["follow_up_plan"]["immediate_actions"]) == 1
    assert "Budget cap?" in res_plan["follow_up_plan"]["pending_decisions"]


def test_finalize_and_error_handlers():
    """Test finalize, error handler, and conditional edge routing."""
    # Finalize
    state_fin: MeetingWorkflowState = {"status": "processing"}
    res_fin = finalize_workflow_node(state_fin)
    assert res_fin["status"] == "completed"
    assert res_fin["current_stage"] == "finalized"

    # Error handler
    state_err: MeetingWorkflowState = {"error_message": "Some error"}
    res_err = error_handler_node(state_err)
    assert res_err["status"] == "failed"

    # should_continue
    assert should_continue({"status": "processing"}) == "continue"
    assert should_continue({"status": "failed"}) == "error"
    assert should_continue({"error_message": "Failed step"}) == "error"


def test_build_meeting_workflow_graph_compilation():
    """Test that build_meeting_workflow_graph compiles without errors."""
    graph = build_meeting_workflow_graph()
    assert graph is not None
