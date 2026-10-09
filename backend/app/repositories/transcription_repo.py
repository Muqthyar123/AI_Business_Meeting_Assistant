"""Transcription data repository handling MongoDB CRUD operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database
from app.database import get_database
from app.schemas.transcription import TranscriptionStatus

logger = logging.getLogger(__name__)


def _format_record(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Convert MongoDB BSON document to schema-compatible dictionary with string ID.

    Args:
        doc: Raw MongoDB document dictionary.

    Returns:
        Formatted dictionary with 'id' as a hex string and '_id' removed.
    """
    if doc is None:
        return None
    formatted = dict(doc)
    if "_id" in formatted:
        formatted["id"] = str(formatted.pop("_id"))
    return formatted


class TranscriptionRepository:
    """Repository managing 'transcriptions' MongoDB collection queries and mutations."""

    COLLECTION_NAME = "transcriptions"

    def __init__(self, db: Optional[Database] = None) -> None:
        """Initialize repository with an optional database instance."""
        self._db = db

    @property
    def db(self) -> Database:
        """Get the active database instance, raising an error if unavailable."""
        active_db = self._db if self._db is not None else get_database()
        if active_db is None:
            raise RuntimeError("Database connection is not initialized.")
        return active_db

    @property
    def collection(self):
        """Get the 'transcriptions' collection."""
        return self.db[self.COLLECTION_NAME]

    def create(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new transcription document into the database.

        Args:
            record_data: Dictionary containing transcription attributes.

        Returns:
            Inserted record formatted with string 'id'.
        """
        now = datetime.now(timezone.utc)
        payload = dict(record_data)
        if "created_at" not in payload:
            payload["created_at"] = now
        if "updated_at" not in payload:
            payload["updated_at"] = now

        result = self.collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return _format_record(payload)  # type: ignore

    def create_queued(
        self,
        filename: str,
        file_format: str,
        file_size_bytes: int,
        whisper_model: str,
        requested_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new transcription job with initial 'queued' status.

        Args:
            filename: Original audio filename.
            file_format: Extension / format (e.g., 'mp3', 'wav').
            file_size_bytes: Size of the uploaded file in bytes.
            whisper_model: Configured Whisper model name.
            requested_language: Optional user-specified language code.

        Returns:
            Inserted record dictionary with string 'id'.
        """
        now = datetime.now(timezone.utc)
        record_data: Dict[str, Any] = {
            "original_filename": filename,
            "file_format": file_format,
            "file_size_bytes": file_size_bytes,
            "status": TranscriptionStatus.QUEUED.value,
            "audio_duration": None,
            "requested_language": requested_language,
            "detected_language": None,
            "whisper_model": whisper_model,
            "transcript_text": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
        return self.create(record_data)

    def mark_processing(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Transition transcription job status to 'processing'.

        Args:
            record_id: Hexadecimal string representing MongoDB ObjectId.

        Returns:
            Updated document or None if not found.
        """
        return self.update(record_id, {"status": TranscriptionStatus.PROCESSING.value})

    def mark_completed(
        self,
        record_id: str,
        transcript_text: str,
        detected_language: Optional[str] = None,
        audio_duration: Optional[float] = None,
        whisper_model: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Transition transcription job status to 'completed' with results.

        Args:
            record_id: Hexadecimal string representing MongoDB ObjectId.
            transcript_text: Generated transcription text.
            detected_language: Detected language code.
            audio_duration: Duration of audio in seconds.
            whisper_model: Whisper model name used.

        Returns:
            Updated document or None if not found.
        """
        payload: Dict[str, Any] = {
            "status": TranscriptionStatus.COMPLETED.value,
            "transcript_text": transcript_text,
            "error_message": None,
        }
        if detected_language is not None:
            payload["detected_language"] = detected_language
        if audio_duration is not None:
            payload["audio_duration"] = audio_duration
        if whisper_model is not None:
            payload["whisper_model"] = whisper_model

        return self.update(record_id, payload)

    def mark_failed(self, record_id: str, error_message: str) -> Optional[Dict[str, Any]]:
        """Transition transcription job status to 'failed' with error message.

        Args:
            record_id: Hexadecimal string representing MongoDB ObjectId.
            error_message: Safe error explanation.

        Returns:
            Updated document or None if not found.
        """
        return self.update(
            record_id,
            {
                "status": TranscriptionStatus.FAILED.value,
                "error_message": error_message,
            },
        )

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single transcription document by its string ID.

        Args:
            record_id: Hexadecimal string representing MongoDB ObjectId.

        Returns:
            Formatted record dictionary or None if not found or ID is invalid.
        """
        try:
            obj_id = ObjectId(record_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format requested: %s", record_id)
            return None

        doc = self.collection.find_one({"_id": obj_id})
        return _format_record(doc)

    def list_records(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch a paginated list of transcription documents ordered by creation date descending.

        Args:
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            status: Optional filter by transcription status.

        Returns:
            Tuple of (list of formatted records, total matching record count).
        """
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status

        total = self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        items = [_format_record(doc) for doc in cursor if doc is not None]
        return [item for item in items if item is not None], total

    def update(self, record_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields of an existing transcription document.

        Args:
            record_id: Hexadecimal string representing MongoDB ObjectId.
            update_data: Dictionary of fields to update.

        Returns:
            Updated formatted document or None if document was not found or ID is invalid.
        """
        try:
            obj_id = ObjectId(record_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format for update: %s", record_id)
            return None

        payload = dict(update_data)
        # Ensure updated_at is always refreshed
        payload["updated_at"] = datetime.now(timezone.utc)

        # Do not allow overwriting _id or id in update payload
        payload.pop("_id", None)
        payload.pop("id", None)

        updated_doc = self.collection.find_one_and_update(
            {"_id": obj_id},
            {"$set": payload},
            return_document=True,
        )
        return _format_record(updated_doc)

    def delete(self, record_id: str) -> bool:
        """Delete a transcription record by its ID.

        Args:
            record_id: Hexadecimal string representing MongoDB ObjectId.

        Returns:
            True if a document was deleted, False otherwise.
        """
        try:
            obj_id = ObjectId(record_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format for deletion: %s", record_id)
            return False

        result = self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0


def get_transcription_repository() -> TranscriptionRepository:
    """Dependency helper returning a TranscriptionRepository instance."""
    return TranscriptionRepository()
