"""Action items extraction and follow-up planning services."""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.config import get_settings
from app.schemas.task import (
    ActionItemExtractionResult,
    ExtractedTaskItem,
    FollowUpPlanResponse,
    TaskPriority,
    TaskResponse,
    TaskStatus,
)
from app.services.llm_service import (
    BaseLLMProvider,
    LLMOutputParsingError,
    get_llm_provider,
)

logger = logging.getLogger(__name__)

SYSTEM_TASK_EXTRACTION_PROMPT = """You are an expert project manager and executive meeting analyst.
Extract all explicit action items, deliverables, commitments, and assigned tasks from the provided meeting content.

Strict Grounding & Extraction Rules:
1. Task Description: Provide a concise, clear, and actionable description starting with an active verb (e.g., "Prepare", "Deploy", "Review", "Schedule").
2. Assignee: ONLY specify an assignee if an individual person or specific role is explicitly named as the owner in the text. If no clear owner is specified, set "assignee": null and "has_missing_assignee": true. Do NOT invent, assume, or hallucinate names.
3. Due Date: ONLY extract a due date or deadline if explicitly stated in the text (e.g., "by Friday", "by Oct 15", "next sprint"). If no deadline is stated, set "due_date": null.
4. Priority: Categorize priority strictly based on explicit urgency or business impact stated in the text: "high", "medium", "low", or "unknown".
5. Dependencies: List any prerequisite tasks, blockers, or dependencies explicitly mentioned. If none, provide an empty list.
6. Evidence Excerpt: Quote a short, verbatim or near-verbatim excerpt from the text that directly justifies this action item.

Strict Response Format:
You MUST respond with a valid JSON object strictly conforming to:
{
  "tasks": [
    {
      "description": "string",
      "assignee": "string or null",
      "has_missing_assignee": boolean,
      "due_date": "string or null",
      "priority": "low" | "medium" | "high" | "unknown",
      "dependencies": ["string"],
      "evidence_excerpt": "string or null"
    }
  ]
}
"""


class ActionItemExtractionService:
    """Service orchestrating LLM prompt execution and validation for action item extraction."""

    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        """Initialize service with an optional LLM provider instance."""
        self._provider = provider

    @property
    def provider(self) -> BaseLLMProvider:
        """Retrieve the active LLM provider instance."""
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    @staticmethod
    def _parse_llm_json_response(raw_response: str) -> Dict[str, Any]:
        """Parse raw LLM response text into a dictionary, extracting JSON from code blocks if needed."""
        if not raw_response or not raw_response.strip():
            raise LLMOutputParsingError("Received empty response from LLM provider.")

        text = raw_response.strip()

        # Extract content from markdown ```json ``` code fences if present
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            text = json_match.group(1).strip()

        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise LLMOutputParsingError("LLM response did not parse into a JSON dictionary object.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON from LLM response: %s", str(e))
            raise LLMOutputParsingError(
                f"LLM returned malformed JSON output that could not be parsed: {str(e)}"
            ) from e

    def extract_action_items(
        self,
        meeting_text: str,
        provider: Optional[BaseLLMProvider] = None,
    ) -> ActionItemExtractionResult:
        """Extract structured action items from meeting notes or transcripts.

        Args:
            meeting_text: Full meeting transcript or document text.
            provider: Optional custom LLM provider override.

        Returns:
            Validated ActionItemExtractionResult instance.

        Raises:
            ValueError: If input text is empty or whitespace.
            LLMProviderError: If LLM call fails or output is invalid.
        """
        if not meeting_text or not meeting_text.strip():
            raise ValueError("Meeting content is empty or contains only whitespace.")

        active_provider = provider or self.provider
        settings = get_settings()

        messages = [
            {"role": "system", "content": SYSTEM_TASK_EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": f"Please extract all action items from the following meeting content:\n\n---\n{meeting_text.strip()}\n---",
            },
        ]

        logger.info("Executing action item extraction with LLM (length: %d chars)...", len(meeting_text))
        raw_output = active_provider.generate_chat_completion(
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"},
        )

        parsed_dict = self._parse_llm_json_response(raw_output)

        try:
            return ActionItemExtractionResult.model_validate(parsed_dict)
        except Exception as e:
            logger.error("Schema validation failed for extracted action items: %s", str(e))
            raise LLMOutputParsingError(
                f"Extracted action items failed schema validation: {str(e)}"
            ) from e


