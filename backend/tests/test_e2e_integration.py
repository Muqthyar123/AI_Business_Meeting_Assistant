"""Comprehensive End-to-End Integration Tests for AI Business Meeting Assistant.

Tests all complete pipeline flows:
1. Audio -> Transcription -> Workflow -> Analysis -> Action Items -> Follow-up Plan -> Exports
2. Document (PDF/DOCX/TXT) -> Ingestion -> Workflow -> Analysis -> Action Items -> Follow-up Plan -> Exports
3. Direct / Pasted Text -> Workflow -> Analysis -> Action Items -> Follow-up Plan -> Exports
4. Idempotency, Task Regeneration, and Manual Updates
5. System Resilience, Error Masking, and Security
6. OpenAPI Schema Generation & Route Registry Validation
"""

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
from app.services.llm_service import (
    LLMAuthenticationError,
)
from app.services.meeting_analysis_service import (
    MeetingAnalysisService,
    get_meeting_analysis_service,
)
from app.services.task_service import (
    ActionItemExtractionService,
    get_action_item_extraction_service,
)
from app.services.whisper_service import (
    WhisperModelStatus,
    WhisperService,
    get_whisper_service,
)


@pytest.fixture
def mock_db(monkeypatch):
    """Create an isolated in-memory MongoDB instance."""
    client = mongomock.MongoClient()
    db = client["test_e2e_meeting_assistant"]
    import app.database
    monkeypatch.setattr(app.database, "_database", db)
    yield db
    client.close()
    close_mongo_connection()


@pytest.fixture
def e2e_client(mock_db, monkeypatch):
    """Create TestClient with fully wired repositories and mocked AI service providers."""
    # Wire repositories
    transcription_repo = TranscriptionRepository(db=mock_db)
    document_repo = DocumentRepository(db=mock_db)
    analysis_repo = AnalysisRepository(db=mock_db)
    task_repo = TaskRepository(db=mock_db)
    workflow_repo = WorkflowRepository(db=mock_db)

    app.dependency_overrides[get_transcription_repository] = lambda: transcription_repo
    app.dependency_overrides[get_document_repository] = lambda: document_repo
    app.dependency_overrides[get_analysis_repository] = lambda: analysis_repo
    app.dependency_overrides[get_task_repository] = lambda: task_repo
    app.dependency_overrides[get_workflow_repository] = lambda: workflow_repo

    # Mock Whisper Service
    mock_whisper = MagicMock(spec=WhisperService)
    mock_whisper.status = WhisperModelStatus.LOADED
    mock_whisper.model_name = "small"
    mock_whisper.transcribe.return_value = {
        "text": "Alex presented the Q4 roadmap. Sarah agreed to deploy the new auth service by Friday.",
        "language": "en",
        "duration": 45.5,
        "segments": [],
    }
    app.dependency_overrides[get_whisper_service] = lambda: mock_whisper

    # Mock Meeting Analysis Service
    mock_analysis_svc = MagicMock(spec=MeetingAnalysisService)
    mock_provider = MagicMock()
    mock_provider.provider_name = "groq"
    mock_provider.model_name = "llama-3.3-70b-versatile"
    mock_analysis_svc.provider = mock_provider
    mock_analysis_svc.analyze_meeting.return_value = MeetingAnalysisResult(
        executive_summary="Team reviewed Q4 roadmap and agreed on authentication deployment schedule.",
        meeting_purpose="Review Q4 deliverables and allocate deployment ownership",
        key_discussion_points=[
            "Q4 architectural roadmap review",
            "Authentication service migration timeline",
        ],
        decisions_made=[
            "Deploy authentication service to staging by Friday",
            "Freeze non-critical feature work during migration",
        ],
        risks_and_blockers=[
            "Potential latency spike during database index rebuild",
        ],
        unresolved_questions=[
            "Who will handle emergency rollback documentation?",
        ],
        topics_and_themes=[
            "Infrastructure",
            "Security",
            "Roadmap",
        ],
    )
    app.dependency_overrides[get_meeting_analysis_service] = lambda: mock_analysis_svc
    monkeypatch.setattr("app.workflows.meeting_workflow.get_meeting_analysis_service", lambda: mock_analysis_svc)

    # Mock Action Item Extraction Service
    mock_task_svc = MagicMock(spec=ActionItemExtractionService)
    mock_task_svc.extract_action_items.return_value = ActionItemExtractionResult(
        tasks=[
            ExtractedTaskItem(
                description="Deploy authentication service to staging environment",
                assignee="Sarah",
                has_missing_assignee=False,
                due_date="by Friday",
                priority=TaskPriority.HIGH,
                dependencies=["Database index rebuild"],
                evidence_excerpt="Sarah agreed to deploy the new auth service by Friday.",
            ),
            ExtractedTaskItem(
                description="Draft emergency rollback documentation",
                assignee=None,
                has_missing_assignee=True,
                due_date=None,
                priority=TaskPriority.MEDIUM,
                dependencies=[],
                evidence_excerpt="Who will handle emergency rollback documentation?",
            ),
        ]
    )
    app.dependency_overrides[get_action_item_extraction_service] = lambda: mock_task_svc
    monkeypatch.setattr("app.workflows.meeting_workflow.get_action_item_extraction_service", lambda: mock_task_svc)

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# =========================================================================
# 1. AUDIO END-TO-END PIPELINE
# =========================================================================

