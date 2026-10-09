import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field

from .config import CONFIG

logger = logging.getLogger(__name__)


@dataclass
class WorkflowAnalysisResult:
    success: bool
    status: str
    workflow_id: Optional[str] = None
    title: Optional[str] = None
    executive_summary: str = ""
    discussion_points: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_plan: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class MeetingApiClient:
    """
    Client for interacting with the AI Business Meeting Assistant FastAPI backend.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0):
        self.base_url = (base_url or CONFIG.BACKEND_URL).rstrip("/")
        self.timeout = timeout

    def check_health(self) -> Tuple[bool, Dict[str, Any]]:
        """Check backend and MongoDB connectivity"""
        url = f"{self.base_url}/api/health"
        try:
            resp = requests.get(url, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                return True, data
            return False, {"error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False, {"error": str(e)}

    def submit_meeting_workflow_sync(
        self,
        transcript_text: str,
        title: Optional[str] = None,
        force_reanalyze: bool = False
    ) -> WorkflowAnalysisResult:
        """
        Submits cumulative meeting transcript to POST /api/workflows/run-sync.
        """
        cleaned_text = transcript_text.strip()
        if not cleaned_text:
            return WorkflowAnalysisResult(
                success=False,
                status="failed",
                error_message="Meeting transcript is empty. Cannot submit empty text to AI backend."
            )

        meeting_title = title or f"Live Meeting - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        url = f"{self.base_url}/api/workflows/run-sync"

        payload = {
            "source_type": "direct_text",
            "source_id": None,
            "text": cleaned_text,
            "title": meeting_title,
            "force_reanalyze": force_reanalyze
        }

        # Save local backup recovery file before making network call
        self.save_local_recovery_transcript(cleaned_text, meeting_title)

        logger.info(f"Submitting meeting workflow sync to {url} ({len(cleaned_text.split())} words)...")

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                err = f"Backend returned HTTP {resp.status_code}: {resp.text}"
                logger.error(err)
                return WorkflowAnalysisResult(
                    success=False,
                    status="failed",
                    error_message=err
                )

            data = resp.json()
            status = data.get("status", "unknown")

            if status == "failed":
                err = data.get("error_details") or data.get("error_message") or "Workflow failed during execution"
                return WorkflowAnalysisResult(
                    success=False,
                    status="failed",
                    workflow_id=data.get("id"),
                    error_message=err,
                    raw_response=data
                )

            # Parse successful result
            analysis_data = data.get("analysis") or {}
            tasks_data = data.get("tasks") or []
            plan_data = data.get("follow_up_plan") or {}

            return WorkflowAnalysisResult(
                success=True,
                status="completed",
                workflow_id=data.get("id"),
                title=analysis_data.get("meeting_title", meeting_title),
                executive_summary=analysis_data.get("executive_summary", ""),
                discussion_points=analysis_data.get("key_discussion_points", []),
                decisions=analysis_data.get("decisions_made", []),
                risks=analysis_data.get("potential_risks", []),
                unresolved_questions=analysis_data.get("unresolved_questions", []),
                topics=analysis_data.get("topics_covered", []),
                tasks=tasks_data,
                follow_up_plan=plan_data,
                raw_response=data
            )

        except requests.exceptions.Timeout:
            err = f"Request to backend timed out after {self.timeout}s. Transcript is safely saved locally."
            logger.error(err)
            return WorkflowAnalysisResult(success=False, status="failed", error_message=err)
        except requests.exceptions.ConnectionError:
            err = f"Could not connect to backend at {self.base_url}. Ensure FastAPI server is running."
            logger.error(err)
            return WorkflowAnalysisResult(success=False, status="failed", error_message=err)
        except Exception as e:
            logger.error(f"Unexpected API error: {e}", exc_info=True)
            return WorkflowAnalysisResult(success=False, status="failed", error_message=str(e))

    def publish_live_segment(
        self,
        text: str,
        timestamp: Optional[str] = None,
        mode: str = "meeting",
        segment_id: Optional[int] = None
    ) -> bool:
        """Publishes a speech segment to /api/stream/publish for live broadcast to React frontend."""
        if not text or not text.strip():
            return False
        url = f"{self.base_url}/api/stream/publish"
        payload = {
            "text": text.strip(),
            "timestamp": timestamp or datetime.now().strftime("%H:%M:%S"),
            "mode": mode,
            "segment_id": segment_id
        }
        try:
            resp = requests.post(url, json=payload, timeout=2.0)
            return resp.status_code == 200
        except Exception as e:
            logger.debug("Failed publishing live segment to backend stream: %s", str(e))
            return False

    def save_local_recovery_transcript(self, transcript_text: str, title: str) -> str:
        """Saves a local backup of the transcript so meeting notes are never lost"""
        try:
            recovery_dir = CONFIG.RECOVERY_DIR
            os.makedirs(recovery_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:40]
            filepath = os.path.join(recovery_dir, f"transcript_{timestamp}_{safe_title}.txt")
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                f.write(transcript_text)
                f.write("\n")
                
            logger.info(f"Local transcript backup saved: {filepath}")
            return filepath
        except Exception as e:
            logger.warning(f"Failed to save local transcript backup: {e}")
            return ""
