"""Workflow execution engine orchestrating LangGraph execution and MongoDB status updates."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.repositories.workflow_repo import (
    WorkflowRepository,
    get_workflow_repository,
)
from app.workflows.meeting_workflow import (
    MeetingWorkflowState,
    build_meeting_workflow_graph,
)

logger = logging.getLogger(__name__)

_compiled_workflow_graph = None


def get_compiled_workflow_graph():
    """Retrieve or compile the singleton LangGraph meeting workflow instance."""
    global _compiled_workflow_graph
    if _compiled_workflow_graph is None:
        _compiled_workflow_graph = build_meeting_workflow_graph()
    return _compiled_workflow_graph


class WorkflowEngine:
    """Engine executing the LangGraph meeting pipeline and persisting status updates."""

    def __init__(self, workflow_repo: Optional[WorkflowRepository] = None) -> None:
        """Initialize workflow engine."""
        self._repo = workflow_repo

    @property
    def repo(self) -> WorkflowRepository:
        """Retrieve active WorkflowRepository instance."""
        if self._repo is None:
            self._repo = get_workflow_repository()
        return self._repo

    def execute_workflow(
        self,
        workflow_id: str,
        initial_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute the LangGraph workflow synchronously or from a background worker.

        Args:
            workflow_id: MongoDB ID of the workflow run document.
            initial_input: Initial parameters (source_type, source_id, text, title, force_reanalyze).

        Returns:
            Final state dictionary of the workflow run.
        """
        now = datetime.now(timezone.utc)
        logger.info("Starting LangGraph workflow execution for run '%s'...", workflow_id)

        # Mark workflow as processing in MongoDB
        self.repo.update_stage_and_status(
            workflow_id=workflow_id,
            stage="input_validation",
            status="processing",
        )

        initial_state: MeetingWorkflowState = {
            "workflow_run_id": workflow_id,
            "source_type": initial_input.get("source_type", "transcription"),
            "source_id": initial_input.get("source_id"),
            "title": initial_input.get("title"),
            "text": initial_input.get("text"),
            "force_reanalyze": initial_input.get("force_reanalyze", False),
            "existing_analysis_id": initial_input.get("existing_analysis_id"),
            "current_stage": "queued",
            "status": "processing",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        graph = get_compiled_workflow_graph()

        try:
            final_state = graph.invoke(initial_state)
        except Exception as e:
            logger.error("Unexpected error during LangGraph graph invocation: %s", str(e))
            error_msg = f"Workflow engine execution failed: {str(e)}"
            self.repo.update_stage_and_status(
                workflow_id=workflow_id,
                stage="failed",
                status="failed",
                error_stage="graph_invocation",
                error_message=error_msg,
                completed_at=datetime.now(timezone.utc),
            )
            return {
                "workflow_run_id": workflow_id,
                "status": "failed",
                "current_stage": "failed",
                "error_stage": "graph_invocation",
                "error_message": error_msg,
            }

        # Update MongoDB with final state
        analysis_id = None
        if final_state.get("analysis_record") and "id" in final_state["analysis_record"]:
            analysis_id = final_state["analysis_record"]["id"]

        is_success = final_state.get("status") == "completed"
        final_status = "completed" if is_success else "failed"
        final_stage = final_state.get("current_stage", "finalized" if is_success else "failed")
        completed_at = datetime.now(timezone.utc)

        self.repo.update_stage_and_status(
            workflow_id=workflow_id,
            stage=final_stage,
            status=final_status,
            analysis_id=analysis_id,
            error_stage=final_state.get("error_stage"),
            error_message=final_state.get("error_message"),
            completed_at=completed_at,
        )

        logger.info(
            "LangGraph workflow '%s' finished with status '%s' at stage '%s'",
            workflow_id,
            final_status,
            final_stage,
        )
        return final_state


_workflow_engine_instance: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Retrieve or initialize the global WorkflowEngine singleton."""
    global _workflow_engine_instance
    if _workflow_engine_instance is None:
        _workflow_engine_instance = WorkflowEngine()
    return _workflow_engine_instance
