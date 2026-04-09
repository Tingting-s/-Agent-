from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
DATA_DIR = Path(__file__).resolve().parent / "data"


def test_post_tasks_execute_runs_compound_workflow() -> None:
    meeting_text = (DATA_DIR / "meeting_notes.txt").read_text(encoding="utf-8")

    response = client.post(
        "/tasks/execute",
        json={
            "user_input": "根据会议纪要提取任务项并生成邮件草稿",
            "context": {
                "meeting_text": meeting_text,
                "subject": "Weekly Sync Action Items",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["task_type"] == "email_draft"
    assert payload["status"] == "success"
    assert payload["structured_result"]["workflow"] == ["meeting_extraction", "email_draft"]
    assert payload["structured_result"]["email_draft"]["subject"] == "Weekly Sync Action Items"


def test_post_tasks_execute_extracts_city_from_weather_query() -> None:
    response = client.post(
        "/tasks/execute",
        json={
            "user_input": "帮我查询北京今天天气",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "weather_query"
    assert payload["status"] == "success"
    assert payload["structured_result"]["city"] == "北京"


def test_post_tasks_execute_prioritizes_additional_inputs_city() -> None:
    response = client.post(
        "/tasks/execute",
        json={
            "user_input": "帮我查询北京今天天气",
            "additional_inputs": {
                "city": "上海"
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["structured_result"]["city"] == "上海"


def test_post_tasks_execute_returns_need_more_info_when_city_missing() -> None:
    response = client.post(
        "/tasks/execute",
        json={
            "user_input": "帮我查询今天天气",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "weather_query"
    assert payload["status"] == "need_more_info"
    assert payload["structured_result"]["missing_fields"] == ["city"]


import app.agents.executor_agent as executor_agent_module
from app.schemas.tool_result import ToolResult


def test_post_tasks_execute_runs_compound_workflow(monkeypatch) -> None:
    monkeypatch.setattr(
        executor_agent_module,
        "extract_meeting_tasks",
        lambda meeting_text: ToolResult(
            tool_name="meeting_tool",
            status="success",
            message="Meeting tasks extracted.",
            output={
                "summary": "Weekly sync completed.",
                "participants": ["Alice", "Bob", "Carol"],
                "decisions": [],
                "tasks": [
                    {
                        "task_name": "Prepare demo script",
                        "owner": "Alice",
                        "deadline": "2026-04-10",
                        "priority": "high",
                    }
                ],
            },
        ),
    )
    monkeypatch.setattr(
        executor_agent_module,
        "generate_email_draft",
        lambda subject, purpose, context, tone: ToolResult(
            tool_name="email_tool",
            status="success",
            message="Email draft generated.",
            output={
                "subject": subject,
                "body": f"Purpose: {purpose}\n\n{context}",
                "tone": tone,
            },
        ),
    )

    meeting_text = (DATA_DIR / "meeting_notes.txt").read_text(encoding="utf-8")

    response = client.post(
        "/tasks/execute",
        json={
            "user_input": "Extract action items from meeting notes and draft an email",
            "context": {
                "meeting_text": meeting_text,
                "subject": "Weekly Sync Action Items",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["task_type"] == "email_draft"
    assert payload["status"] == "success"
    assert payload["structured_result"]["workflow"] == ["meeting_extraction", "email_draft"]
    assert payload["structured_result"]["email_draft"]["subject"] == "Weekly Sync Action Items"
    assert payload["structured_result"]["meeting_extraction"]["tasks"][0]["task_name"] == "Prepare demo script"
