from __future__ import annotations

import re

from app.schemas.request import TaskRequest
from app.schemas.task_result import MeetingExtractResult, MeetingTaskItem
from app.schemas.tool_result import ToolResult


TASK_PREFIXES = (
    "action:",
    "task:",
    "todo:",
    "待办：",
    "待办:",
    "任务：",
    "任务:",
    "- [ ]",
    "* [ ]",
)


def _parse_participants(lines: list[str]) -> list[str]:
    for line in lines:
        if ":" not in line and "：" not in line:
            continue
        key, value = re.split(r"[:：]", line, maxsplit=1)
        if key.strip().lower() in {"participants", "attendees", "members", "参会人", "参与人"}:
            return [item.strip() for item in re.split(r"[，,]", value) if item.strip()]
    return []


def _parse_decisions(lines: list[str]) -> list[str]:
    decisions: list[str] = []
    for line in lines:
        lowered = line.lower().strip()
        if lowered.startswith("decision:") or lowered.startswith("决议:") or lowered.startswith("决议："):
            _, value = re.split(r"[:：]", line, maxsplit=1)
            decisions.append(value.strip())
    return decisions


def _extract_owner(text: str) -> str | None:
    patterns = (
        r"@(?P<owner>[A-Za-z][A-Za-z0-9_-]*)",
        r"owner[:=]\s*(?P<owner>[A-Za-z][A-Za-z0-9_-]*)",
        r"assignee[:=]\s*(?P<owner>[A-Za-z][A-Za-z0-9_-]*)",
        r"负责人[:：]\s*(?P<owner>\S+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group("owner")
    return None


def _extract_due_date(text: str) -> str | None:
    patterns = (
        r"due[:=]\s*(?P<due>\d{4}-\d{2}-\d{2})",
        r"deadline[:=]\s*(?P<due>\d{4}-\d{2}-\d{2})",
        r"before\s+(?P<due>\d{4}-\d{2}-\d{2})",
        r"截止[:：]\s*(?P<due>\d{4}-\d{2}-\d{2})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group("due")
    return None


def _clean_task_title(text: str) -> str:
    cleaned = re.sub(r"^(- \[ \]|\* \[ \]|action:|task:|todo:|待办[:：]|任务[:：])\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"@[\w-]+", "", cleaned)
    cleaned = re.sub(r"(owner|assignee|due|deadline)\s*[:=]\s*[\w-]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"负责人[:：]\s*\S+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"截止[:：]\s*\d{4}-\d{2}-\d{2}", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"before\s+\d{4}-\d{2}-\d{2}", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" -;,.")


def extract_meeting_tasks(meeting_text: str) -> ToolResult:
    raw_text = meeting_text.strip()
    if not raw_text:
        return ToolResult(
            tool_name="meeting_tool",
            status="error",
            message="Meeting text is required.",
            output={},
            error="Missing meeting_text value.",
        )

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title = lines[0].lstrip("# ").strip() if lines else "Meeting Notes"
    participants = _parse_participants(lines)
    decisions = _parse_decisions(lines)

    action_items: list[MeetingTaskItem] = []
    for line in lines:
        lowered = line.lower()
        if not any(lowered.startswith(prefix) for prefix in TASK_PREFIXES):
            continue
        action_items.append(
            MeetingTaskItem(
                title=_clean_task_title(line),
                owner=_extract_owner(line),
                due_date=_extract_due_date(line),
                status="open",
            )
        )

    summary_lines = [line for line in lines[1:] if not any(line.lower().startswith(prefix) for prefix in TASK_PREFIXES)]
    summary = " ".join(summary_lines[:3])[:240] if summary_lines else "Meeting notes parsed from mock input."

    result = MeetingExtractResult(
        meeting_title=title,
        summary=summary,
        participants=participants,
        decisions=decisions,
        action_items=action_items,
    )

    return ToolResult(
        tool_name="meeting_tool",
        status="success",
        message=f"Extracted {len(action_items)} task items from meeting notes.",
        output=result.model_dump(),
    )


class MeetingTool:
    name = "meeting_tool"

    def run(self, request: TaskRequest) -> ToolResult:
        context = request.context or {}
        meeting_text = str(context.get("meeting_text") or request.user_input)
        return extract_meeting_tasks(meeting_text)


from app.services.llm_service import LLMServiceError, get_qwen_llm_service


def extract_meeting_tasks(meeting_text: str) -> ToolResult:
    raw_text = meeting_text.strip()
    if not raw_text:
        return ToolResult(
            tool_name="meeting_tool",
            status="error",
            message="Meeting text is required.",
            output={},
            error="Missing meeting_text value.",
        )

    try:
        result = get_qwen_llm_service().extract_meeting_tasks(raw_text)
    except LLMServiceError as exc:
        return ToolResult(
            tool_name="meeting_tool",
            status="error",
            message="Failed to extract tasks from the meeting notes.",
            output={},
            error=str(exc),
        )

    task_count = len(result.get("tasks", []))
    return ToolResult(
        tool_name="meeting_tool",
        status="success",
        message=f"Extracted {task_count} task items from meeting notes.",
        output=result,
    )


class MeetingTool:
    name = "meeting_tool"

    def run(self, request: TaskRequest) -> ToolResult:
        meeting_text = str(request.get_input_value("meeting_text") or request.user_input)
        return extract_meeting_tasks(meeting_text)
