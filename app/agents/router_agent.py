from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from app.prompts.router_prompt import ROUTER_SYSTEM_PROMPT
from app.schemas.request import TaskRequest


@dataclass(frozen=True)
class RouteDecision:
    task_type: str
    steps: tuple[str, ...]
    reason: str
    prompt: str = ROUTER_SYSTEM_PROMPT


class RouterAgent:
    supported_task_types: ClassVar[set[str]] = {
        "meeting_extraction",
        "document_summary",
        "weather_query",
        "email_draft",
    }
    keyword_rules: ClassVar[dict[str, tuple[str, ...]]] = {
        "meeting_extraction": ("会议纪要", "待办", "任务", "meeting", "todo", "action item"),
        "document_summary": ("总结", "摘要", "文档", "文件", "summary", "document", "file"),
        "weather_query": ("天气", "温度", "下雨", "weather", "temperature", "rain"),
        "email_draft": ("邮件", "草稿", "发给", "email", "draft", "send to"),
    }

    def __init__(self, system_prompt: str = ROUTER_SYSTEM_PROMPT) -> None:
        self.system_prompt = system_prompt

    def route(self, request: TaskRequest) -> RouteDecision:
        text = self._build_search_text(request)

        if self._is_compound_meeting_email_task(text):
            return RouteDecision(
                task_type="email_draft",
                steps=("meeting_extraction", "email_draft"),
                reason="Matched meeting and email keywords, routing as a compound workflow.",
            )

        for task_type, keywords in self.keyword_rules.items():
            matched_keyword = next((keyword for keyword in keywords if keyword in text), None)
            if matched_keyword:
                return RouteDecision(
                    task_type=task_type,
                    steps=(task_type,),
                    reason=f"Matched keyword '{matched_keyword}' and routed to {task_type}.",
                )

        if request.task_type in self.supported_task_types:
            return RouteDecision(
                task_type=request.task_type,
                steps=(request.task_type,),
                reason=f"Used explicit task_type '{request.task_type}'.",
            )

        inferred_task_type = self._infer_from_context(request)
        return RouteDecision(
            task_type=inferred_task_type,
            steps=(inferred_task_type,),
            reason=f"No keyword matched, inferred task type as {inferred_task_type}.",
        )

    def _build_search_text(self, request: TaskRequest) -> str:
        parts = [
            request.user_input,
            request.task_type or "",
            str(request.get_input_value("city") or ""),
            str(request.get_input_value("subject") or ""),
            str(request.get_input_value("purpose") or ""),
        ]
        return " ".join(part for part in parts if part).lower()

    def _is_compound_meeting_email_task(self, text: str) -> bool:
        has_meeting_keyword = any(keyword in text for keyword in self.keyword_rules["meeting_extraction"])
        has_email_keyword = any(keyword in text for keyword in self.keyword_rules["email_draft"])
        return has_meeting_keyword and has_email_keyword

    def _infer_from_context(self, request: TaskRequest) -> str:
        user_input = request.user_input.strip().lower()
        if request.get_input_value("meeting_text"):
            return "meeting_extraction"
        if request.get_input_value("file_path"):
            return "document_summary"
        if user_input.endswith(".txt") or user_input.endswith(".md"):
            return "document_summary"
        if request.get_input_value("city"):
            return "weather_query"
        if request.get_input_value("subject") or request.get_input_value("purpose"):
            return "email_draft"
        return "email_draft"