def test_e2e_audio_pipeline(e2e_client, mock_db):
    """Validate full flow: Audio Upload -> Transcription -> Workflow -> Analysis -> Tasks -> Follow-up Plan -> Exports."""
    prefix = get_settings().API_V1_PREFIX

    # Step 1: Upload audio file
    fake_wav_content = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    upload_resp = e2e_client.post(
        f"{prefix}/transcriptions/upload",
        files={"file": ("team_sync.wav", fake_wav_content, "audio/wav")},
        data={"language": "en"},
    )
    assert upload_resp.status_code == status.HTTP_202_ACCEPTED
    upload_data = upload_resp.json()
    job_id = upload_data["job_id"]
    assert job_id is not None

    # Step 2: Mark transcription as completed in DB (simulate background worker finishing)
    trans_repo = TranscriptionRepository(db=mock_db)
    trans_repo.mark_completed(
        record_id=job_id,
        transcript_text="Alex presented the Q4 roadmap. Sarah agreed to deploy the new auth service by Friday.",
        detected_language="en",
        audio_duration=45.5,
    )

    # Step 3: Verify transcription record retrieval
    get_trans_resp = e2e_client.get(f"{prefix}/transcriptions/{job_id}")
    assert get_trans_resp.status_code == status.HTTP_200_OK
    trans_data = get_trans_resp.json()
    assert trans_data["status"] == "completed"
    assert "Alex presented" in trans_data["transcript_text"]

    # Step 4: Execute full LangGraph workflow synchronously
    workflow_resp = e2e_client.post(
        f"{prefix}/workflows/run-sync",
        json={
            "source_type": "transcription",
            "source_id": job_id,
            "title": "Q4 Roadmap & Deployment Sync",
            "force_reanalyze": True,
        },
    )
    assert workflow_resp.status_code == status.HTTP_200_OK
    wf_data = workflow_resp.json()
    workflow_id = wf_data["id"]

    assert wf_data["status"] == "completed"
    assert wf_data["current_stage"] == "finalized"
    assert wf_data["analysis"] is not None
    assert wf_data["analysis"]["executive_summary"] == "Team reviewed Q4 roadmap and agreed on authentication deployment schedule."
    assert len(wf_data["tasks"]) == 2
    assert wf_data["tasks"][0]["assignee"] == "Sarah"
    assert wf_data["tasks"][1]["has_missing_assignee"] is True
    assert wf_data["follow_up_plan"] is not None
    assert len(wf_data["follow_up_plan"]["immediate_actions"]) >= 1

    # Step 5: Verify consolidated workflow result endpoint
    wf_result_resp = e2e_client.get(f"{prefix}/workflows/{workflow_id}/result")
    assert wf_result_resp.status_code == status.HTTP_200_OK
    assert wf_result_resp.json()["id"] == workflow_id

    # Step 6: Verify JSON, CSV, and Markdown Exports
    analysis_id = wf_data["analysis"]["id"]

    # 6a. JSON Export
    json_export_resp = e2e_client.get(f"{prefix}/tasks/export?format=json&analysis_id={analysis_id}")
    assert json_export_resp.status_code == status.HTTP_200_OK
    assert "application/json" in json_export_resp.headers["content-type"]
    assert "attachment" in json_export_resp.headers["content-disposition"]
    export_json = json_export_resp.json()
    assert len(export_json["tasks"]) == 2
    assert "follow_up_plan" in export_json

    # 6b. CSV Export
    csv_export_resp = e2e_client.get(f"{prefix}/tasks/export?format=csv&analysis_id={analysis_id}")
    assert csv_export_resp.status_code == status.HTTP_200_OK
    assert "text/csv" in csv_export_resp.headers["content-type"]
    assert "Sarah" in csv_export_resp.text

    # 6c. Markdown Export
    md_export_resp = e2e_client.get(f"{prefix}/tasks/export?format=markdown&analysis_id={analysis_id}")
    assert md_export_resp.status_code == status.HTTP_200_OK
    assert "text/markdown" in md_export_resp.headers["content-type"]
    assert "## Follow-up Action Plan" in md_export_resp.text
    assert "Deploy authentication service" in md_export_resp.text


