"""Task and follow-up plan export service supporting JSON, CSV, and Markdown formats."""

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.schemas.task import TaskExportFormat

logger = logging.getLogger(__name__)


class TaskExportService:
    """Service formatting and serializing action items and follow-up plans into exportable file formats."""

    @staticmethod
    def export_to_json(
        tasks: List[Dict[str, Any]],
        plan: Optional[Dict[str, Any]] = None,
        analysis_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Export action items and follow-up plan to a pretty-printed JSON string.

        Args:
            tasks: List of formatted task record dictionaries.
            plan: Optional follow-up plan dictionary.
            analysis_meta: Optional analysis summary metadata dictionary.

        Returns:
            JSON formatted string.
        """
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_tasks": len(tasks),
            "meeting_metadata": analysis_meta or {},
            "tasks": tasks,
            "follow_up_plan": plan or {},
        }

        # Custom serializer for datetime objects
        def default_serializer(obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)

        return json.dumps(payload, indent=2, default=default_serializer)

    @staticmethod
    def export_to_csv(tasks: List[Dict[str, Any]]) -> str:
        """Export action items to RFC 4180 compliant CSV format.

        Args:
            tasks: List of formatted task record dictionaries.

        Returns:
            CSV formatted string with headers and escaped fields.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row
        headers = [
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
        writer.writerow(headers)

        for task in tasks:
            deps = task.get("dependencies", [])
            deps_str = "; ".join(deps) if isinstance(deps, list) else str(deps or "")

            created_val = task.get("created_at")
            if isinstance(created_val, datetime):
                created_str = created_val.isoformat()
            else:
                created_str = str(created_val or "")

            updated_val = task.get("updated_at")
            if isinstance(updated_val, datetime):
                updated_str = updated_val.isoformat()
            else:
                updated_str = str(updated_val or "")

            row = [
                task.get("id", ""),
                task.get("analysis_id", ""),
                task.get("description", ""),
                task.get("assignee") or "Unassigned",
                "Yes" if task.get("has_missing_assignee") else "No",
                task.get("due_date") or "None",
                task.get("priority", "unknown"),
                task.get("status", "pending"),
                deps_str,
                task.get("evidence_excerpt") or "",
                created_str,
                updated_str,
            ]
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def export_to_markdown(
        tasks: List[Dict[str, Any]],
        plan: Optional[Dict[str, Any]] = None,
        analysis_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Export action items and follow-up plan to a structured Markdown document.

        Args:
            tasks: List of formatted task record dictionaries.
            plan: Optional follow-up plan dictionary.
            analysis_meta: Optional meeting analysis metadata.

        Returns:
            Rich GitHub Flavored Markdown document string.
        """
        title = (analysis_meta or {}).get("title") or "Meeting Action Items & Follow-up Plan"
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines: List[str] = [
            f"# {title}",
            f"*Generated on: {generated_at}*",
            "",
            "## Summary Overview",
            "",
        ]

        if analysis_meta and analysis_meta.get("executive_summary"):
            lines.extend([
                f"> **Executive Summary:** {analysis_meta.get('executive_summary')}",
                "",
            ])

        # Task counts breakdown
        total_tasks = len(tasks)
        pending_count = sum(1 for t in tasks if t.get("status") == "pending")
        in_progress_count = sum(1 for t in tasks if t.get("status") == "in_progress")
        completed_count = sum(1 for t in tasks if t.get("status") == "completed")
        cancelled_count = sum(1 for t in tasks if t.get("status") == "cancelled")

        lines.extend([
            "| Total Tasks | Pending | In Progress | Completed | Cancelled |",
            "| :--- | :--- | :--- | :--- | :--- |",
            f"| {total_tasks} | {pending_count} | {in_progress_count} | {completed_count} | {cancelled_count} |",
            "",
            "---",
            "",
            "## Master Action Items Table",
            "",
        ])

        if not tasks:
            lines.extend(["*No action items identified.*", ""])
        else:
            lines.extend([
                "| ID | Task Description | Assignee | Due Date | Priority | Status | Dependencies |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
            ])
            for t in tasks:
                t_id = t.get("id", "")
                short_id = t_id[-6:] if len(t_id) >= 6 else t_id
                desc = t.get("description", "").replace("|", "\\|")
                assignee = t.get("assignee") or ("*(Unassigned)*" if t.get("has_missing_assignee") else "N/A")
                due = t.get("due_date") or "-"
                priority = t.get("priority", "unknown").upper()
                status_val = t.get("status", "pending").replace("_", " ").title()
                deps = t.get("dependencies", [])
                deps_str = "; ".join(deps).replace("|", "\\|") if deps else "-"

                lines.append(f"| `{short_id}` | {desc} | {assignee} | {due} | `{priority}` | {status_val} | {deps_str} |")
            lines.append("")

        # Follow-up Plan Sections if available
        if plan:
            lines.extend([
                "---",
                "",
                "## Follow-up Action Plan",
                "",
            ])

            immediate = plan.get("immediate_actions", [])
            lines.append("### ⚡ Immediate Actions (Urgent / High Priority)")
            if immediate:
                for item in immediate:
                    desc = item.get("description") if isinstance(item, dict) else getattr(item, "description", "")
                    assignee = item.get("assignee") if isinstance(item, dict) else getattr(item, "assignee", "")
                    owner = f" (Owner: **{assignee}**)" if assignee else " *(Needs Owner)*"
                    lines.append(f"- [ ] **{desc}**{owner}")
            else:
                lines.append("*No immediate high-priority actions.*")
            lines.append("")

            upcoming = plan.get("upcoming_tasks", [])
            lines.append("### 📅 Upcoming Scheduled Tasks")
            if upcoming:
                for item in upcoming:
                    desc = item.get("description") if isinstance(item, dict) else getattr(item, "description", "")
                    due = item.get("due_date") if isinstance(item, dict) else getattr(item, "due_date", "")
                    lines.append(f"- [ ] {desc} — *Deadline: {due}*")
            else:
                lines.append("*No scheduled upcoming tasks.*")
            lines.append("")

            clarification = plan.get("clarification_needed", [])
            lines.append("### ⚠️ Clarification Needed (Missing Owner or Deadline)")
            if clarification:
                for item in clarification:
                    desc = item.get("description") if isinstance(item, dict) else getattr(item, "description", "")
                    lines.append(f"- ❓ **{desc}**")
            else:
                lines.append("*All active tasks have designated owners and deadlines.*")
            lines.append("")

            blockers = plan.get("blockers_and_dependencies", [])
            lines.append("### 🚧 Blockers & Prerequisite Dependencies")
            if blockers:
                for item in blockers:
                    desc = item.get("description") if isinstance(item, dict) else getattr(item, "description", "")
                    deps = item.get("dependencies", []) if isinstance(item, dict) else getattr(item, "dependencies", [])
                    lines.append(f"- **{desc}**")
                    for d in deps:
                        lines.append(f"  - Prerequisite: *{d}*")
            else:
                lines.append("*No blockers or dependencies reported.*")
            lines.append("")

            decisions = plan.get("pending_decisions", [])
            lines.append("### ❓ Pending Decisions & Open Questions")
            if decisions:
                for d in decisions:
                    lines.append(f"- {d}")
            else:
                lines.append("*No unresolved questions or pending decisions.*")
            lines.append("")

            suggestions = plan.get("ai_suggestions", [])
            lines.append("### 💡 AI Recommendations for Execution")
            if suggestions:
                for s in suggestions:
                    lines.append(f"- 💡 {s}")
            lines.append("")

        # Source Excerpts
        has_excerpts = any(t.get("evidence_excerpt") for t in tasks)
        if has_excerpts:
            lines.extend([
                "---",
                "",
                "## Supporting Evidence Excerpts",
                "",
            ])
            for t in tasks:
                excerpt = t.get("evidence_excerpt")
                if excerpt:
                    t_id = t.get("id", "")
                    short_id = t_id[-6:] if len(t_id) >= 6 else t_id
                    desc = t.get("description", "")
                    lines.extend([
                        f"**Task [`{short_id}`] {desc}**",
                        f"> \"{excerpt}\"",
                        "",
                    ])

        return "\n".join(lines)


# Global singleton instance holder for TaskExportService
_task_export_service: Optional[TaskExportService] = None


def get_task_export_service() -> TaskExportService:
    """Retrieve or initialize the global TaskExportService singleton."""
    global _task_export_service
    if _task_export_service is None:
        _task_export_service = TaskExportService()
    return _task_export_service
