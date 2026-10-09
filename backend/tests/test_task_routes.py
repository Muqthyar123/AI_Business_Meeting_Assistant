"""Integration tests for Action Items and Task Management API routes."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from bson import ObjectId
from fastapi import status
from fastapi.testclient import TestClient
import mongomock
import pytest
from pymongo.errors import PyMongoError
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
from app.schemas.task import (
    ActionItemExtractionResult,
    ExtractedTaskItem,
    TaskPriority,
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
    get_action_item_extraction_service,
)


@pytest.fixture
def mock_db():
    """Create an isolated in-memory MongoDB database using mongomock."""
    client = mongomock.MongoClient()
    db = client["test_meeting_assistant"]
    yield db
    client.close()
    close_mongo_connection()


@pytest.fixture
def test_client(mock_db):
    """Create FastAPI test client with mocked repositories."""
    analysis_repo = AnalysisRepository(db=mock_db)
    task_repo = TaskRepository(db=mock_db)
    transcription_repo = TranscriptionRepository(db=mock_db)
    document_repo = DocumentRepository(db=mock_db)

    app.dependency_overrides[get_analysis_repository] = lambda: analysis_repo
    app.dependency_overrides[get_task_repository] = lambda: task_repo
    app.dependency_overrides[get_transcription_repository] = lambda: transcription_repo
    app.dependency_overrides[get_document_repository] = lambda: document_repo

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_extract_action_items_transcription_source_success(test_client, mock_db):
    """Test extracting action items from an analysis linked to a transcription source."""
    prefix = get_settings().API_V1_PREFIX
    trans_repo = TranscriptionRepository(db=mock_db)
    analysis_repo = AnalysisRepository(db=mock_db)

    # 1. Create completed transcription
    trans_doc = trans_repo.create_queued(
        filename="meeting.mp3",
        file_format="mp3",
        file_size_bytes=1000,
        whisper_model="base",
    )
    trans_repo.mark_completed(
        trans_doc["id"],
        transcript_text="Alice will deploy the updated API by Friday. Bob will test auth.",
    )

    # 2. Create parent analysis
    analysis_doc = analysis_repo.create({
        "source_id": trans_doc["id"],
        "source_type": "transcription",
        "title": "Weekly Engineering Sync",
        "executive_summary": "Discussed deployment and auth.",
        "meeting_purpose": "Sync on release",
        "key_discussion_points": ["Deployment", "Auth testing"],
        "decisions_made": ["Deploy by Friday"],
        "risks_and_blockers": [],
        "unresolved_questions": [],
        "topics_and_themes": ["Engineering"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
    })

    # 3. Mock extraction service
    mock_extraction_service = MagicMock(spec=ActionItemExtractionService)
    mock_extraction_service.extract_action_items.return_value = ActionItemExtractionResult(
        tasks=[
            ExtractedTaskItem(
                description="Deploy updated API",
                assignee="Alice",
                has_missing_assignee=False,
                due_date="by Friday",
                priority=TaskPriority.HIGH,
                dependencies=[],
                evidence_excerpt="Alice will deploy the updated API by Friday.",
            ),
            ExtractedTaskItem(
                description="Test authentication modules",
                assignee="Bob",
                has_missing_assignee=False,
                due_date=None,
                priority=TaskPriority.MEDIUM,
                dependencies=["Deploy updated API"],
                evidence_excerpt="Bob will test auth.",
            ),
        ]
    )
    app.dependency_overrides[get_action_item_extraction_service] = lambda: mock_extraction_service

    resp = test_client.post(f"{prefix}/tasks/extract/{analysis_doc['id']}")
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert len(data) == 2
    assert data[0]["description"] == "Deploy updated API"
    assert data[0]["assignee"] == "Alice"
    assert data[0]["analysis_id"] == analysis_doc["id"]
    assert data[1]["assignee"] == "Bob"
    assert data[1]["dependencies"] == ["Deploy updated API"]


def test_extract_action_items_document_source_success(test_client, mock_db):
    """Test extracting action items from an analysis linked to an ingested document."""
    prefix = get_settings().API_V1_PREFIX
    doc_repo = DocumentRepository(db=mock_db)
    analysis_repo = AnalysisRepository(db=mock_db)

    # Create document
    doc = doc_repo.create({
        "source_type": "document",
        "title": "Strategy Doc",
        "text_content": "Emma needs to prepare the budget spreadsheet by Oct 20.",
        "status": "completed",
    })

    analysis_doc = analysis_repo.create({
        "source_id": doc["id"],
        "source_type": "document",
        "title": "Strategy Review",
        "executive_summary": "Budget discussion.",
        "meeting_purpose": "Budget review",
        "key_discussion_points": ["Budget limits"],
        "decisions_made": [],
        "risks_and_blockers": [],
        "unresolved_questions": [],
        "topics_and_themes": ["Finance"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
    })

    mock_service = MagicMock(spec=ActionItemExtractionService)
    mock_service.extract_action_items.return_value = ActionItemExtractionResult(
        tasks=[
            ExtractedTaskItem(
                description="Prepare budget spreadsheet",
                assignee="Emma",
                due_date="2026-10-20",
                priority=TaskPriority.HIGH,
            )
        ]
    )
    app.dependency_overrides[get_action_item_extraction_service] = lambda: mock_service

    resp = test_client.post(f"{prefix}/tasks/extract/{analysis_doc['id']}")
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert len(data) == 1
    assert data[0]["assignee"] == "Emma"


def test_extract_action_items_analysis_not_found(test_client):
    """Test extracting action items for a non-existent analysis ID returns 404."""
    prefix = get_settings().API_V1_PREFIX
    fake_id = str(ObjectId())
    resp = test_client.post(f"{prefix}/tasks/extract/{fake_id}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert f"Meeting analysis record '{fake_id}' was not found" in resp.json()["detail"]


@pytest.mark.parametrize(
    "exception_cls,expected_status",
    [
        (LLMConfigurationError("API key not set"), status.HTTP_503_SERVICE_UNAVAILABLE),
        (LLMAuthenticationError("Invalid API key"), status.HTTP_502_BAD_GATEWAY),
        (LLMRateLimitError("Rate limit exceeded"), status.HTTP_503_SERVICE_UNAVAILABLE),
        (LLMTimeoutError("Request timed out"), status.HTTP_504_GATEWAY_TIMEOUT),
        (LLMOutputParsingError("Malformed JSON"), status.HTTP_502_BAD_GATEWAY),
        (LLMProviderError("Provider error"), status.HTTP_502_BAD_GATEWAY),
    ],
)
def test_extract_action_items_llm_errors(test_client, mock_db, exception_cls, expected_status):
    """Test proper HTTP status code mapping when LLM extraction fails."""
    prefix = get_settings().API_V1_PREFIX
    analysis_repo = AnalysisRepository(db=mock_db)
    analysis_doc = analysis_repo.create({
        "source_type": "direct_text",
        "title": "Test Sync",
        "executive_summary": "Test summary",
        "meeting_purpose": "Test",
        "key_discussion_points": [],
        "decisions_made": [],
        "risks_and_blockers": [],
        "unresolved_questions": [],
        "topics_and_themes": [],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
    })

    mock_service = MagicMock(spec=ActionItemExtractionService)
    mock_service.extract_action_items.side_effect = exception_cls
    app.dependency_overrides[get_action_item_extraction_service] = lambda: mock_service

    resp = test_client.post(f"{prefix}/tasks/extract/{analysis_doc['id']}")
    assert resp.status_code == expected_status


def test_create_task_manual(test_client, mock_db):
    """Test manual creation of a task."""
    prefix = get_settings().API_V1_PREFIX
    analysis_repo = AnalysisRepository(db=mock_db)
    analysis_doc = analysis_repo.create({
        "source_type": "direct_text",
        "title": "Sprint Planning",
        "executive_summary": "Sprint planning meeting.",
        "meeting_purpose": "Plan sprint",
        "key_discussion_points": [],
        "decisions_made": [],
        "risks_and_blockers": [],
        "unresolved_questions": [],
        "topics_and_themes": [],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
    })

    payload = {
        "analysis_id": analysis_doc["id"],
        "description": "Create integration tests for task endpoints",
        "assignee": "Tester",
        "priority": "high",
        "due_date": "Today",
        "dependencies": ["Implement endpoints"],
    }
    resp = test_client.post(f"{prefix}/tasks/", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["description"] == "Create integration tests for task endpoints"
    assert data["assignee"] == "Tester"
    assert data["status"] == "pending"


def test_list_tasks_and_filters(test_client, mock_db):
    """Test listing tasks with filters."""
    prefix = get_settings().API_V1_PREFIX
    task_repo = TaskRepository(db=mock_db)

    task_repo.create({
        "analysis_id": "a1",
        "description": "Task 1",
        "status": "pending",
        "priority": "high",
        "assignee": "Alex",
    })
    task_repo.create({
        "analysis_id": "a1",
        "description": "Task 2",
        "status": "completed",
        "priority": "low",
        "assignee": "Bob",
    })

    # List all
    resp = test_client.get(f"{prefix}/tasks/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["total"] == 2

    # Filter by status
    resp = test_client.get(f"{prefix}/tasks/?status=pending")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["total"] == 1

    # Filter by priority
    resp = test_client.get(f"{prefix}/tasks/?priority=high")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["total"] == 1


def test_get_task_by_id_and_not_found(test_client, mock_db):
    """Test getting single task by ID."""
    prefix = get_settings().API_V1_PREFIX
    task_repo = TaskRepository(db=mock_db)
    created = task_repo.create({
        "analysis_id": "a1",
        "description": "Task to fetch",
    })

    resp = test_client.get(f"{prefix}/tasks/{created['id']}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["id"] == created["id"]

    resp = test_client.get(f"{prefix}/tasks/{str(ObjectId())}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_patch_task_and_patch_status(test_client, mock_db):
    """Test updating task details and updating status."""
    prefix = get_settings().API_V1_PREFIX
    task_repo = TaskRepository(db=mock_db)
    created = task_repo.create({
        "analysis_id": "a1",
        "description": "Original description",
        "status": "pending",
    })
    task_id = created["id"]

    # Patch details
    patch_resp = test_client.patch(
        f"{prefix}/tasks/{task_id}",
        json={"description": "Updated description", "assignee": "Lead Engineer"},
    )
    assert patch_resp.status_code == status.HTTP_200_OK
    assert patch_resp.json()["description"] == "Updated description"
    assert patch_resp.json()["assignee"] == "Lead Engineer"

    # Patch status
    status_resp = test_client.patch(
        f"{prefix}/tasks/{task_id}/status",
        json={"status": "completed"},
    )
    assert status_resp.status_code == status.HTTP_200_OK
    assert status_resp.json()["status"] == "completed"


def test_delete_task(test_client, mock_db):
    """Test deleting task."""
    prefix = get_settings().API_V1_PREFIX
    task_repo = TaskRepository(db=mock_db)
    created = task_repo.create({
        "analysis_id": "a1",
        "description": "Task to delete",
    })
    task_id = created["id"]

    del_resp = test_client.delete(f"{prefix}/tasks/{task_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Second delete returns 404
    del_resp2 = test_client.delete(f"{prefix}/tasks/{task_id}")
    assert del_resp2.status_code == status.HTTP_404_NOT_FOUND


def test_get_follow_up_plan_endpoint(test_client, mock_db):
    """Test GET /api/tasks/analysis/{analysis_id}/plan endpoint."""
    prefix = get_settings().API_V1_PREFIX
    analysis_repo = AnalysisRepository(db=mock_db)
    task_repo = TaskRepository(db=mock_db)

    analysis_doc = analysis_repo.create({
        "source_type": "direct_text",
        "title": "Quarterly Planning",
        "executive_summary": "Planning session for Q4.",
        "meeting_purpose": "Q4 Plan",
        "key_discussion_points": ["Budget"],
        "decisions_made": [],
        "risks_and_blockers": ["Resource constraints"],
        "unresolved_questions": ["What is the marketing budget?"],
        "topics_and_themes": ["Strategy"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
    })

    task_repo.create({
        "analysis_id": analysis_doc["id"],
        "description": "Review cloud infrastructure costs",
        "assignee": "DevOps Lead",
        "priority": "high",
        "due_date": "asap",
        "status": "pending",
        "dependencies": [],
    })

    resp = test_client.get(f"{prefix}/tasks/analysis/{analysis_doc['id']}/plan")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["analysis_id"] == analysis_doc["id"]
    assert len(data["immediate_actions"]) == 1
    assert "What is the marketing budget?" in data["pending_decisions"]
    assert len(data["ai_suggestions"]) > 0


def test_export_tasks_endpoints(test_client, mock_db):
    """Test exporting tasks in JSON, CSV, and Markdown formats."""
    prefix = get_settings().API_V1_PREFIX
    analysis_repo = AnalysisRepository(db=mock_db)
    task_repo = TaskRepository(db=mock_db)

    analysis_doc = analysis_repo.create({
        "source_type": "direct_text",
        "title": "Export Test Meeting",
        "executive_summary": "Testing export formats.",
        "meeting_purpose": "Test exports",
        "key_discussion_points": [],
        "decisions_made": [],
        "risks_and_blockers": [],
        "unresolved_questions": [],
        "topics_and_themes": [],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
    })

    task_repo.create({
        "analysis_id": analysis_doc["id"],
        "description": "Export item 1",
        "assignee": "Lead",
        "priority": "high",
    })

    # JSON export
    resp_json = test_client.get(f"{prefix}/tasks/export?format=json&analysis_id={analysis_doc['id']}")
    assert resp_json.status_code == status.HTTP_200_OK
    assert "application/json" in resp_json.headers["content-type"]
    assert "attachment; filename=" in resp_json.headers["content-disposition"]

    # CSV export
    resp_csv = test_client.get(f"{prefix}/tasks/export?format=csv&analysis_id={analysis_doc['id']}")
    assert resp_csv.status_code == status.HTTP_200_OK
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "Task ID,Analysis ID,Description" in resp_csv.text

    # Markdown export
    resp_md = test_client.get(f"{prefix}/tasks/export?format=markdown&analysis_id={analysis_doc['id']}")
    assert resp_md.status_code == status.HTTP_200_OK
    assert "text/markdown" in resp_md.headers["content-type"]
    assert "# Export Test Meeting" in resp_md.text
    assert "## Master Action Items Table" in resp_md.text
