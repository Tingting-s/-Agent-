from pathlib import Path

from app.agents.executor_agent import ExecutorAgent
from app.agents.router_agent import RouteDecision, RouterAgent
from app.schemas.request import TaskRequest


DATA_DIR = Path(__file__).resolve().parent / "data"


def test_executor_runs_meeting_extraction() -> None:
    meeting_text = (DATA_DIR / "meeting_notes.txt").read_text(encoding="utf-8")
    request = TaskRequest(
        user_input="请提取会议纪要中的任务项",
        context={"meeting_text": meeting_text},
    )
    decision = RouteDecision(
        task_type="meeting_extraction",
        steps=("meeting_extraction",),
        reason="unit test",
    )

    response = ExecutorAgent().execute(decision=decision, request=request)

    assert response.task_type == "meeting_extraction"
    assert response.status == "success"
    assert len(response.structured_result["action_items"]) == 3
    assert response.structured_result["route_reason"] == "unit test"


def test_executor_runs_compound_meeting_to_email_workflow() -> None:
    meeting_text = (DATA_DIR / "meeting_notes.txt").read_text(encoding="utf-8")
    request = TaskRequest(
        user_input="根据会议纪要提取任务项并生成邮件草稿",
        context={
            "meeting_text": meeting_text,
            "subject": "Weekly Sync Action Items",
            "tone": "formal",
        },
    )
    decision = RouterAgent().route(request)

    response = ExecutorAgent().execute(decision=decision, request=request)

    assert response.task_type == "email_draft"
    assert response.status == "success"
    assert response.structured_result["workflow"] == ["meeting_extraction", "email_draft"]
    assert len(response.structured_result["meeting_extraction"]["action_items"]) == 3
    assert response.structured_result["email_draft"]["subject"] == "Weekly Sync Action Items"
    assert "Action items:" in response.structured_result["email_draft"]["body"]


import app.agents.executor_agent as executor_agent_module
from app.schemas.tool_result import ToolResult


def test_executor_runs_meeting_extraction(monkeypatch) -> None:
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
                "decisions": ["Keep the first release focused on mock tools."],
                "tasks": [
                    {
                        "task_name": "Prepare demo script",
                        "owner": "Alice",
                        "deadline": "2026-04-10",
                        "priority": "high",
                    },
                    {
                        "task_name": "Review tool schemas",
                        "owner": "Bob",
                        "deadline": "2026-04-12",
                        "priority": "medium",
                    },
                ],
            },
        ),
    )

    meeting_text = (DATA_DIR / "meeting_notes.txt").read_text(encoding="utf-8")
    request = TaskRequest(
        user_input="Please extract tasks from these meeting notes.",
        context={"meeting_text": meeting_text},
    )
    decision = RouteDecision(
        task_type="meeting_extraction",
        steps=("meeting_extraction",),
        reason="unit test",
    )

    response = executor_agent_module.ExecutorAgent().execute(decision=decision, request=request)

    assert response.task_type == "meeting_extraction"
    assert response.status == "success"
    assert len(response.structured_result["tasks"]) == 2
    assert response.structured_result["tasks"][0]["task_name"] == "Prepare demo script"
    assert response.structured_result["route_reason"] == "unit test"


def test_executor_runs_compound_meeting_to_email_workflow(monkeypatch) -> None:
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
    request = TaskRequest(
        user_input="Extract action items from meeting notes and draft an email.",
        context={
            "meeting_text": meeting_text,
            "subject": "Weekly Sync Action Items",
            "tone": "formal",
        },
    )
    decision = RouteDecision(
        task_type="email_draft",
        steps=("meeting_extraction", "email_draft"),
        reason="unit test compound",
    )

    response = executor_agent_module.ExecutorAgent().execute(decision=decision, request=request)

    assert response.task_type == "email_draft"
    assert response.status == "success"
    assert response.structured_result["workflow"] == ["meeting_extraction", "email_draft"]
    assert len(response.structured_result["meeting_extraction"]["tasks"]) == 1
    assert response.structured_result["email_draft"]["subject"] == "Weekly Sync Action Items"
    assert "Tasks:" in response.structured_result["email_draft"]["body"]
