"""Transcription API endpoints and router configuration."""

import logging
import math
import os
from pathlib import Path
from typing import Optional
import uuid
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from app.config import Settings, get_settings
from app.repositories.transcription_repo import (
    TranscriptionRepository,
    get_transcription_repository,
)
from app.schemas.transcription import (
    TranscriptionCreateResponse,
    TranscriptionListResponse,
    TranscriptionResponse,
    TranscriptionStatus,
    TranscriptionUpdateRequest,
)
from app.services.transcription_worker import process_transcription_job
from app.services.whisper_service import (
    WhisperService,
    get_whisper_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["transcriptions"])

# Supported audio extensions compatible with FFmpeg & Whisper
SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".webm",
    ".ogg",
    ".flac",
    ".wma",
}


@router.post(
    "/upload",
    response_model=TranscriptionCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload recorded audio for transcription",
    description=(
        "Upload a recorded audio file (e.g. .mp3, .wav, .m4a, .webm) for speech-to-text processing. "
        "Returns a job ID and queues local OpenAI Whisper transcription in the background."
    ),
)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Recorded audio file to transcribe"),
    language: Optional[str] = Form(
        default=None,
        description="Optional ISO 639-1 language code (e.g., 'en', 'es', 'te') to guide transcription",
    ),
    settings: Settings = Depends(get_settings),
    repo: TranscriptionRepository = Depends(get_transcription_repository),
    whisper_service: WhisperService = Depends(get_whisper_service),
) -> TranscriptionCreateResponse:
    """Handle audio upload, stream to temporary disk storage, create database record, and queue background job."""

    # 1. Validate presence of file and filename
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file provided or filename is missing.",
        )

    original_filename = file.filename.strip()
    ext = Path(original_filename).suffix.lower()

    # 2. Validate file extension
    if ext not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported audio format '{ext}'. "
                f"Allowed formats: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
            ),
        )

    # 3. Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 4. Generate safe temporary filename
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    temp_filepath = os.path.join(settings.UPLOAD_DIR, safe_filename)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1MB buffer

    # 5. Stream and write chunks to disk while enforcing max file size
    try:
        with open(temp_filepath, "wb") as f_out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                        detail=f"File exceeds maximum allowed upload size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                    )
                f_out.write(chunk)
    except HTTPException:
        # Clean up partial file on size limit error
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise
    except Exception as e:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        logger.error("Error writing uploaded file '%s': %s", temp_filepath, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving the uploaded audio file.",
        )

    # 6. Reject empty files (0 bytes)
    if total_bytes == 0:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty (0 bytes).",
        )

    # 7. Create database record with status 'queued'
    try:
        record = repo.create_queued(
            filename=original_filename,
            file_format=ext.lstrip("."),
            file_size_bytes=total_bytes,
            whisper_model=settings.WHISPER_MODEL,
            requested_language=language,
        )
    except Exception as e:
        # Clean up temp file on database failure
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        logger.error("Failed to create database record for upload: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable. Could not queue transcription.",
        )

    record_id = str(record["id"])

    # 8. Dispatch non-blocking background task
    background_tasks.add_task(
        process_transcription_job,
        record_id=record_id,
        temp_audio_path=temp_filepath,
        requested_language=language,
        whisper_model=settings.WHISPER_MODEL,
        repo=repo,
        whisper_service=whisper_service,
    )

    logger.info("Queued transcription job '%s' for file '%s'.", record_id, original_filename)

    return TranscriptionCreateResponse(
        job_id=record_id,
        status=TranscriptionStatus.QUEUED,
        message="Audio accepted for transcription",
    )


@router.get(
    "/",
    response_model=TranscriptionListResponse,
    summary="List transcription history",
    description="Retrieve a paginated list of recorded transcription jobs ordered chronologically.",
)
def list_transcriptions(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[TranscriptionStatus] = Query(
        default=None, alias="status", description="Optional status filter"
    ),
    repo: TranscriptionRepository = Depends(get_transcription_repository),
) -> TranscriptionListResponse:
    """Fetch paginated transcription records."""
    skip = (page - 1) * page_size
    items_raw, total = repo.list_records(
        skip=skip,
        limit=page_size,
        status=status_filter.value if status_filter else None,
    )

    items = [TranscriptionResponse(**item) for item in items_raw]
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return TranscriptionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{record_id}",
    response_model=TranscriptionResponse,
    summary="Get transcription details",
    description="Retrieve the complete details, status, and generated transcript for a specific record ID.",
)
def get_transcription(
    record_id: str,
    repo: TranscriptionRepository = Depends(get_transcription_repository),
) -> TranscriptionResponse:
    """Fetch a single transcription record by its ID."""
    doc = repo.get_by_id(record_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription record '{record_id}' was not found.",
        )
    return TranscriptionResponse(**doc)


@router.patch(
    "/{record_id}",
    response_model=TranscriptionResponse,
    summary="Update transcript text",
    description="Edit the generated transcript text for a specific record.",
)
def update_transcription_text(
    record_id: str,
    payload: TranscriptionUpdateRequest,
    repo: TranscriptionRepository = Depends(get_transcription_repository),
) -> TranscriptionResponse:
    """Update manual edits or corrections to an existing transcript."""
    existing = repo.get_by_id(record_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription record '{record_id}' was not found.",
        )

    update_dict = {}
    if payload.transcript_text is not None:
        update_dict["transcript_text"] = payload.transcript_text

    if not update_dict:
        return TranscriptionResponse(**existing)

    updated_doc = repo.update(record_id, update_dict)
    if updated_doc is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transcription record.",
        )
    return TranscriptionResponse(**updated_doc)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete transcription record",
    description="Remove a transcription record from the database.",
)
def delete_transcription(
    record_id: str,
    repo: TranscriptionRepository = Depends(get_transcription_repository),
) -> None:
    """Delete a transcription record by its ID."""
    deleted = repo.delete(record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription record '{record_id}' was not found.",
        )
    return None
