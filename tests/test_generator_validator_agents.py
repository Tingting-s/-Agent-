import json

from app.agents.generator_agent import GeneratorAgent
from app.agents.validator_agent import ValidatorAgent


def test_generator_agent_builds_message_and_structured_result() -> None:
    raw_response = GeneratorAgent().generate(
        task_type="weather_query",
        status="success",
        message="Weather query completed.",
        structured_result={"city": "Shanghai", "condition": "Cloudy"},
        fallback_message="Fallback weather message.",
    )

    payload = json.loads(raw_response)

    assert payload["task_type"] == "weather_query"
    assert payload["status"] == "success"
    assert payload["message"] == "Weather query completed."
    assert payload["structured_result"]["city"] == "Shanghai"


def test_validator_agent_rejects_missing_required_fields() -> None:
    result = ValidatorAgent().validate('{"status": "success", "message": "ok"}')

    assert result.is_valid is False
    assert "task_type" in (result.error_message or "")
    assert "structured_result" in (result.error_message or "")


def test_validator_agent_accepts_valid_json_payload() -> None:
    result = ValidatorAgent().validate(
        json.dumps(
            {
                "task_type": "document_summary",
                "status": "success",
                "message": "Document summary completed.",
                "structured_result": {"title": "Release Plan"},
            }
        )
    )

    assert result.is_valid is True
    assert result.payload is not None
    assert result.payload["structured_result"]["title"] == "Release Plan"
