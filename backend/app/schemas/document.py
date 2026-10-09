"""Pydantic schemas for Document and Pasted Text Ingestion."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentSourceType(str, Enum):
    """Supported document ingestion source types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    PASTED_TEXT = "pasted_text"


class DocumentProcessingStatus(str, Enum):
    """Processing status for document ingestion."""

    COMPLETED = "completed"
    FAILED = "failed"


class PastedTextInput(BaseModel):
    """Payload for submitting pasted meeting notes or text."""

    text: str = Field(
        ...,
        min_length=1,
        description="Pasted meeting notes or transcript text content",
    )
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional title or label for the meeting notes",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Weekly Engineering Sync Notes",
                "text": "Discussed Q4 roadmap priorities and database migration milestones.",
            }
        }
    )


class DocumentResponse(BaseModel):
    """Structured response model for ingested documents and text."""

    id: str = Field(description="Unique document record identifier (hex string)")
    source_type: DocumentSourceType = Field(description="Source format or type of document")
    title: Optional[str] = Field(default=None, description="Document title or original filename")
    original_filename: Optional[str] = Field(
        default=None,
        description="Original uploaded filename (None for pasted text)",
    )
    file_format: Optional[str] = Field(
        default=None,
        description="File format extension (pdf, docx, txt) or None",
    )
    file_size_bytes: Optional[int] = Field(
        default=None,
        description="Uploaded file size in bytes (None for pasted text)",
    )
    text_content: str = Field(description="Full extracted and normalized text content")
    character_count: int = Field(description="Total character count in extracted text")
    word_count: int = Field(description="Total word count in extracted text")
    status: DocumentProcessingStatus = Field(
        default=DocumentProcessingStatus.COMPLETED,
        description="Extraction processing status",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if document extraction encountered issues",
    )
    created_at: datetime = Field(description="UTC timestamp of document ingestion")
    updated_at: datetime = Field(description="UTC timestamp of last update")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "651a2b3c4d5e6f7a8b9c0d1e",
                "source_type": "pdf",
                "title": "project_requirements.pdf",
                "original_filename": "project_requirements.pdf",
                "file_format": "pdf",
                "file_size_bytes": 45020,
                "text_content": "Project kickoff agenda and requirement specifications...",
                "character_count": 520,
                "word_count": 82,
                "status": "completed",
                "error_message": None,
                "created_at": "2026-10-09T14:30:00Z",
                "updated_at": "2026-10-09T14:30:00Z",
            }
        },
    )


class DocumentListResponse(BaseModel):
    """Paginated collection of ingested document records."""

    items: List[DocumentResponse] = Field(
        default_factory=list,
        description="List of document records for the current page",
    )
    total: int = Field(description="Total count of matching document records")
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
