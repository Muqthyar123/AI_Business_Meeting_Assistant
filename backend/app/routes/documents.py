"""Document and pasted text ingestion API endpoints."""

import logging
import math
import os
from pathlib import Path
from typing import Optional
import uuid
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pymongo.errors import PyMongoError
from app.config import Settings, get_settings
from app.repositories.document_repo import (
    DocumentRepository,
    get_document_repository,
)
from app.schemas.document import (
    DocumentListResponse,
    DocumentProcessingStatus,
    DocumentResponse,
    DocumentSourceType,
    PastedTextInput,
)
from app.services.document_service import (
    CorruptDocumentError,
    DocumentExtractionError,
    DocumentExtractionService,
    EmptyDocumentError,
    NoExtractableTextError,
    UnsupportedDocumentFormatError,
    get_document_extraction_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and extract text from document (PDF, DOCX, TXT)",
    description=(
        "Upload a meeting document (text-based PDF, DOCX, or TXT file). "
        "Extracts and normalizes text content synchronously and persists the document record."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (.pdf, .docx, .txt)"),
    title: Optional[str] = Form(default=None, description="Optional custom title for the document"),
    settings: Settings = Depends(get_settings),
    doc_service: DocumentExtractionService = Depends(get_document_extraction_service),
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    """Validate file, extract and normalize text synchronously, and store document metadata."""
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document file provided or filename is missing.",
        )

    original_filename = file.filename.strip()
    ext = Path(original_filename).suffix.lower()

    if ext not in doc_service.SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(doc_service.SUPPORTED_EXTENSIONS.keys()))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported document format '{ext}'. Allowed formats: {allowed}",
        )

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    temp_filepath = os.path.join(settings.UPLOAD_DIR, safe_filename)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1MB buffer

    try:
        # Stream and save file chunks with size check
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

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded document file is empty (0 bytes).",
            )

        # Read file bytes for extraction
        with open(temp_filepath, "rb") as f_in:
            file_bytes = f_in.read()

        extracted_text, source_type = doc_service.extract_document(
            filename=original_filename,
            file_bytes=file_bytes,
        )

    except HTTPException:
        raise
    except UnsupportedDocumentFormatError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EmptyDocumentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NoExtractableTextError as e:
        raise HTTPException(status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422), detail=str(e))
    except CorruptDocumentError as e:
        raise HTTPException(status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422), detail=str(e))
    except Exception as e:
        logger.error("Unexpected error during document ingestion: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the uploaded document.",
        )
    finally:
        # Clean up temporary disk file
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception as e:
                logger.warning("Failed to remove temporary document file '%s': %s", temp_filepath, str(e))

    # Persist extracted document metadata
    char_count = len(extracted_text)
    word_count = len(extracted_text.split())

    try:
        record = repo.create({
            "source_type": source_type.value,
            "title": title or original_filename,
            "original_filename": original_filename,
            "file_format": ext.lstrip("."),
            "file_size_bytes": total_bytes,
            "text_content": extracted_text,
            "character_count": char_count,
            "word_count": word_count,
            "status": DocumentProcessingStatus.COMPLETED.value,
            "error_message": None,
        })
    except PyMongoError as e:
        logger.error("Database failure while saving document record: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable. Could not save document record.",
        )

    return DocumentResponse(**record)


@router.post(
    "/text",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit pasted meeting notes or text",
    description="Submit raw pasted meeting notes or transcript text as JSON for normalization and persistence.",
)
def submit_pasted_text(
    payload: PastedTextInput,
    doc_service: DocumentExtractionService = Depends(get_document_extraction_service),
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    """Normalize and persist pasted meeting notes text."""
    normalized_text = doc_service.normalize_text(payload.text)
    if not normalized_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pasted text is empty or contains only whitespace.",
        )

    char_count = len(normalized_text)
    word_count = len(normalized_text.split())

    try:
        record = repo.create({
            "source_type": DocumentSourceType.PASTED_TEXT.value,
            "title": payload.title or "Pasted Meeting Notes",
            "original_filename": None,
            "file_format": None,
            "file_size_bytes": len(payload.text.encode("utf-8")),
            "text_content": normalized_text,
            "character_count": char_count,
            "word_count": word_count,
            "status": DocumentProcessingStatus.COMPLETED.value,
            "error_message": None,
        })
    except PyMongoError as e:
        logger.error("Database failure while saving pasted text: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable. Could not save text record.",
        )

    return DocumentResponse(**record)


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List ingested documents and text",
    description="Retrieve a paginated list of ingested documents and pasted text records.",
)
def list_documents(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    source_type: Optional[DocumentSourceType] = Query(
        default=None, description="Optional filter by document source type"
    ),
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentListResponse:
    """Fetch paginated document records."""
    skip = (page - 1) * page_size
    items_raw, total = repo.list_records(
        skip=skip,
        limit=page_size,
        source_type=source_type.value if source_type else None,
    )

    items = [DocumentResponse(**item) for item in items_raw]
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details and extracted text",
    description="Retrieve the complete extracted text and metadata for a specific document ID.",
)
def get_document(
    document_id: str,
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    """Fetch a single document record by its ID."""
    doc = repo.get_by_id(document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document record '{document_id}' was not found.",
        )
    return DocumentResponse(**doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ingested document record",
    description="Remove a document record and its extracted text from the database.",
)
def delete_document(
    document_id: str,
    repo: DocumentRepository = Depends(get_document_repository),
) -> None:
    """Delete a document record by its ID."""
    deleted = repo.delete(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document record '{document_id}' was not found.",
        )
    return None
