"""MongoDB connection management and database utilities using PyMongo."""

import logging
from typing import Optional
import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Global database client instance holders
_mongo_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def connect_to_mongo(uri: str, db_name: str, server_selection_timeout_ms: int = 10000) -> Database:
    """Initialize MongoDB connection client, verify connectivity, and return database instance.

    Args:
        uri: MongoDB connection URI string (supports local or MongoDB Atlas).
        db_name: Target database name.
        server_selection_timeout_ms: Timeout in milliseconds for server selection (default: 10000).

    Returns:
        PyMongo Database instance.

    Raises:
        ConnectionFailure: If unable to reach MongoDB.
    """
    global _mongo_client, _database

    try:
        logger.info("Initializing MongoDB client...")
        try:
            import certifi
            ca_file = certifi.where()
        except Exception:
            ca_file = None

        client_kwargs = {
            "serverSelectionTimeoutMS": server_selection_timeout_ms,
            "connectTimeoutMS": server_selection_timeout_ms,
        }
        if ca_file and ("mongodb+srv://" in uri or "ssl=true" in uri.lower() or "tls=true" in uri.lower()):
            client_kwargs["tlsCAFile"] = ca_file

        _mongo_client = MongoClient(
            uri,
            **client_kwargs,
        )
        # Verify connection immediately with a ping command
        _mongo_client.admin.command("ping")
        _database = _mongo_client[db_name]
        logger.info("Successfully connected to MongoDB database '%s'", db_name)
        return _database
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        logger.error("Failed to connect to MongoDB. Ensure MongoDB is running and accessible.")
        _mongo_client = None
        _database = None
        raise ConnectionFailure("Could not connect to MongoDB server.") from e
    except Exception as e:
        logger.error("Unexpected error occurred while connecting to MongoDB.")
        _mongo_client = None
        _database = None
        raise PyMongoError("MongoDB initialization error.") from e


def close_mongo_connection() -> None:
    """Gracefully close the active MongoDB client connection."""
    global _mongo_client, _database
    if _mongo_client is not None:
        try:
            logger.info("Closing MongoDB connection...")
            _mongo_client.close()
            logger.info("MongoDB connection closed successfully.")
        except Exception as e:
            logger.warning("Error encountered while closing MongoDB client: %s", str(e))
        finally:
            _mongo_client = None
            _database = None


def get_database() -> Optional[Database]:
    """Retrieve the active database instance.

    Returns:
        Database instance or None if not connected.
    """
    return _database


def ping_database() -> bool:
    """Check if the active MongoDB connection is healthy and responsive.

    Returns:
        True if database is reachable, False otherwise.
    """
    if _mongo_client is None:
        return False
    try:
        _mongo_client.admin.command("ping")
        return True
    except Exception as e:
        logger.warning("MongoDB ping failed: %s", str(e))
        return False


def init_db_indexes(db: Database) -> None:
    """Create essential indexes idempotently for collections.

    Args:
        db: PyMongo Database instance.
    """
    if db is None:
        logger.warning("Cannot initialize indexes: Database instance is None.")
        return

    try:
        transcriptions = db["transcriptions"]
        # Index on creation timestamp (descending) for fast chronological listing
        transcriptions.create_index([("created_at", pymongo.DESCENDING)], name="idx_created_at_desc")
        # Index on status for status filtering
        transcriptions.create_index([("status", pymongo.ASCENDING)], name="idx_status_asc")

        documents = db["documents"]
        # Index on creation timestamp (descending) for documents chronological listing
        documents.create_index([("created_at", pymongo.DESCENDING)], name="idx_docs_created_at_desc")
        # Index on source_type for filtering
        documents.create_index([("source_type", pymongo.ASCENDING)], name="idx_docs_source_type_asc")

        analyses = db["meeting_analyses"]
        # Index on creation timestamp (descending) for chronological listing
        analyses.create_index([("created_at", pymongo.DESCENDING)], name="idx_analyses_created_at_desc")
        # Index on source_id for quick lookup by parent record
        analyses.create_index([("source_id", pymongo.ASCENDING)], name="idx_analyses_source_id_asc")

        tasks = db["tasks"]
        # Index on analysis_id for querying tasks belonging to an analysis
        tasks.create_index([("analysis_id", pymongo.ASCENDING)], name="idx_tasks_analysis_id_asc")
        # Index on status for status filtering
        tasks.create_index([("status", pymongo.ASCENDING)], name="idx_tasks_status_asc")
        # Index on priority for priority filtering
        tasks.create_index([("priority", pymongo.ASCENDING)], name="idx_tasks_priority_asc")
        # Index on creation timestamp (descending) for chronological task listing
        tasks.create_index([("created_at", pymongo.DESCENDING)], name="idx_tasks_created_at_desc")

        workflows = db["workflows"]
        # Index on creation timestamp (descending) for workflow listing
        workflows.create_index([("created_at", pymongo.DESCENDING)], name="idx_workflows_created_at_desc")
        # Index on status for filtering
        workflows.create_index([("status", pymongo.ASCENDING)], name="idx_workflows_status_asc")
        # Index on source_id for lookup
        workflows.create_index([("source_id", pymongo.ASCENDING)], name="idx_workflows_source_id_asc")
        # Index on analysis_id for lookup
        workflows.create_index([("analysis_id", pymongo.ASCENDING)], name="idx_workflows_analysis_id_asc")

        logger.info("MongoDB indexes verified/created successfully.")
    except Exception as e:
        logger.error("Failed to create database indexes: %s", str(e))
