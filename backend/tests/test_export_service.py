"""Unit tests for TaskExportService (JSON, CSV, and Markdown exports)."""

import csv
import io
import json
from datetime import datetime, timezone
from app.services.export_service import (
    TaskExportService,
    get_task_export_service,
)


def sample_tasks():
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "670560a12f3e8b1d9c4e5a61",
            "analysis_id": "analysis_123",
            "description": 'Refactor "auth" middleware to support OAuth2',
            "assignee": "Sarah Chen",
            "has_missing_assignee": False,
            "due_date": "by Friday 5 PM",
            "priority": "high",
            "status": "pending",
            "dependencies": ["OAuth provider registration", "Security review"],
            "evidence_excerpt": 'Sarah will refactor "auth" middleware by Friday 5 PM.',
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "670560a12f3e8b1d9c4e5a62",
            "analysis_id": "analysis_123",
            "description": "Send meeting recap notes, including budget table",
            "assignee": None,
            "has_missing_assignee": True,
            "due_date": None,
            "priority": "low",
            "status": "in_progress",
            "dependencies": [],
            "evidence_excerpt": "Need to send recap notes.",
            "created_at": now,
            "updated_at": now,
        },
    ]


def test_export_to_json():
    """Test exporting tasks and follow-up plan to JSON format."""
    service = TaskExportService()
    tasks = sample_tasks()
    meta = {"title": "Architecture Sync", "executive_summary": "Discussed auth and budget."}
    plan = {"immediate_actions": [{"description": "Action 1"}], "ai_suggestions": ["Assign owner"]}

    json_str = service.export_to_json(tasks=tasks, plan=plan, analysis_meta=meta)
    parsed = json.loads(json_str)

    assert parsed["total_tasks"] == 2
    assert parsed["meeting_metadata"]["title"] == "Architecture Sync"
    assert len(parsed["tasks"]) == 2
    assert parsed["follow_up_plan"]["ai_suggestions"] == ["Assign owner"]


def test_export_to_csv():
    """Test exporting tasks to RFC 4180 compliant CSV format with proper quoting and escaping."""
    service = TaskExportService()
    tasks = sample_tasks()

    csv_str = service.export_to_csv(tasks=tasks)
    reader = csv.reader(io.StringIO(csv_str))
    rows = list(reader)

    # Check header
    header = rows[0]
    assert header == [
        "Task ID",
        "Analysis ID",
        "Description",
        "Assignee",
        "Needs Assignee",
        "Due Date",
        "Priority",
        "Status",
        "Dependencies",
        "Evidence Excerpt",
        "Created At",
        "Updated At",
    ]

    assert len(rows) == 3  # 1 header + 2 tasks

    # First task row
    row1 = rows[1]
    assert row1[0] == "670560a12f3e8b1d9c4e5a61"
    assert row1[2] == 'Refactor "auth" middleware to support OAuth2'
    assert row1[3] == "Sarah Chen"
    assert row1[4] == "No"
    assert row1[5] == "by Friday 5 PM"
    assert row1[6] == "high"
    assert row1[7] == "pending"
    assert row1[8] == "OAuth provider registration; Security review"

    # Second task row
    row2 = rows[2]
    assert row2[2] == "Send meeting recap notes, including budget table"
    assert row2[3] == "Unassigned"
    assert row2[4] == "Yes"
    assert row2[5] == "None"


def test_export_to_markdown():
    """Test exporting tasks and follow-up plan to rich Markdown format."""
    service = TaskExportService()
    tasks = sample_tasks()
    meta = {"title": "Architecture Sync", "executive_summary": "Discussed auth and budget."}
    plan = {
        "immediate_actions": [{"description": "Action 1", "assignee": "Sarah"}],
        "upcoming_tasks": [],
        "clarification_needed": [{"description": "Action 2"}],
        "blockers_and_dependencies": [],
        "pending_decisions": ["Decide on budget cap"],
        "ai_suggestions": ["Assign owner to unassigned task"],
    }

    md_str = service.export_to_markdown(tasks=tasks, plan=plan, analysis_meta=meta)

    assert "# Architecture Sync" in md_str
    assert "## Summary Overview" in md_str
    assert "## Master Action Items Table" in md_str
    assert "## Follow-up Action Plan" in md_str
    assert "⚡ Immediate Actions" in md_str
    assert "💡 AI Recommendations for Execution" in md_str
    assert "Supporting Evidence Excerpts" in md_str


def test_export_service_singleton():
    """Verify get_task_export_service singleton helper."""
    service = get_task_export_service()
    assert isinstance(service, TaskExportService)
