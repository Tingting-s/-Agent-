from pathlib import Path

import app.tools.meeting_tool as meeting_tool


DATA_DIR = Path(__file__).resolve().parent / "data"


class FakeMeetingLLMService:
    def extract_meeting_tasks(self, meeting_text: str) -> dict[str, object]:
        return {
            "summary": "Weekly sync focused on release readiness.",
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
        }


def test_extract_meeting_tasks_returns_llm_tasks(monkeypatch) -> None:
    monkeypatch.setattr(meeting_tool, "get_qwen_llm_service", lambda: FakeMeetingLLMService())
    meeting_text = (DATA_DIR / "meeting_notes.txt").read_text(encoding="utf-8")

    result = meeting_tool.extract_meeting_tasks(meeting_text)

    assert result.status == "success"
    assert result.output["participants"] == ["Alice", "Bob", "Carol"]
    assert len(result.output["tasks"]) == 2
    assert result.output["tasks"][0]["task_name"] == "Prepare demo script"
    assert result.output["tasks"][0]["owner"] == "Alice"
    assert result.output["tasks"][1]["deadline"] == "2026-04-12"
    assert result.output["tasks"][1]["priority"] == "medium"


def test_extract_meeting_tasks_requires_text() -> None:
    result = meeting_tool.extract_meeting_tasks("   ")

    assert result.status == "error"
    assert result.error == "Missing meeting_text value."
