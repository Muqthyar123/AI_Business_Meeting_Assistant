"""Routes package."""

from app.routes.analysis import router as analysis_router
from app.routes.documents import router as documents_router
from app.routes.tasks import router as tasks_router
from app.routes.transcriptions import router as transcriptions_router
from app.routes.workflows import router as workflows_router

__all__ = [
    "transcriptions_router",
    "documents_router",
    "analysis_router",
    "tasks_router",
    "workflows_router",
]
