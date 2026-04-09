from __future__ import annotations

from app.schemas.request import TaskRequest
from app.schemas.task_result import EmailDraftResult
from app.schemas.tool_result import ToolResult


TONE_STYLES = {
    "formal": {
        "greeting": "Dear team,",
        "closing": "Best regards,",
    },
    "friendly": {
        "greeting": "Hi team,",
        "closing": "Thanks,",
    },
    "concise": {
        "greeting": "Hello,",
        "closing": "Regards,",
    },
}


def generate_email_draft(subject: str, purpose: str, context: str, tone: str = "formal") -> ToolResult:
    normalized_subject = subject.strip()
    normalized_purpose = purpose.strip()
    normalized_context = context.strip()

    if not normalized_subject:
        return ToolResult(
            tool_name="email_tool",
            status="error",
            message="Email subject is required.",
            output={},
            error="Missing subject value.",
        )

    if not normalized_purpose:
        return ToolResult(
            tool_name="email_tool",
            status="error",
            message="Email purpose is required.",
            output={"subject": normalized_subject},
            error="Missing purpose value.",
        )

    tone_key = tone.strip().lower() or "formal"
    style = TONE_STYLES.get(tone_key, TONE_STYLES["formal"])

    body_parts = [
        style["greeting"],
        "",
        f"I am writing to {normalized_purpose}.",
    ]
    if normalized_context:
        body_parts.append(normalized_context)
    body_parts.extend(
        [
            "",
            "Please let me know if you need any additional information.",
            "",
            style["closing"],
            "Office Assistant",
        ]
    )
    body = "\n".join(body_parts)

    draft = EmailDraftResult(
        subject=normalized_subject,
        recipients=[],
        cc=[],
        body=body,
        tone=tone_key if tone_key in TONE_STYLES else "formal",
    )

    return ToolResult(
        tool_name="email_tool",
        status="success",
        message=f"Generated mock email draft for '{normalized_subject}'.",
        output=draft.model_dump(),
    )


class EmailTool:
    name = "email_tool"

    def run(self, request: TaskRequest) -> ToolResult:
        context = request.context or {}
        subject = str(context.get("subject") or "Draft Email")
        purpose = str(context.get("purpose") or request.user_input)
        email_context = str(context.get("context") or "")
        tone = str(context.get("tone") or "formal")
        return generate_email_draft(subject, purpose, email_context, tone=tone)


from app.services.llm_service import LLMServiceError, get_qwen_llm_service


def generate_email_draft(subject: str, purpose: str, context: str, tone: str = "formal") -> ToolResult:
    normalized_subject = subject.strip()
    normalized_purpose = purpose.strip()
    normalized_context = context.strip()
    normalized_tone = tone.strip().lower() or "formal"

    if not normalized_subject:
        return ToolResult(
            tool_name="email_tool",
            status="error",
            message="Email subject is required.",
            output={},
            error="Missing subject value.",
        )

    if not normalized_purpose:
        return ToolResult(
            tool_name="email_tool",
            status="error",
            message="Email purpose is required.",
            output={"subject": normalized_subject},
            error="Missing purpose value.",
        )

    try:
        result = get_qwen_llm_service().generate_email(
            subject=normalized_subject,
            purpose=normalized_purpose,
            context=normalized_context,
            tone=normalized_tone,
        )
    except LLMServiceError as exc:
        return ToolResult(
            tool_name="email_tool",
            status="error",
            message="Failed to generate the email draft.",
            output={
                "subject": normalized_subject,
                "tone": normalized_tone,
            },
            error=str(exc),
        )

    return ToolResult(
        tool_name="email_tool",
        status="success",
        message=f"Generated email draft for '{result['subject']}'.",
        output=result,
    )


class EmailTool:
    name = "email_tool"

    def run(self, request: TaskRequest) -> ToolResult:
        subject = str(request.get_input_value("subject") or "Draft Email")
        purpose = str(request.get_input_value("purpose") or request.user_input)
        email_context = str(request.get_input_value("email_context") or request.get_input_value("context") or "")
        tone = str(request.get_input_value("tone") or "formal")
        return generate_email_draft(subject, purpose, email_context, tone=tone)
