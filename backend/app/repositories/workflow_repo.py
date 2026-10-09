"""Workflow execution run repository managing MongoDB persistence."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from bson.errors import InvalidId
import pymongo
from pymongo.database import Database
from app.database import get_database

logger = logging.getLogger(__name__)


def format_workflow_record(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
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


class WorkflowRepository:
    """Repository managing 'workflows' MongoDB collection queries and mutations."""

    COLLECTION_NAME = "workflows"

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
        """Get the 'workflows' collection."""
        return self.db[self.COLLECTION_NAME]

    def create(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new workflow execution run document.

        Args:
            record_data: Dictionary containing workflow run attributes.

        Returns:
            Inserted record formatted with string 'id'.
        """
        now = datetime.now(timezone.utc)
        payload = dict(record_data)
        if "created_at" not in payload:
            payload["created_at"] = now
        if "updated_at" not in payload:
            payload["updated_at"] = now
        if "status" not in payload:
            payload["status"] = "queued"
        if "current_stage" not in payload:
            payload["current_stage"] = "queued"
        if "analysis_id" not in payload:
            payload["analysis_id"] = None
        if "error_stage" not in payload:
            payload["error_stage"] = None
        if "error_message" not in payload:
            payload["error_message"] = None
        if "started_at" not in payload:
            payload["started_at"] = None
        if "completed_at" not in payload:
            payload["completed_at"] = None

        result = self.collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return format_workflow_record(payload)  # type: ignore

    def get_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single workflow document by its string ID.

        Args:
            workflow_id: Hexadecimal string representing MongoDB ObjectId.

        Returns:
            Formatted record dictionary or None if not found or ID is invalid.
        """
        try:
            obj_id = ObjectId(workflow_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format requested for workflow: %s", workflow_id)
            return None

        doc = self.collection.find_one({"_id": obj_id})
        return format_workflow_record(doc)

    def update(self, workflow_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields of an existing workflow document.

        Args:
            workflow_id: Hexadecimal string representing MongoDB ObjectId.
            update_data: Fields to update.

        Returns:
            Updated document or None if not found or ID is invalid.
        """
        try:
            obj_id = ObjectId(workflow_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format for workflow update: %s", workflow_id)
            return None

        payload = {k: v for k, v in update_data.items() if v is not None}
        payload["updated_at"] = datetime.now(timezone.utc)

        doc = self.collection.find_one_and_update(
            {"_id": obj_id},
            {"$set": payload},
            return_document=pymongo.ReturnDocument.AFTER,
        )
        return format_workflow_record(doc)

    def update_stage_and_status(
        self,
        workflow_id: str,
        stage: str,
        status: Optional[str] = None,
        analysis_id: Optional[str] = None,
        error_stage: Optional[str] = None,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update workflow progress stage, lifecycle status, and error states.

        Args:
            workflow_id: Hexadecimal string representing MongoDB ObjectId.
            stage: Current workflow stage name.
            status: Optional workflow lifecycle status.
            analysis_id: Optional created or reused analysis record ID.
            error_stage: Optional stage where an error occurred.
            error_message: Optional safe error description.
            started_at: Optional start timestamp.
            completed_at: Optional completion timestamp.

        Returns:
            Updated workflow record dictionary.
        """
        update_dict: Dict[str, Any] = {"current_stage": stage}
        if status is not None:
            update_dict["status"] = status
        if analysis_id is not None:
            update_dict["analysis_id"] = analysis_id
        if error_stage is not None:
            update_dict["error_stage"] = error_stage
        if error_message is not None:
            update_dict["error_message"] = error_message
        if started_at is not None:
            update_dict["started_at"] = started_at
        if completed_at is not None:
            update_dict["completed_at"] = completed_at

        return self.update(workflow_id, update_dict)

    def list_workflows(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch a paginated list of workflow run records ordered by creation date descending.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            status: Optional filter by workflow status.
            source_type: Optional filter by source type.

        Returns:
            Tuple of (list of formatted workflow records, total count).
        """
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if source_type:
            query["source_type"] = source_type

        total = self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        items = [format_workflow_record(doc) for doc in cursor if doc is not None]
        return [item for item in items if item is not None], total

    def delete(self, workflow_id: str) -> bool:
        """Delete a workflow record by its ID.

        Args:
            workflow_id: Hexadecimal string representing MongoDB ObjectId.

        Returns:
            True if a document was deleted, False otherwise.
        """
        try:
            obj_id = ObjectId(workflow_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format for workflow deletion: %s", workflow_id)
            return False

        result = self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0


def get_workflow_repository() -> WorkflowRepository:
    """Dependency helper returning a WorkflowRepository instance."""
    return WorkflowRepository()