# =========================================================================
# 2. DOCUMENT INGESTION END-TO-END PIPELINE
# =========================================================================

def test_e2e_document_pipeline(e2e_client, mock_db):
    """Validate full flow: Document Upload (.txt) -> Ingestion -> Workflow -> Analysis -> Tasks -> Follow-up Plan -> Exports."""
    prefix = get_settings().API_V1_PREFIX

    # Step 1: Upload text document
    doc_content = b"Executive leadership meeting notes. Discussed Q4 budget and approved staging migration."
    upload_resp = e2e_client.post(
        f"{prefix}/documents/upload",
        files={"file": ("meeting_notes.txt", doc_content, "text/plain")},
        data={"title": "Executive Leadership Notes"},
    )
    assert upload_resp.status_code == status.HTTP_201_CREATED
    doc_data = upload_resp.json()
    document_id = doc_data["id"]
    assert doc_data["word_count"] > 0
    assert doc_data["character_count"] > 0

    # Step 2: Get document details
    get_doc_resp = e2e_client.get(f"{prefix}/documents/{document_id}")
    assert get_doc_resp.status_code == status.HTTP_200_OK
    assert get_doc_resp.json()["title"] == "Executive Leadership Notes"

    # Step 3: Run workflow for document
    wf_resp = e2e_client.post(
        f"{prefix}/workflows/run-sync",
        json={
            "source_type": "document",
            "source_id": document_id,
            "title": "Executive Sync Workflow",
        },
    )
    assert wf_resp.status_code == status.HTTP_200_OK
    wf_data = wf_resp.json()
    assert wf_data["status"] == "completed"
    assert wf_data["analysis"]["meeting_purpose"] == "Review Q4 deliverables and allocate deployment ownership"
    assert len(wf_data["tasks"]) == 2

    # Step 4: List tasks filtered by this analysis
    analysis_id = wf_data["analysis"]["id"]
    tasks_resp = e2e_client.get(f"{prefix}/tasks/?analysis_id={analysis_id}")
    assert tasks_resp.status_code == status.HTTP_200_OK
    tasks_data = tasks_resp.json()
    assert tasks_data["total"] == 2


# =========================================================================
# 3. DIRECT / PASTED TEXT END-TO-END PIPELINE & TASK UPDATES
# =========================================================================

