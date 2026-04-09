from __future__ import annotations

from app.agents.executor_agent import ExecutorAgent
from app.agents.router_agent import RouterAgent
from app.schemas.request import TaskRequest
from app.schemas.response import TaskResponse
from app.utils.logger import get_logger


logger = get_logger(__name__)


class TaskService:
    def __init__(
        self,
        router_agent: RouterAgent | None = None,
        executor_agent: ExecutorAgent | None = None,
    ) -> None:
        self.router_agent = router_agent or RouterAgent()
        self.executor_agent = executor_agent or ExecutorAgent()

    def handle_request(self, request: TaskRequest) -> TaskResponse:
        logger.info(
            "Handling task request. task_type_hint=%s input_preview=%s",
            request.task_type,
            request.user_input[:80],
        )
        decision = self.router_agent.route(request)
        logger.info(
            "Route decision created. task_type=%s steps=%s reason=%s",
            decision.task_type,
            list(decision.steps),
            decision.reason,
        )
        response = self.executor_agent.execute(decision=decision, request=request)
        logger.info(
            "Task handled. task_type=%s status=%s retry_count=%s",
            response.task_type,
            response.status,
            response.retry_count,
        )
        return response
