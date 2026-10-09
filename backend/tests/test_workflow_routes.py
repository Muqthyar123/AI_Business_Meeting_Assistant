"""Integration tests for LangGraph Workflow routes."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from bson import ObjectId
from fastapi import status
from fastapi.testclient import TestClient
import mongomock
import pytest
from app.config import get_settings
from app.database import close_mongo_connection
from app.main import app
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
from app.schemas.analysis import MeetingAnalysisResult
from app.schemas.task import (
    ActionItemExtractionResult,
    ExtractedTaskItem,
    TaskPriority,
)
from app.services.meeting_analysis_service import (
    MeetingAnalysisService,
    get_meeting_analysis_service,
)
from app.services.task_service import (
    ActionItemExtractionService,
    get_action_item_extraction_service,
)


@pytest.fixture
def mock_db(monkeypatch):
    """Create isolated in-memory MongoDB database using mongomock."""
    client = mongomock.MongoClient()
    db = client["test_meeting_assistant"]
    import app.database
    monkeypatch.setattr(app.database, "_database", db)
    yield db
    client.close()
    close_mongo_connection()


@pytest.fixture
def test_client(mock_db, monkeypatch):
    """Create FastAPI test client with mocked dependencies."""
    analysis_repo = AnalysisRepository(db=mock_db)
    task_repo = TaskRepository(db=mock_db)
    transcription_repo = TranscriptionRepository(db=mock_db)
    document_repo = DocumentRepository(db=mock_db)
    workflow_repo = WorkflowRepository(db=mock_db)

    app.dependency_overrides[get_analysis_repository] = lambda: analysis_repo
    app.dependency_overrides[get_task_repository] = lambda: task_repo
    app.dependency_overrides[get_transcription_repository] = lambda: transcription_repo
    app.dependency_overrides[get_document_repository] = lambda: document_repo
    app.dependency_overrides[get_workflow_repository] = lambda: workflow_repo

    # Mock Analysis Service
    mock_analysis_service = MagicMock(spec=MeetingAnalysisService)
    mock_provider = MagicMock()
    mock_provider.provider_name = "groq"
    mock_provider.model_name = "llama-3.3-70b-versatile"
    mock_analysis_service.provider = mock_provider
    mock_analysis_service.analyze_meeting.return_value = MeetingAnalysisResult(
        executive_summary="Team reviewed roadmap and approved release schedule.",
        meeting_purpose="Align on quarterly deliverables",
        key_discussion_points=["Release date", "Feature freeze"],
        decisions_made=["Approved release for Nov 1"],
        risks_and_blockers=["Load test delays"],
        unresolved_questions=["Third-party license cost?"],
        topics_and_themes=["Release", "QA"],
    )
    app.dependency_overrides[get_meeting_analysis_service] = lambda: mock_analysis_service
    monkeypatch.setattr("app.workflows.meeting_workflow.get_meeting_analysis_service", lambda: mock_analysis_service)

    # Mock Action Item Extraction Service
    mock_task_service = MagicMock(spec=ActionItemExtractionService)
    mock_task_service.extract_action_items.return_value = ActionItemExtractionResult(
        tasks=[
            ExtractedTaskItem(
                description="Execute final end-to-end performance tests",
                assignee="QA Lead",
                has_missing_assignee=False,
                due_date="by Oct 25",
                priority=TaskPriority.HIGH,
                dependencies=["Staging deployment"],
                evidence_excerpt="QA Lead will execute tests by Oct 25.",
            )
        ]
    )
    app.dependency_overrides[get_action_item_extraction_service] = lambda: mock_task_service
    monkeypatch.setattr("app.workflows.meeting_workflow.get_action_item_extraction_service", lambda: mock_task_service)

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_start_workflow_background_endpoint(test_client, mock_db):
    """Test POST /api/workflows/start kicks off background workflow and returns 202 Accepted."""
    prefix = get_settings().API_V1_PREFIX
    trans_repo = TranscriptionRepository(db=mock_db)

    trans_doc = trans_repo.create_queued(
        filename="meeting.mp3",
        file_format="mp3",
        file_size_bytes=1000,
        whisper_model="base",
    )
    trans_repo.mark_completed(trans_doc["id"], transcript_text="Team aligned on sprint goals.")

    payload = {
        "source_type": "transcription",
        "source_id": trans_doc["id"],
        "title": "Sprint Alignment",
    }
    resp = test_client.post(f"{prefix}/workflows/start", json=payload)
    assert resp.status_code == status.HTTP_202_ACCEPTED
    data = resp.json()
    assert data["id"] is not None
    assert data["source_type"] == "transcription"
    assert data["source_id"] == trans_doc["id"]


def test_run_workflow_sync_endpoint(test_client, mock_db):
    """Test POST /api/workflows/run-sync executes full workflow and returns consolidated result."""
    prefix = get_settings().API_V1_PREFIX
    doc_repo = DocumentRepository(db=mock_db)

    doc = doc_repo.create({
        "source_type": "document",
        "title": "Architecture Doc",
        "text_content": "Architecture sync meeting text content.",
        "status": "completed",
    })

    payload = {
        "source_type": "document",
        "source_id": doc["id"],
        "title": "Architecture Review",
    }
    resp = test_client.post(f"{prefix}/workflows/run-sync", json=payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["id"] is not None
    assert data["status"] == "completed"
    assert data["current_stage"] == "finalized"
    assert data["analysis"] is not None
    assert data["analysis"]["executive_summary"] == "Team reviewed roadmap and approved release schedule."
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["assignee"] == "QA Lead"
    assert data["follow_up_plan"] is not None
    assert len(data["follow_up_plan"]["immediate_actions"]) == 1


def test_get_workflow_status_and_not_found(test_client, mock_db):
    """Test GET /api/workflows/{workflow_id} polling status."""
    prefix = get_settings().API_V1_PREFIX
    workflow_repo = WorkflowRepository(db=mock_db)
    created = workflow_repo.create({
        "source_type": "direct_text",
        "status": "processing",
        "current_stage": "meeting_analysis",
    })

    resp = test_client.get(f"{prefix}/workflows/{created['id']}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "processing"

    resp404 = test_client.get(f"{prefix}/workflows/{str(ObjectId())}")
    assert resp404.status_code == status.HTTP_404_NOT_FOUND


def test_get_workflow_result_endpoint(test_client, mock_db):
    """Test GET /api/workflows/{workflow_id}/result."""
    prefix = get_settings().API_V1_PREFIX
    workflow_repo = WorkflowRepository(db=mock_db)
    analysis_repo = AnalysisRepository(db=mock_db)
    task_repo = TaskRepository(db=mock_db)

    analysis_doc = analysis_repo.create({
        "source_type": "direct_text",
        "title": "Result Test",
        "executive_summary": "Summary text",
        "meeting_purpose": "Purpose",
        "key_discussion_points": [],
        "decisions_made": [],
        "risks_and_blockers": [],
        "unresolved_questions": [],
        "topics_and_themes": [],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
    })

    task_doc = task_repo.create({
        "analysis_id": analysis_doc["id"],
        "description": "Task 1",
        "assignee": "Dev",
        "priority": "high",
    })

    workflow_doc = workflow_repo.create({
        "source_type": "direct_text",
        "status": "completed",
        "current_stage": "finalized",
        "analysis_id": analysis_doc["id"],
    })

    resp = test_client.get(f"{prefix}/workflows/{workflow_doc['id']}/result")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["status"] == "completed"
    assert data["analysis"]["id"] == analysis_doc["id"]
    assert len(data["tasks"]) == 1


def test_list_workflows_route(test_client, mock_db):
    """Test GET /api/workflows/ with pagination and filters."""
    prefix = get_settings().API_V1_PREFIX
    workflow_repo = WorkflowRepository(db=mock_db)

    workflow_repo.create({"source_type": "transcription", "status": "completed"})
    workflow_repo.create({"source_type": "document", "status": "failed"})

    resp = test_client.get(f"{prefix}/workflows/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["total"] == 2

    resp_filtered = test_client.get(f"{prefix}/workflows/?status=failed")
    assert resp_filtered.status_code == status.HTTP_200_OK
    assert resp_filtered.json()["total"] == 1


def test_retry_workflow_endpoint(test_client, mock_db):
    """Test POST /api/workflows/{workflow_id}/retry."""
    prefix = get_settings().API_V1_PREFIX
    workflow_repo = WorkflowRepository(db=mock_db)

    failed_doc = workflow_repo.create({
        "source_type": "direct_text",
        "status": "failed",
        "error_stage": "meeting_analysis",
        "error_message": "LLM timeout",
    })

    resp = test_client.post(f"{prefix}/workflows/{failed_doc['id']}/retry")
    assert resp.status_code == status.HTTP_202_ACCEPTED
    assert resp.json()["status"] == "queued"

    # Retrying a processing workflow returns 400
    proc_doc = workflow_repo.create({"source_type": "direct_text", "status": "processing"})
    resp_bad = test_client.post(f"{prefix}/workflows/{proc_doc['id']}/retry")
    assert resp_bad.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_workflow_endpoint(test_client, mock_db):
    """Test DELETE /api/workflows/{workflow_id}."""
    prefix = get_settings().API_V1_PREFIX
    workflow_repo = WorkflowRepository(db=mock_db)
    doc = workflow_repo.create({"source_type": "direct_text"})

    resp = test_client.delete(f"{prefix}/workflows/{doc['id']}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    resp404 = test_client.delete(f"{prefix}/workflows/{doc['id']}")
    assert resp404.status_code == status.HTTP_404_NOT_FOUND
