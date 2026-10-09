"""FastAPI application entry point, lifespan management, and core route configuration."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError
from app.config import get_settings
from app.database import close_mongo_connection, connect_to_mongo, init_db_indexes, ping_database
from app.routes.analysis import router as analysis_router
from app.routes.documents import router as documents_router
from app.routes.tasks import router as tasks_router
from app.routes.transcriptions import router as transcriptions_router
from app.routes.workflows import router as workflows_router
from app.schemas.transcription import (
    ApiStatus,
    DatabaseStatus,
    HealthResponse,
    WhisperModelStatus,
)
from app.services.whisper_service import get_whisper_service

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("meeting_assistant")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager handling application startup and shutdown events."""
    settings = get_settings()
    logger.info("Starting %s v%s...", settings.PROJECT_NAME, settings.VERSION)

    # --- Startup ---
    # 1. Connect to MongoDB
    try:
        db = connect_to_mongo(
            uri=settings.MONGODB_URI,
            db_name=settings.MONGODB_DATABASE,
        )
        init_db_indexes(db)
    except PyMongoError as e:
        logger.warning(
            "MongoDB could not be reached at startup. Running in degraded state. Error: %s",
            str(e),
        )
    except Exception as e:
        logger.error("Unexpected error during database initialization: %s", str(e))

    # 2. Initialize Whisper service container (lazy model loading prepared)
    whisper_service = get_whisper_service(model_name=settings.WHISPER_MODEL)
    logger.info(
        "Whisper service initialized with model configuration: '%s' (status: %s)",
        whisper_service.model_name,
        whisper_service.status.value,
    )

    yield

    # --- Shutdown ---
    logger.info("Shutting down %s...", settings.PROJECT_NAME)
    close_mongo_connection()
    logger.info("Application shutdown completed.")


settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend REST API for AI Business Meeting Assistant. "
        "Provides recorded audio transcription, meeting intelligence, and notes storage."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes.stream import router as stream_router

# Register Sub-Routers
app.include_router(
    transcriptions_router,
    prefix=f"{settings.API_V1_PREFIX}/transcriptions",
)
app.include_router(
    documents_router,
    prefix=f"{settings.API_V1_PREFIX}/documents",
)
app.include_router(
    analysis_router,
    prefix=f"{settings.API_V1_PREFIX}/analysis",
)
app.include_router(
    tasks_router,
    prefix=f"{settings.API_V1_PREFIX}/tasks",
)
app.include_router(
    workflows_router,
    prefix=f"{settings.API_V1_PREFIX}/workflows",
)
app.include_router(
    stream_router,
    prefix=f"{settings.API_V1_PREFIX}/stream",
)


@app.get(
    f"{settings.API_V1_PREFIX}/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="API and Database Health Check",
    description="Check the current status of the FastAPI server, MongoDB connectivity, and Whisper engine.",
)
def health_check(response: Response) -> HealthResponse:
    """Evaluate system health across core components (API, MongoDB, Whisper)."""
    settings = get_settings()
    is_db_connected = ping_database()
    whisper_service = get_whisper_service()

    db_status = DatabaseStatus.CONNECTED if is_db_connected else DatabaseStatus.DISCONNECTED
    whisper_status = whisper_service.status

    if not is_db_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = ApiStatus.DEGRADED
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = ApiStatus.HEALTHY

    return HealthResponse(
        status=overall_status,
        api_status="running",
        database_status=db_status,
        whisper_status=whisper_status,
        whisper_model=whisper_service.model_name,
        version=settings.VERSION,
    )


@app.get(
    "/",
    tags=["root"],
    summary="Root Welcome Endpoint",
    description="Root endpoint providing quick navigation links to health and documentation.",
)
def root_info() -> dict:
    """Root metadata response."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "api_prefix": settings.API_V1_PREFIX,
    }
