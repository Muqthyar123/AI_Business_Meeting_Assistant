"""Action items and task management data repository managing MongoDB CRUD operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from bson.errors import InvalidId
import pymongo
from pymongo.database import Database
from app.database import get_database

logger = logging.getLogger(__name__)


def format_task_record(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
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


class TaskRepository:
    """Repository managing 'tasks' MongoDB collection queries and mutations."""

    COLLECTION_NAME = "tasks"

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
        """Get the 'tasks' collection."""
        return self.db[self.COLLECTION_NAME]

    def create(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single new task document into the database.

        Args:
            record_data: Dictionary containing task fields.

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
            payload["status"] = "pending"
        if "dependencies" not in payload:
            payload["dependencies"] = []
        if "has_missing_assignee" not in payload:
            payload["has_missing_assignee"] = payload.get("assignee") is None

        result = self.collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return format_task_record(payload)  # type: ignore

    def create_many_for_analysis(
        self,
        analysis_id: str,
        tasks_data: List[Dict[str, Any]],
        replace: bool = True,
    ) -> List[Dict[str, Any]]:
        """Batch insert tasks extracted for an analysis, optionally replacing existing tasks.

        Args:
            analysis_id: Associated meeting analysis ID string.
            tasks_data: List of extracted task dictionaries.
            replace: If True, existing tasks associated with this analysis are deleted first.

        Returns:
            List of persisted and formatted task dictionaries.
        """
        if replace:
            deleted_count = self.delete_by_analysis_id(analysis_id)
            logger.info(
                "Regeneration replacement: removed %d previous tasks for analysis '%s'",
                deleted_count,
                analysis_id,
            )

        if not tasks_data:
            return []

        now = datetime.now(timezone.utc)
        documents = []
        for task in tasks_data:
            doc = dict(task)
            doc["analysis_id"] = analysis_id
            if "status" not in doc:
                doc["status"] = "pending"
            if "dependencies" not in doc:
                doc["dependencies"] = []
            if "has_missing_assignee" not in doc:
                doc["has_missing_assignee"] = doc.get("assignee") is None
            doc["created_at"] = now
            doc["updated_at"] = now
            documents.append(doc)

        result = self.collection.insert_many(documents)
        for doc, inserted_id in zip(documents, result.inserted_ids):
            doc["_id"] = inserted_id

        return [format_task_record(doc) for doc in documents if doc is not None]  # type: ignore

    def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single task document by its string ID.

        Args:
            task_id: Hexadecimal string representing MongoDB ObjectId.

        Returns:
            Formatted record dictionary or None if not found or ID is invalid.
        """
        try:
            obj_id = ObjectId(task_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format requested for task: %s", task_id)
            return None

        doc = self.collection.find_one({"_id": obj_id})
        return format_task_record(doc)

    def get_by_analysis_id(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Fetch all tasks associated with a specific meeting analysis ID.

        Args:
            analysis_id: Meeting analysis ID string.

        Returns:
            List of formatted task records ordered by creation date ascending.
        """
        cursor = self.collection.find({"analysis_id": analysis_id}).sort("created_at", 1)
        return [format_task_record(doc) for doc in cursor if doc is not None]  # type: ignore

    def list_tasks(
        self,
        skip: int = 0,
        limit: int = 50,
        analysis_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch a paginated list of tasks filtered by optional criteria.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            analysis_id: Optional filter by parent analysis ID.
            status: Optional filter by task status ('pending', 'in_progress', etc.).
            priority: Optional filter by priority ('low', 'medium', 'high', etc.).
            assignee: Optional filter by exact assignee name.

        Returns:
            Tuple of (list of formatted task records, total matching task count).
        """
        query: Dict[str, Any] = {}
        if analysis_id:
            query["analysis_id"] = analysis_id
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if assignee:
            query["assignee"] = assignee

        total = self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        items = [format_task_record(doc) for doc in cursor if doc is not None]
        return [item for item in items if item is not None], total

    def update(self, task_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields of an existing task document.

        Args:
            task_id: Hexadecimal string representing MongoDB ObjectId.
            update_data: Fields to update.

        Returns:
            Updated task dictionary or None if not found or ID is invalid.
        """
        try:
            obj_id = ObjectId(task_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format for task update: %s", task_id)
            return None

        payload = {k: v for k, v in update_data.items() if v is not None}
        if not payload:
            return self.get_by_id(task_id)

        payload["updated_at"] = datetime.now(timezone.utc)

        doc = self.collection.find_one_and_update(
            {"_id": obj_id},
            {"$set": payload},
            return_document=pymongo.ReturnDocument.AFTER,
        )
        return format_task_record(doc)

    def update_status(self, task_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update only the status of an existing task.

        Args:
            task_id: Hexadecimal string representing MongoDB ObjectId.
            status: New status value.

        Returns:
            Updated task dictionary or None if not found.
        """
        return self.update(task_id, {"status": status})

    def delete(self, task_id: str) -> bool:
        """Delete a task record by its ID.

        Args:
            task_id: Hexadecimal string representing MongoDB ObjectId.

        Returns:
            True if a task was deleted, False otherwise.
        """
        try:
            obj_id = ObjectId(task_id)
        except (InvalidId, TypeError):
            logger.debug("Invalid ObjectId format for task deletion: %s", task_id)
            return False

        result = self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0

    def delete_by_analysis_id(self, analysis_id: str) -> int:
        """Delete all tasks associated with a specific analysis ID.

        Args:
            analysis_id: Meeting analysis ID string.

        Returns:
            Number of deleted task documents.
        """
        result = self.collection.delete_many({"analysis_id": analysis_id})
        return result.deleted_count


def get_task_repository() -> TaskRepository:
    """Dependency helper returning a TaskRepository instance."""
    return TaskRepository()
