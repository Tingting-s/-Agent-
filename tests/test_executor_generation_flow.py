import json

from app.agents.executor_agent import ExecutorAgent
from app.agents.router_agent import RouteDecision
from app.agents.validator_agent import ValidatorAgent
from app.schemas.request import TaskRequest


class FlakyGeneratorAgent:
    def __init__(self) -> None:
        self.calls = 0

    def generate(
        self,
        *,
        task_type: str,
        status: str,
        structured_result: dict[str, object] | None,
        message: str | None = None,
        fallback_message: str | None = None,
    ) -> str:
        self.calls += 1
        if self.calls == 1:
            return json.dumps({"status": status, "message": "missing fields"})
        return json.dumps(
            {
                "task_type": task_type,
                "status": status,
                "message": message or fallback_message or "ok",
                "structured_result": structured_result or {},
            }
        )


class AlwaysInvalidGeneratorAgent:
    def __init__(self) -> None:
        self.calls = 0

    def generate(
        self,
        *,
        task_type: str,
        status: str,
        structured_result: dict[str, object] | None,
        message: str | None = None,
        fallback_message: str | None = None,
    ) -> str:
        self.calls += 1
        return json.dumps({"status": status})


def test_executor_retries_when_generated_json_is_missing_fields() -> None:
    generator_agent = FlakyGeneratorAgent()
    executor = ExecutorAgent(
        generator_agent=generator_agent,
        validator_agent=ValidatorAgent(),
    )
    decision = RouteDecision(
        task_type="weather_query",
        steps=("weather_query",),
        reason="unit test retry",
    )
    request = TaskRequest(
        user_input="Shanghai weather",
        context={"city": "Shanghai"},
    )

    response = executor.execute(decision=decision, request=request)

    assert response.status == "success"
    assert response.retry_count == 1
    assert generator_agent.calls == 2


def test_executor_returns_need_more_info_without_retry() -> None:
    generator_agent = FlakyGeneratorAgent()
    executor = ExecutorAgent(
        generator_agent=generator_agent,
        validator_agent=ValidatorAgent(),
    )
    decision = RouteDecision(
        task_type="document_summary",
        steps=("document_summary",),
        reason="unit test need_more_info",
    )
    request = TaskRequest(user_input="please summarize this document")

    response = executor.execute(decision=decision, request=request)

    assert response.status == "need_more_info"
    assert response.retry_count == 0
    assert generator_agent.calls == 1
    assert response.structured_result["missing_fields"] == ["file_path"]


def test_executor_returns_fallback_message_after_retry_exhaustion() -> None:
    generator_agent = AlwaysInvalidGeneratorAgent()
    executor = ExecutorAgent(
        generator_agent=generator_agent,
        validator_agent=ValidatorAgent(),
    )
    decision = RouteDecision(
        task_type="weather_query",
        steps=("weather_query",),
        reason="unit test fallback",
    )
    request = TaskRequest(
        user_input="Hangzhou weather",
        context={"city": "Hangzhou"},
    )

    response = executor.execute(decision=decision, request=request)

    assert response.status == "error"
    assert response.retry_count == 2
    assert generator_agent.calls == 3
    assert "fallback" in response.message.lower()
    assert "validation_error" in response.structured_result


def test_executor_extracts_city_from_weather_query_text() -> None:
    executor = ExecutorAgent(
        generator_agent=FlakyGeneratorAgent(),
        validator_agent=ValidatorAgent(),
    )
    decision = RouteDecision(
        task_type="weather_query",
        steps=("weather_query",),
        reason="unit test city extraction",
    )
    request = TaskRequest(user_input="帮我查询北京今天天气")

    response = executor.execute(decision=decision, request=request)

    assert response.status == "success"
    assert response.structured_result["city"] == "北京"


def test_executor_prioritizes_additional_inputs_city_for_weather_query() -> None:
    executor = ExecutorAgent(
        generator_agent=FlakyGeneratorAgent(),
        validator_agent=ValidatorAgent(),
    )
    decision = RouteDecision(
        task_type="weather_query",
        steps=("weather_query",),
        reason="unit test additional_inputs city",
    )
    request = TaskRequest(
        user_input="帮我查询北京今天天气",
        additional_inputs={"city": "上海"},
    )

    response = executor.execute(decision=decision, request=request)

    assert response.status == "success"
    assert response.structured_result["city"] == "上海"


def test_executor_returns_need_more_info_when_weather_city_is_missing() -> None:
    executor = ExecutorAgent(
        generator_agent=FlakyGeneratorAgent(),
        validator_agent=ValidatorAgent(),
    )
    decision = RouteDecision(
        task_type="weather_query",
        steps=("weather_query",),
        reason="unit test weather need_more_info",
    )
    request = TaskRequest(user_input="帮我查询今天天气")

    response = executor.execute(decision=decision, request=request)

    assert response.status == "need_more_info"
    assert response.retry_count == 0
    assert response.structured_result["missing_fields"] == ["city"]