def test_e2e_pasted_text_pipeline_and_task_mutations(e2e_client, mock_db):
    """Validate full flow: Pasted Text Submission -> Workflow -> Task Status Update -> Plan Refresh."""
    prefix = get_settings().API_V1_PREFIX

    # Step 1: Submit pasted text
    pasted_resp = e2e_client.post(
        f"{prefix}/documents/text",
        json={
            "text": "Design review sync: User interface completed. Backend API contracts finalized.",
            "title": "Design Sync Notes",
        },
    )
    assert pasted_resp.status_code == status.HTTP_201_CREATED
    pasted_data = pasted_resp.json()
    pasted_id = pasted_data["id"]

    # Step 2: Run workflow directly on raw text
    wf_resp = e2e_client.post(
        f"{prefix}/workflows/run-sync",
        json={
            "source_type": "direct_text",
            "text": "Design review sync: User interface completed. Backend API contracts finalized.",
            "title": "Design Review Run",
        },
    )
    assert wf_resp.status_code == status.HTTP_200_OK
    wf_data = wf_resp.json()
    assert wf_data["status"] == "completed"
    analysis_id = wf_data["analysis"]["id"]
    task_id = wf_data["tasks"][0]["id"]

    # Step 3: Update Task Status to 'completed'
    patch_status_resp = e2e_client.patch(
        f"{prefix}/tasks/{task_id}/status",
        json={"status": "completed"},
    )
    assert patch_status_resp.status_code == status.HTTP_200_OK
    assert patch_status_resp.json()["status"] == "completed"

    # Step 4: Update Task Details (assignee, priority, due date)
    patch_task_resp = e2e_client.patch(
        f"{prefix}/tasks/{task_id}",
        json={
            "assignee": "Lead Engineer",
            "priority": "high",
            "due_date": "by Monday",
        },
    )
    assert patch_task_resp.status_code == status.HTTP_200_OK
    updated_task = patch_task_resp.json()
    assert updated_task["assignee"] == "Lead Engineer"
    assert updated_task["priority"] == "high"
    assert updated_task["due_date"] == "by Monday"
    assert updated_task["has_missing_assignee"] is False

    # Step 5: Fetch fresh follow-up plan
    plan_resp = e2e_client.get(f"{prefix}/tasks/analysis/{analysis_id}/plan")
    assert plan_resp.status_code == status.HTTP_200_OK
    plan_data = plan_resp.json()
    assert plan_data["total_tasks"] == 2


# =========================================================================
# 4. IDEMPOTENCY & REGENERATION TESTS
# =========================================================================

def test_workflow_idempotency_and_regeneration(e2e_client, mock_db):
    """Verify that force_reanalyze=False reuses existing analysis and tasks, while replace=True avoids duplication."""
    prefix = get_settings().API_V1_PREFIX
    doc_repo = DocumentRepository(db=mock_db)

    doc = doc_repo.create({
        "source_type": "document",
        "title": "Architecture Spec",
        "text_content": "Detailed microservices decomposition plan.",
        "status": "completed",
    })

    # Run 1: Create initial analysis and tasks
    wf1_resp = e2e_client.post(
        f"{prefix}/workflows/run-sync",
        json={
            "source_type": "document",
            "source_id": doc["id"],
            "force_reanalyze": False,
        },
    )
    assert wf1_resp.status_code == status.HTTP_200_OK
    wf1_data = wf1_resp.json()
    analysis_id_1 = wf1_data["analysis"]["id"]

    # Run 2: Re-run with force_reanalyze=False -> should reuse same analysis
    wf2_resp = e2e_client.post(
        f"{prefix}/workflows/run-sync",
        json={
            "source_type": "document",
            "source_id": doc["id"],
            "force_reanalyze": False,
        },
    )
    assert wf2_resp.status_code == status.HTTP_200_OK
    wf2_data = wf2_resp.json()
    assert wf2_data["analysis"]["id"] == analysis_id_1
    assert len(wf2_data["tasks"]) == 2

    # Run 3: Extract action items again with replace=True -> task count remains 2 (no duplicates)
    re_extract_resp = e2e_client.post(
        f"{prefix}/tasks/extract/{analysis_id_1}?replace=true"
    )
    assert re_extract_resp.status_code == status.HTTP_201_CREATED
    assert len(re_extract_resp.json()) == 2

    # Check database task count for this analysis
    task_repo = TaskRepository(db=mock_db)
    current_tasks = task_repo.get_by_analysis_id(analysis_id_1)
    assert len(current_tasks) == 2


# =========================================================================
# 5. OPENAPI SCHEMA AND ROUTE REGISTRY VALIDATION
# =========================================================================