class FollowUpPlanningService:
    """Service organizing extracted tasks and meeting intelligence into structured follow-up plans."""

    @staticmethod
    def generate_plan(
        analysis_id: str,
        tasks: List[Dict[str, Any]],
        analysis_record: Optional[Dict[str, Any]] = None,
    ) -> FollowUpPlanResponse:
        """Categorize tasks and meeting intelligence into an actionable follow-up plan.

        Args:
            analysis_id: Meeting analysis ID string.
            tasks: List of formatted task record dictionaries.
            analysis_record: Optional parent meeting analysis record dictionary.

        Returns:
            FollowUpPlanResponse structured object.
        """
        immediate_actions: List[TaskResponse] = []
        upcoming_tasks: List[TaskResponse] = []
        clarification_needed: List[TaskResponse] = []
        blockers_and_dependencies: List[TaskResponse] = []

        urgent_keywords = ["urgent", "asap", "immediate", "today", "tomorrow", "blocker", "critical"]

        for task_dict in tasks:
            task_resp = TaskResponse(**task_dict)
            status_val = task_resp.status

            # Only categorize active (non-completed, non-cancelled) tasks for follow-up planning
            is_active = status_val in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]

            if not is_active:
                continue

            # 1. Immediate actions: High priority or explicit urgency keywords
            due_str = (task_resp.due_date or "").lower()
            desc_str = task_resp.description.lower()
            has_urgent_keyword = any(kw in due_str or kw in desc_str for kw in urgent_keywords)

            if task_resp.priority == TaskPriority.HIGH or has_urgent_keyword:
                immediate_actions.append(task_resp)

            # 2. Upcoming tasks: Explicitly scheduled due dates
            if task_resp.due_date and not has_urgent_keyword and task_resp.priority != TaskPriority.HIGH:
                upcoming_tasks.append(task_resp)
            elif task_resp.due_date and task_resp not in immediate_actions:
                upcoming_tasks.append(task_resp)

            # 3. Clarification needed: Missing assignee or missing due date
            if task_resp.has_missing_assignee or task_resp.assignee is None or task_resp.due_date is None:
                clarification_needed.append(task_resp)

            # 4. Blockers and dependencies: Non-empty prerequisite dependencies
            if task_resp.dependencies:
                blockers_and_dependencies.append(task_resp)

        # 5. Pending decisions & unresolved questions
        pending_decisions: List[str] = []
        if analysis_record:
            unresolved = analysis_record.get("unresolved_questions", [])
            for q in unresolved:
                if q and q not in pending_decisions:
                    pending_decisions.append(q)

            risks = analysis_record.get("risks_and_blockers", [])
            for r in risks:
                if r and r not in pending_decisions:
                    pending_decisions.append(f"Risk: {r}")

        # 6. Proactive AI suggestions synthesized from task status distribution
        ai_suggestions: List[str] = []
        unassigned_count = sum(1 for t in tasks if t.get("has_missing_assignee") or t.get("assignee") is None)
        no_deadline_count = sum(1 for t in tasks if not t.get("due_date"))
        high_priority_count = len(immediate_actions)
        blocked_count = len(blockers_and_dependencies)

        if unassigned_count > 0:
            ai_suggestions.append(
                f"Assign dedicated owners to {unassigned_count} unassigned action item(s) to guarantee accountability."
            )
        if no_deadline_count > 0:
            ai_suggestions.append(
                f"Establish target delivery deadlines for {no_deadline_count} task(s) currently missing completion dates."
            )
        if blocked_count > 0:
            ai_suggestions.append(
                f"Review and resolve dependencies on {blocked_count} task(s) to prevent project bottlenecks."
            )
        if high_priority_count > 0:
            ai_suggestions.append(
                f"Schedule a prompt sync on {high_priority_count} immediate high-priority deliverable(s)."
            )
        if len(tasks) == 0:
            ai_suggestions.append("No explicit action items were identified in this meeting.")
        elif unassigned_count == 0 and no_deadline_count == 0 and blocked_count == 0:
            ai_suggestions.append("All action items have assigned owners and targets; proceed with regular check-ins.")

        return FollowUpPlanResponse(
            analysis_id=analysis_id,
            immediate_actions=immediate_actions,
            upcoming_tasks=upcoming_tasks,
            clarification_needed=clarification_needed,
            blockers_and_dependencies=blockers_and_dependencies,
            pending_decisions=pending_decisions,
            ai_suggestions=ai_suggestions,
            total_tasks=len(tasks),
            generated_at=datetime.now(timezone.utc),
        )


# Global singleton instance holders
_action_item_extraction_service: Optional[ActionItemExtractionService] = None
_follow_up_planning_service: Optional[FollowUpPlanningService] = None


def get_action_item_extraction_service() -> ActionItemExtractionService:
    """Retrieve or initialize the global ActionItemExtractionService singleton."""
    global _action_item_extraction_service
    if _action_item_extraction_service is None:
        _action_item_extraction_service = ActionItemExtractionService()
    return _action_item_extraction_service


def get_follow_up_planning_service() -> FollowUpPlanningService:
    """Retrieve or initialize the global FollowUpPlanningService singleton."""
    global _follow_up_planning_service
    if _follow_up_planning_service is None:
        _follow_up_planning_service = FollowUpPlanningService()
    return _follow_up_planning_service
