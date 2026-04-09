from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.schemas.request import TaskRequest
from app.schemas.response import HealthResponse, TaskResponse
from app.services.task_service import TaskService
from app.utils.logger import get_logger


router = APIRouter(tags=["system"])
task_service = TaskService()
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    logger.info("Health check requested.")
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )


@router.post("/tasks/execute", response_model=TaskResponse, tags=["tasks"])
def execute_task(request: TaskRequest) -> TaskResponse:
    logger.info(
        "Task execution requested. task_type=%s input_preview=%s",
        request.task_type,
        request.user_input[:80],
    )
    return task_service.handle_request(request)