def test_openapi_schema_generation_and_routes():
    """Verify that OpenAPI schema generates cleanly with all routes, tags, and valid status codes."""
    schema = app.openapi()
    assert schema is not None
    assert "openapi" in schema
    assert schema["info"]["title"] == "AI Business Meeting Assistant"

    paths = schema["paths"]
    expected_endpoints = [
        "/api/transcriptions/upload",
        "/api/transcriptions/",
        "/api/transcriptions/{record_id}",
        "/api/documents/upload",
        "/api/documents/text",
        "/api/documents/",
        "/api/documents/{document_id}",
        "/api/analysis/",
        "/api/analysis/{analysis_id}",
        "/api/tasks/extract/{analysis_id}",
        "/api/tasks/",
        "/api/tasks/export",
        "/api/tasks/analysis/{analysis_id}/plan",
        "/api/tasks/{task_id}",
        "/api/tasks/{task_id}/status",
        "/api/workflows/start",
        "/api/workflows/run-sync",
        "/api/workflows/",
        "/api/workflows/{workflow_id}",
        "/api/workflows/{workflow_id}/result",
        "/api/workflows/{workflow_id}/retry",
        "/api/health",
        "/",
    ]

    for ep in expected_endpoints:
        assert ep in paths, f"Missing endpoint in OpenAPI paths: {ep}"

    # Verify expected tags
    all_operation_tags = set()
    for path_data in paths.values():
        for method, op_data in path_data.items():
            if isinstance(op_data, dict) and "tags" in op_data:
                all_operation_tags.update(op_data["tags"])

    assert "transcriptions" in all_operation_tags
    assert "documents" in all_operation_tags
    assert "analysis" in all_operation_tags
    assert "tasks" in all_operation_tags
    assert "workflows" in all_operation_tags
    assert "health" in all_operation_tags


# =========================================================================
# 6. SYSTEM RESILIENCE, SECURITY & ERROR HANDLING
# =========================================================================

def test_health_check_database_unavailability(e2e_client, monkeypatch):
    """Verify health check returns degraded 503 when MongoDB is unreachable."""
    prefix = get_settings().API_V1_PREFIX
    import app.main
    monkeypatch.setattr(app.main, "ping_database", lambda: False)

    resp = e2e_client.get(f"{prefix}/health")
    assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["database_status"] == "disconnected"


def test_llm_failure_modes_do_not_leak_internals(e2e_client, mock_db, monkeypatch):
    """Verify that LLM errors return sanitized status codes and do not leak stack traces."""
    prefix = get_settings().API_V1_PREFIX
    doc_repo = DocumentRepository(db=mock_db)
    doc = doc_repo.create({
        "source_type": "document",
        "title": "Error Test Doc",
        "text_content": "Some text",
        "status": "completed",
    })

    # Test LLM Authentication Failure (502)
    mock_failing_analysis = MagicMock(spec=MeetingAnalysisService)
    mock_failing_analysis.analyze_meeting.side_effect = LLMAuthenticationError("Invalid API Key for Groq")
    monkeypatch.setattr("app.workflows.meeting_workflow.get_meeting_analysis_service", lambda: mock_failing_analysis)

    wf_resp = e2e_client.post(
        f"{prefix}/workflows/run-sync",
        json={"source_type": "document", "source_id": doc["id"], "force_reanalyze": True},
    )
    assert wf_resp.status_code == status.HTTP_200_OK  # run-sync returns consolidated result container
    wf_data = wf_resp.json()
    assert wf_data["status"] == "failed"
    assert wf_data["error_stage"] == "meeting_analysis"
    assert "Invalid API Key" in wf_data["error_message"]
    # Ensure no raw stack trace is returned
    assert "Traceback" not in wf_data["error_message"]


def test_not_found_handlers_across_all_entities(e2e_client):
    """Verify 404 responses for non-existent IDs across all entity types."""
    prefix = get_settings().API_V1_PREFIX
    non_existent_id = str(ObjectId())

    assert e2e_client.get(f"{prefix}/transcriptions/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND
    assert e2e_client.get(f"{prefix}/documents/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND
    assert e2e_client.get(f"{prefix}/analysis/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND
    assert e2e_client.get(f"{prefix}/tasks/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND
    assert e2e_client.get(f"{prefix}/workflows/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND
    assert e2e_client.get(f"{prefix}/workflows/{non_existent_id}/result").status_code == status.HTTP_404_NOT_FOUND
