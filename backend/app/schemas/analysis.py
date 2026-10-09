"""Pydantic schemas for AI Meeting Analysis structured extraction."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalysisSourceType(str, Enum):
    """Source origin for meeting analysis."""

    TRANSCRIPTION = "transcription"
    DOCUMENT = "document"
    PASTED_TEXT = "pasted_text"
    DIRECT_TEXT = "direct_text"


class AnalysisStatus(str, Enum):
    """Lifecycle processing status of an analysis job."""

    COMPLETED = "completed"
    FAILED = "failed"


class MeetingAnalysisResult(BaseModel):
    """Validated structured intelligence output extracted from meeting text."""

    executive_summary: str = Field(
        description="Comprehensive executive summary synthesizing the entire meeting context"
    )
    meeting_purpose: str = Field(
        description="Clear statement of the meeting's primary objective and purpose"
    )
    key_discussion_points: List[str] = Field(
        default_factory=list,
        description="List of primary topics and significant points debated or reviewed",
    )
    decisions_made: List[str] = Field(
        default_factory=list,
        description="Explicitly confirmed decisions, distinguishing from tentative suggestions",
    )
    risks_and_blockers: List[str] = Field(
        default_factory=list,
        description="Identified operational, technical, or business risks and bottlenecks",
    )
    unresolved_questions: List[str] = Field(
        default_factory=list,
        description="Questions left open, pending further investigation, or unresolved discussions",
    )
    topics_and_themes: List[str] = Field(
        default_factory=list,
        description="High-level themes, categories, or functional areas discussed",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "executive_summary": "The leadership team reviewed Q3 performance and approved the cloud migration timeline.",
                "meeting_purpose": "Align on Q4 engineering objectives and finalize infrastructure budget allocation.",
                "key_discussion_points": [
                    "AWS vs Azure cost comparison for backend microservices.",
                    "Database read throughput scaling during peak traffic hours.",
                ],
                "decisions_made": [
                    "Approved transition to MongoDB Atlas for cluster management.",
                    "Postponed mobile client redesign to Q1 2027.",
                ],
                "risks_and_blockers": [
                    "Lead DevOps engineer on leave during staging cutover.",
                ],
                "unresolved_questions": [
                    "Final licensing cost for third-party analytics telemetry tool.",
                ],
                "topics_and_themes": [
                    "Infrastructure",
                    "Budgeting",
                    "Resource Planning",
                ],
            }
        }
    )


class AnalysisCreateRequest(BaseModel):
    """Request payload for triggering meeting analysis on an existing record or raw text."""

    source_id: Optional[str] = Field(
        default=None,
        description="ID of the transcription or document record in MongoDB",
    )
    source_type: AnalysisSourceType = Field(
        default=AnalysisSourceType.TRANSCRIPTION,
        description="Origin of the meeting content ('transcription', 'document', 'direct_text')",
    )
    text: Optional[str] = Field(
        default=None,
        description="Direct meeting text content (required if source_type is 'direct_text')",
    )
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional title for the analysis record",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "source_type": "transcription",
                "title": "Q3 Strategy Meeting Analysis",
            }
        }
    )


class AnalysisResponse(BaseModel):
    """Full saved meeting analysis record."""

    id: str = Field(description="Unique analysis record identifier (hex string)")
    source_id: Optional[str] = Field(default=None, description="Referenced source record ID if any")
    source_type: AnalysisSourceType = Field(description="Source content type")
    title: Optional[str] = Field(default=None, description="Analysis title or meeting subject")
    executive_summary: str = Field(description="Synthesized executive summary")
    meeting_purpose: str = Field(description="Meeting purpose and objectives")
    key_discussion_points: List[str] = Field(default_factory=list, description="Key discussion items")
    decisions_made: List[str] = Field(default_factory=list, description="Explicit decisions made")
    risks_and_blockers: List[str] = Field(default_factory=list, description="Identified risks and blockers")
    unresolved_questions: List[str] = Field(default_factory=list, description="Open and unresolved questions")
    topics_and_themes: List[str] = Field(default_factory=list, description="Themes and core topics")
    llm_provider: str = Field(description="LLM provider name (e.g., groq)")
    llm_model: str = Field(description="LLM model name used for generation")
    status: AnalysisStatus = Field(
        default=AnalysisStatus.COMPLETED,
        description="Analysis processing status",
    )
    error_message: Optional[str] = Field(default=None, description="Error details if analysis failed")
    created_at: datetime = Field(description="UTC timestamp when analysis was generated")
    updated_at: datetime = Field(description="UTC timestamp of last update")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "651a2b3c4d5e6f7a8b9c0d1e",
                "source_id": "651a2b3c4d5e6f7a8b9c0d1e",
                "source_type": "transcription",
                "title": "Q3 Strategy Meeting",
                "executive_summary": "The executive team approved the Q4 roadmap...",
                "meeting_purpose": "Quarterly planning and budget approval",
                "key_discussion_points": ["Budget limits", "Hiring headcount"],
                "decisions_made": ["Approved 5 new engineering hires"],
                "risks_and_blockers": ["Candidate sourcing delays"],
                "unresolved_questions": ["Remote vs hybrid compensation bands"],
                "topics_and_themes": ["Recruiting", "Planning"],
                "llm_provider": "groq",
                "llm_model": "llama-3.3-70b-versatile",
                "status": "completed",
                "error_message": None,
                "created_at": "2026-10-09T14:40:00Z",
                "updated_at": "2026-10-09T14:40:00Z",
            }
        },
    )


class AnalysisListResponse(BaseModel):
    """Paginated collection of meeting analysis records."""

    items: List[AnalysisResponse] = Field(
        default_factory=list,
        description="List of meeting analyses for the current page",
    )
    total: int = Field(description="Total count of matching analysis records")
    page: int = Field(default=1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    total_pages: int = Field(default=1, description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
            }
        }
    )
