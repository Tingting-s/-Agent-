import logging

from app.services.task_service import TaskService
from app.schemas.request import TaskRequest


def test_task_service_emits_basic_logs(caplog) -> None:
    service = TaskService()

    with caplog.at_level(logging.INFO):
        service.handle_request(TaskRequest(user_input="Shanghai weather today", context={"city": "Shanghai"}))

    messages = [record.getMessage() for record in caplog.records]
    assert any("Handling task request." in message for message in messages)
    assert any("Route decision created." in message for message in messages)
    assert any("Task handled." in message for message in messages)
