"""Unit tests for ActionItemExtractionService and FollowUpPlanningService."""

import json
from unittest.mock import MagicMock
import pytest
from app.schemas.task import TaskPriority, TaskStatus
from app.services.llm_service import (
    BaseLLMProvider,
    LLMOutputParsingError,
)
from app.services.task_service import (
    ActionItemExtractionService,
    FollowUpPlanningService,
    get_action_item_extraction_service,
    get_follow_up_planning_service,
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider returning preset responses."""

    def __init__(self, response_text: str):
        self.response_text = response_text
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock_provider"

    @property
    def model_name(self) -> str:
        return "mock-model"

    def generate_chat_completion(self, messages, temperature=0.2, max_tokens=4000, response_format=None) -> str:
        self.call_count += 1
        return self.response_text


def test_action_item_extraction_service_success():
    """Test successful action item extraction with valid LLM response."""
    sample_json = {
        "tasks": [
            {
                "description": "Deploy backend microservices to AWS ECS",
                "assignee": "Devon",
                "has_missing_assignee": False,
                "due_date": "by Friday",
                "priority": "high",
                "dependencies": ["Finalize Dockerfile multi-stage build"],
                "evidence_excerpt": "Devon committed to deploying microservices by Friday.",
            },
            {
                "description": "Circulate quarterly metrics deck",
                "assignee": None,
                "has_missing_assignee": True,
                "due_date": None,
                "priority": "medium",
                "dependencies": [],
                "evidence_excerpt": "Someone needs to circulate the metrics deck.",
            }
        ]
    }
    provider = MockLLMProvider(response_text=json.dumps(sample_json))
    service = ActionItemExtractionService(provider=provider)

    result = service.extract_action_items("Sample meeting text")
    assert len(result.tasks) == 2
    assert result.tasks[0].description == "Deploy backend microservices to AWS ECS"
    assert result.tasks[0].assignee == "Devon"
    assert result.tasks[0].priority == TaskPriority.HIGH
    assert result.tasks[1].has_missing_assignee is True


def test_action_item_extraction_service_markdown_code_fences():
    """Test extracting JSON wrapped in markdown ```json ``` code fences."""
    sample_json = {
        "tasks": [
            {
                "description": "Review API documentation",
                "assignee": "Sarah",
                "has_missing_assignee": False,
                "due_date": "2026-10-15",
                "priority": "low",
                "dependencies": [],
                "evidence_excerpt": "Sarah will review the docs.",
            }
        ]
    }
    wrapped_text = f"```json\n{json.dumps(sample_json)}\n```"
    provider = MockLLMProvider(response_text=wrapped_text)
    service = ActionItemExtractionService(provider=provider)

    result = service.extract_action_items("Meeting text with markdown output")
    assert len(result.tasks) == 1
    assert result.tasks[0].assignee == "Sarah"


def test_action_item_extraction_service_malformed_json_raises():
    """Test that malformed JSON response raises LLMOutputParsingError."""
    provider = MockLLMProvider(response_text="Not valid json output")
    service = ActionItemExtractionService(provider=provider)

    with pytest.raises(LLMOutputParsingError, match="LLM returned malformed JSON"):
        service.extract_action_items("Meeting text")


def test_action_item_extraction_service_empty_text_raises():
    """Test that passing empty text raises ValueError."""
    service = ActionItemExtractionService(provider=MockLLMProvider(response_text="{}"))
    with pytest.raises(ValueError, match="empty or contains only whitespace"):
        service.extract_action_items("   ")


def test_follow_up_planning_service_categorization():
    """Test categorization logic of FollowUpPlanningService."""
    service = FollowUpPlanningService()

    tasks = [
        {
            "id": "1",
            "analysis_id": "analysis_1",
            "description": "Critical hotfix deployment",
            "assignee": "Alex",
            "has_missing_assignee": False,
            "due_date": "asap",
            "priority": "high",
            "status": "pending",
            "dependencies": ["Code review approval"],
            "evidence_excerpt": "Alex will deploy asap.",
            "created_at": "2026-10-09T12:00:00Z",
            "updated_at": "2026-10-09T12:00:00Z",
        },
        {
            "id": "2",
            "analysis_id": "analysis_1",
            "description": "Prepare financial forecast for Q1",
            "assignee": "Emma",
            "has_missing_assignee": False,
            "due_date": "2026-11-01",
            "priority": "medium",
            "status": "in_progress",
            "dependencies": [],
            "evidence_excerpt": "Emma to prepare forecast by Nov 1.",
            "created_at": "2026-10-09T12:00:00Z",
            "updated_at": "2026-10-09T12:00:00Z",
        },
        {
            "id": "3",
            "analysis_id": "analysis_1",
            "description": "Investigate database latency spike",
            "assignee": None,
            "has_missing_assignee": True,
            "due_date": None,
            "priority": "unknown",
            "status": "pending",
            "dependencies": [],
            "evidence_excerpt": "Need to investigate DB latency.",
            "created_at": "2026-10-09T12:00:00Z",
            "updated_at": "2026-10-09T12:00:00Z",
        },
        {
            "id": "4",
            "analysis_id": "analysis_1",
            "description": "Already completed task",
            "assignee": "John",
            "has_missing_assignee": False,
            "due_date": "Yesterday",
            "priority": "high",
            "status": "completed",
            "dependencies": [],
            "evidence_excerpt": "Completed.",
            "created_at": "2026-10-09T12:00:00Z",
            "updated_at": "2026-10-09T12:00:00Z",
        },
    ]

    analysis_doc = {
        "id": "analysis_1",
        "unresolved_questions": ["What is the total cloud budget cap?"],
        "risks_and_blockers": ["DevOps capacity bottleneck"],
    }

    plan = service.generate_plan(
        analysis_id="analysis_1",
        tasks=tasks,
        analysis_record=analysis_doc,
    )

    # Check immediate actions (task 1 is high priority and asap)
    assert len(plan.immediate_actions) == 1
    assert plan.immediate_actions[0].id == "1"

    # Check upcoming tasks (task 2 has explicit deadline)
    assert len(plan.upcoming_tasks) == 1
    assert plan.upcoming_tasks[0].id == "2"

    # Check clarification needed (task 3 is unassigned and has no deadline)
    assert len(plan.clarification_needed) >= 1
    assert any(t.id == "3" for t in plan.clarification_needed)

    # Check blockers and dependencies (task 1 has dependencies)
    assert len(plan.blockers_and_dependencies) == 1
    assert plan.blockers_and_dependencies[0].id == "1"

    # Check pending decisions
    assert "What is the total cloud budget cap?" in plan.pending_decisions
    assert "Risk: DevOps capacity bottleneck" in plan.pending_decisions

    # Check AI suggestions generated
    assert len(plan.ai_suggestions) > 0

    # Verify completed task 4 was excluded from active categories
    all_categorized_ids = [
        t.id for t in plan.immediate_actions + plan.upcoming_tasks + plan.clarification_needed
    ]
    assert "4" not in all_categorized_ids


def test_service_singletons():
    """Verify singleton accessor functions return valid service instances."""
    extraction_service = get_action_item_extraction_service()
    assert isinstance(extraction_service, ActionItemExtractionService)

    planning_service = get_follow_up_planning_service()
    assert isinstance(planning_service, FollowUpPlanningService)
