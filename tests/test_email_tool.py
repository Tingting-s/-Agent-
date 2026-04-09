import app.tools.email_tool as email_tool


class FakeEmailLLMService:
    def generate_email(self, subject: str, purpose: str, context: str, tone: str) -> dict[str, str]:
        return {
            "subject": subject,
            "body": f"{purpose}\n\nContext: {context}",
            "tone": tone,
        }


def test_generate_email_draft_returns_llm_result(monkeypatch) -> None:
    monkeypatch.setattr(email_tool, "get_qwen_llm_service", lambda: FakeEmailLLMService())

    result = email_tool.generate_email_draft(
        subject="Project Update",
        purpose="Share the latest project update",
        context="The backend skeleton is complete and unit tests are in progress.",
        tone="friendly",
    )

    assert result.status == "success"
    assert result.output["subject"] == "Project Update"
    assert result.output["tone"] == "friendly"
    assert "Share the latest project update" in result.output["body"]
    assert "backend skeleton is complete" in result.output["body"]


def test_generate_email_draft_requires_subject() -> None:
    result = email_tool.generate_email_draft(
        subject="",
        purpose="share an update",
        context="Status looks good.",
    )

    assert result.status == "error"
    assert result.error == "Missing subject value."
