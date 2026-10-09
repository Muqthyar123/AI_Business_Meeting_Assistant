import pytest
import os
from unittest.mock import patch, MagicMock
from desktop.api_client import MeetingApiClient, WorkflowAnalysisResult

def test_submit_meeting_workflow_sync_success():
    client = MeetingApiClient(base_url="http://127.0.0.1:8000")
    
    mock_response_data = {
        "id": "wf_test_12345",
        "status": "completed",
        "current_stage": "finalized",
        "analysis": {
            "meeting_title": "Product Strategy Review",
            "meeting_type": "Strategy",
            "executive_summary": "The team agreed on Q4 roadmap.",
            "key_discussion_points": ["Timeline", "Resources"],
            "decisions_made": ["Launch on Nov 15"],
            "potential_risks": ["Dependency on third-party vendor"],
            "unresolved_questions": ["Budget approval for contractor"],
            "topics_covered": ["Roadmap", "Budget"]
        },
        "tasks": [
            {
                "id": "task_1",
                "title": "Complete staging deployment",
                "owner": "David",
                "priority": "high",
                "deadline": "2026-11-10",
                "status": "pending",
                "evidence_quote": "David will complete staging deployment by Nov 10."
            }
        ],
        "follow_up_plan": {
            "immediate_actions": [{"title": "Send meeting minutes"}],
            "short_term_actions": [{"title": "QA regression testing"}],
            "recommended_agenda_next_meeting": ["Check vendor deliverables"]
        }
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch("requests.post", return_value=mock_resp) as mock_post:
        res = client.submit_meeting_workflow_sync(
            transcript_text="David will complete staging deployment by Nov 10. The team agreed on Q4 roadmap.",
            title="Product Strategy Review"
        )

        assert res.success is True
        assert res.status == "completed"
        assert res.workflow_id == "wf_test_12345"
        assert res.executive_summary == "The team agreed on Q4 roadmap."
        assert len(res.tasks) == 1
        assert res.tasks[0]["owner"] == "David"
        assert len(res.decisions) == 1
        assert res.decisions[0] == "Launch on Nov 15"

        # Verify payload sent to requests.post
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["source_type"] == "direct_text"
        assert kwargs["json"]["source_id"] is None
        assert kwargs["json"]["title"] == "Product Strategy Review"
        assert "David will complete" in kwargs["json"]["text"]

def test_submit_meeting_workflow_sync_backend_failure_status():
    client = MeetingApiClient(base_url="http://127.0.0.1:8000")
    
    mock_failed_data = {
        "id": "wf_test_failed",
        "status": "failed",
        "current_stage": "meeting_analysis",
        "error_details": "Groq LLM rate limit exceeded"
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_failed_data

    with patch("requests.post", return_value=mock_resp):
        res = client.submit_meeting_workflow_sync(
            transcript_text="Some discussion points here.",
            title="Failed Meeting"
        )

        assert res.success is False
        assert res.status == "failed"
        assert "rate limit" in res.error_message.lower()

def test_submit_empty_transcript_validation():
    client = MeetingApiClient(base_url="http://127.0.0.1:8000")
    res = client.submit_meeting_workflow_sync(
        transcript_text="   \n   ",
        title="Empty"
    )
    assert res.success is False
    assert "empty" in res.error_message.lower()

def test_save_local_recovery_transcript():
    client = MeetingApiClient()
    path = client.save_local_recovery_transcript(
        transcript_text="Crucial meeting minutes that must never be lost.",
        title="Executive Sync"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Crucial meeting minutes that must never be lost." in content
    # Cleanup
    try:
        os.remove(path)
    except Exception:
        pass
