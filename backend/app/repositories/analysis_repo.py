"""Meeting Analysis data repository managing MongoDB CRUD operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database
from app.database import get_database

logger = logging.getLogger(__name__)


def _format_analysis_record(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
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


class AnalysisRepository:
    """Repository managing 'meeting_analyses' MongoDB collection queries and mutations."""

    COLLECTION_NAME = "meeting_analyses"

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
        """Get the 'meeting_analyses' collection."""
        return self.db[self.COLLECTION_NAME]

    def create(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new meeting analysis document into the database.

        Args:
            record_data: Dictionary containing analysis fields.

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
        return _format_analysis_record(payload)  # type: ignore

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single analysis document by its string ID.

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
        return _format_analysis_record(doc)

    def get_by_source_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an analysis document by its associated source record ID.

        Args:
            source_id: Source record ID string.

        Returns:
            Formatted record dictionary or None if not found.
        """
        doc = self.collection.find_one({"source_id": source_id})
        return _format_analysis_record(doc)

    def list_records(
        self,
        skip: int = 0,
        limit: int = 20,
        source_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch a paginated list of analysis records ordered by creation date descending.

        Args:
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            source_type: Optional filter by source type.

        Returns:
            Tuple of (list of formatted records, total matching record count).
        """
        query: Dict[str, Any] = {}
        if source_type:
            query["source_type"] = source_type

        total = self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        items = [_format_analysis_record(doc) for doc in cursor if doc is not None]
        return [item for item in items if item is not None], total

    def delete(self, record_id: str) -> bool:
        """Delete an analysis record by its ID.

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


def get_analysis_repository() -> AnalysisRepository:
    """Dependency helper returning an AnalysisRepository instance."""
    return AnalysisRepository()
