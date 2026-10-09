"""Meeting Analysis API endpoints."""

import logging
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.errors import PyMongoError
from app.repositories.analysis_repo import (
    AnalysisRepository,
    get_analysis_repository,
)
from app.repositories.document_repo import (
    DocumentRepository,
    get_document_repository,
)
from app.repositories.transcription_repo import (
    TranscriptionRepository,
    get_transcription_repository,
)
from app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisListResponse,
    AnalysisResponse,
    AnalysisSourceType,
    AnalysisStatus,
)
from app.schemas.transcription import TranscriptionStatus
from app.services.llm_service import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMOutputParsingError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.meeting_analysis_service import (
    MeetingAnalysisService,
    get_meeting_analysis_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])


@router.post(
    "/",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI meeting analysis",
    description=(
        "Analyze a transcribed audio record, ingested document, or raw text using LLM intelligence. "
        "Extracts executive summary, meeting purpose, key discussion points, confirmed decisions, "
        "risks & blockers, unresolved questions, and topics."
    ),
)
def create_meeting_analysis(
    payload: AnalysisCreateRequest,
    analysis_service: MeetingAnalysisService = Depends(get_meeting_analysis_service),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repository),
    transcription_repo: TranscriptionRepository = Depends(get_transcription_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> AnalysisResponse:
    """Validate source record, execute LLM meeting analysis, and persist structured output."""
    meeting_text = ""
    resolved_title: Optional[str] = payload.title

    # 1. Resolve source text based on source_type
    if payload.source_type == AnalysisSourceType.TRANSCRIPTION:
        if not payload.source_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_id is required when source_type is 'transcription'.",
            )
        record = transcription_repo.get_by_id(payload.source_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcription record '{payload.source_id}' was not found.",
            )
        rec_status = record.get("status")
        if rec_status in [TranscriptionStatus.QUEUED.value, TranscriptionStatus.PROCESSING.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transcription job is currently '{rec_status}'. Wait for transcription to complete before analyzing.",
            )
        if rec_status == TranscriptionStatus.FAILED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot analyze a failed transcription record.",
            )
        transcript = record.get("transcript_text")
        if not transcript or not transcript.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcription record has no transcript text to analyze.",
            )
        meeting_text = transcript
        if not resolved_title:
            resolved_title = record.get("original_filename") or "Meeting Transcription Analysis"

    elif payload.source_type == AnalysisSourceType.DOCUMENT:
        if not payload.source_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_id is required when source_type is 'document'.",
            )
        doc = document_repo.get_by_id(payload.source_id)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document record '{payload.source_id}' was not found.",
            )
        content = doc.get("text_content")
        if not content or not content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document record contains no extractable text content.",
            )
        meeting_text = content
        if not resolved_title:
            resolved_title = doc.get("title") or doc.get("original_filename") or "Document Meeting Analysis"

    elif payload.source_type in [AnalysisSourceType.DIRECT_TEXT, AnalysisSourceType.PASTED_TEXT]:
        if not payload.text or not payload.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting text is required when analyzing direct or pasted text.",
            )
        meeting_text = payload.text.strip()
        if not resolved_title:
            resolved_title = "Direct Meeting Notes Analysis"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported analysis source type '{payload.source_type}'.",
        )

    # 2. Execute LLM intelligence extraction
    try:
        analysis_result = analysis_service.analyze_meeting(text=meeting_text)
    except LLMConfigurationError as e:
        logger.error("LLM configuration error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except LLMAuthenticationError as e:
        logger.error("LLM authentication error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except LLMRateLimitError as e:
        logger.warning("LLM rate limit: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except LLMTimeoutError as e:
        logger.error("LLM timeout: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e),
        )
    except LLMOutputParsingError as e:
        logger.error("LLM output parsing error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except (LLMProviderError, ValueError) as e:
        logger.error("Analysis execution error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Meeting analysis failed: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error during meeting analysis: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during meeting analysis.",
        )

    # 3. Persist analysis record in MongoDB
    try:
        provider = analysis_service.provider
        record = analysis_repo.create({
            "source_id": payload.source_id,
            "source_type": payload.source_type.value,
            "title": resolved_title,
            "executive_summary": analysis_result.executive_summary,
            "meeting_purpose": analysis_result.meeting_purpose,
            "key_discussion_points": analysis_result.key_discussion_points,
            "decisions_made": analysis_result.decisions_made,
            "risks_and_blockers": analysis_result.risks_and_blockers,
            "unresolved_questions": analysis_result.unresolved_questions,
            "topics_and_themes": analysis_result.topics_and_themes,
            "llm_provider": provider.provider_name,
            "llm_model": provider.model_name,
            "status": AnalysisStatus.COMPLETED.value,
            "error_message": None,
        })
    except PyMongoError as e:
        logger.error("Database persistence failure for meeting analysis: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable. Could not persist analysis.",
        )

    return AnalysisResponse(**record)


@router.get(
    "/",
    response_model=AnalysisListResponse,
    summary="List meeting analyses",
    description="Retrieve a paginated list of generated meeting intelligence reports.",
)
def list_analyses(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    source_type: Optional[AnalysisSourceType] = Query(
        default=None, description="Optional filter by source type"
    ),
    repo: AnalysisRepository = Depends(get_analysis_repository),
) -> AnalysisListResponse:
    """Fetch paginated meeting analysis records."""
    skip = (page - 1) * page_size
    items_raw, total = repo.list_records(
        skip=skip,
        limit=page_size,
        source_type=source_type.value if source_type else None,
    )

    items = [AnalysisResponse(**item) for item in items_raw]
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return AnalysisListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Get meeting analysis details",
    description="Retrieve the complete structured intelligence report for a specific analysis ID.",
)
def get_analysis(
    analysis_id: str,
    repo: AnalysisRepository = Depends(get_analysis_repository),
) -> AnalysisResponse:
    """Fetch a single meeting analysis record by its ID."""
    doc = repo.get_by_id(analysis_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting analysis record '{analysis_id}' was not found.",
        )
    return AnalysisResponse(**doc)


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete meeting analysis record",
    description="Remove a meeting analysis report from the database.",
)
def delete_analysis(
    analysis_id: str,
    repo: AnalysisRepository = Depends(get_analysis_repository),
) -> None:
    """Delete a meeting analysis record by its ID."""
    deleted = repo.delete(analysis_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting analysis record '{analysis_id}' was not found.",
        )
    return None
