from __future__ import annotations

from typing import Any

from app.agents.generator_agent import GeneratorAgent
from app.agents.router_agent import RouteDecision
from app.agents.validator_agent import ValidationResult, ValidatorAgent
from app.schemas.request import TaskRequest
from app.schemas.response import TaskResponse
from app.schemas.tool_result import ToolResult
from app.tools.document_tool import read_document
from app.tools.email_tool import generate_email_draft
from app.tools.meeting_tool import extract_meeting_tasks
from app.tools.weather_tool import extract_city_from_user_input, get_weather


class ExecutorAgent:
    def __init__(
        self,
        generator_agent: GeneratorAgent | None = None,
        validator_agent: ValidatorAgent | None = None,
    ) -> None:
        self.generator_agent = generator_agent or GeneratorAgent()
        self.validator_agent = validator_agent or ValidatorAgent()
        self.single_task_handlers = {
            "meeting_extraction": self._run_meeting_extraction,
            "document_summary": self._run_document_summary,
            "weather_query": self._run_weather_query,
            "email_draft": self._run_email_draft,
        }

    def execute(self, decision: RouteDecision, request: TaskRequest) -> TaskResponse:
        missing_fields = self._get_missing_fields(decision, request)
        if missing_fields:
            return self._build_need_more_info_response(
                task_type=decision.task_type,
                route_reason=decision.reason,
                missing_fields=missing_fields,
            )

        if decision.steps == ("meeting_extraction", "email_draft"):
            return self._execute_meeting_to_email(decision, request)

        handler = self.single_task_handlers.get(decision.task_type)
        if handler is None:
            return self._finalize_response(
                task_type=decision.task_type,
                status="error",
                structured_result={"route_reason": decision.reason},
                message=f"Unsupported task type: {decision.task_type}.",
                fallback_message="The task could not be routed to a supported tool.",
            )

        tool_result = handler(request)
        return self._build_response(
            task_type=decision.task_type,
            tool_result=tool_result,
            route_reason=decision.reason,
        )

    def _run_meeting_extraction(self, request: TaskRequest) -> ToolResult:
        meeting_text = str(request.get_input_value("meeting_text") or request.user_input)
        return extract_meeting_tasks(meeting_text)

    def _run_document_summary(self, request: TaskRequest) -> ToolResult:
        file_path = str(request.get_input_value("file_path") or request.user_input)
        return read_document(file_path)

    def _run_weather_query(self, request: TaskRequest) -> ToolResult:
        city = self._extract_weather_city(request)
        return get_weather(city)

    def _run_email_draft(self, request: TaskRequest) -> ToolResult:
        subject = str(request.get_input_value("subject") or "Draft Email")
        purpose = str(request.get_input_value("purpose") or request.user_input)
        body_context = str(request.get_input_value("email_context") or request.get_input_value("context") or "")
        tone = str(request.get_input_value("tone") or "formal")
        return generate_email_draft(subject, purpose, body_context, tone=tone)

    def _execute_meeting_to_email(self, decision: RouteDecision, request: TaskRequest) -> TaskResponse:
        meeting_result = self._run_meeting_extraction(request)
        if meeting_result.status == "error":
            return self._finalize_response(
                task_type=decision.task_type,
                status="error",
                structured_result={
                    "workflow": list(decision.steps),
                    "meeting_extraction": self._normalize_structured_result(
                        task_type="meeting_extraction",
                        structured_result=dict(meeting_result.output),
                    ),
                    "meeting_error": meeting_result.error,
                    "route_reason": decision.reason,
                },
                message="Failed to extract task items from the meeting notes.",
                fallback_message="The meeting notes could not be processed, so the email draft was not created.",
            )

        email_context = self._build_email_context_from_meeting(meeting_result.output)
        email_result = generate_email_draft(
            subject=str(request.get_input_value("subject") or "Meeting Action Items"),
            purpose=str(request.get_input_value("purpose") or "share the extracted tasks from the meeting notes"),
            context=email_context,
            tone=str(request.get_input_value("tone") or "formal"),
        )

        status = "success" if email_result.status == "success" else "error"
        message = (
            "Meeting tasks extracted and email draft generated."
            if status == "success"
            else "Meeting tasks were extracted, but email draft generation failed."
        )
        return self._finalize_response(
            task_type=decision.task_type,
            status=status,
            structured_result={
                "workflow": list(decision.steps),
                "meeting_extraction": self._normalize_structured_result(
                    task_type="meeting_extraction",
                    structured_result=dict(meeting_result.output),
                ),
                "email_draft": self._normalize_structured_result(
                    task_type="email_draft",
                    structured_result=dict(email_result.output),
                ),
                "email_error": email_result.error,
                "route_reason": decision.reason,
            },
            message=message,
            fallback_message="The compound workflow finished with errors, and a fallback response was returned.",
        )

    def _build_response(self, task_type: str, tool_result: ToolResult, route_reason: str) -> TaskResponse:
        structured_result = self._normalize_structured_result(
            task_type=task_type,
            structured_result=dict(tool_result.output),
        )
        structured_result["route_reason"] = route_reason
        if tool_result.error:
            structured_result["error"] = tool_result.error
        fallback_message = (
            f"Unable to complete {task_type}. Returning the safest available fallback response."
            if tool_result.status == "error"
            else f"Unable to generate a complete {task_type} response. Returning fallback response."
        )
        return self._finalize_response(
            task_type=task_type,
            status=tool_result.status,
            structured_result=structured_result,
            message=tool_result.message,
            fallback_message=fallback_message,
        )

    def _normalize_structured_result(
        self,
        *,
        task_type: str,
        structured_result: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = dict(structured_result)

        if task_type == "email_draft":
            normalized.setdefault("subject", "")
            normalized.setdefault("body", "")
            normalized.setdefault("tone", "formal")
            return normalized

        if task_type == "meeting_extraction":
            tasks = normalized.get("tasks", [])
            if not isinstance(tasks, list):
                tasks = []
            normalized["tasks"] = [self._normalize_meeting_task(item) for item in tasks]
            normalized.setdefault("summary", "")
            normalized.setdefault("participants", [])
            normalized.setdefault("decisions", [])
            return normalized

        if task_type == "document_summary":
            normalized.setdefault("summary", "")
            normalized.setdefault("key_points", [])
            normalized.setdefault("risks", [])
            return normalized

        return normalized

    def _normalize_meeting_task(self, task_item: object) -> dict[str, Any]:
        if not isinstance(task_item, dict):
            task_item = {}

        normalized_task = dict(task_item)
        normalized_task.setdefault("task_name", "")
        normalized_task.setdefault("owner", "")
        normalized_task.setdefault("deadline", "")
        normalized_task.setdefault("priority", "")
        return normalized_task

    def _finalize_response(
        self,
        *,
        task_type: str,
        status: str,
        structured_result: dict[str, Any],
        message: str | None,
        fallback_message: str,
        max_retries: int = 2,
    ) -> TaskResponse:
        last_validation: ValidationResult | None = None

        for retry_count in range(max_retries + 1):
            raw_response = self.generator_agent.generate(
                task_type=task_type,
                status=status,
                structured_result=structured_result,
                message=message,
                fallback_message=fallback_message,
            )
            validation = self.validator_agent.validate(raw_response)
            if validation.is_valid and validation.payload is not None:
                return TaskResponse(
                    task_type=str(validation.payload["task_type"]),
                    status=str(validation.payload["status"]),
                    message=str(validation.payload["message"]),
                    structured_result=dict(validation.payload["structured_result"]),
                    retry_count=retry_count,
                )
            last_validation = validation
            if retry_count >= max_retries or not validation.retryable:
                break

        safe_structured_result = dict(structured_result)
        if last_validation and last_validation.error_message:
            safe_structured_result["validation_error"] = last_validation.error_message

        return TaskResponse(
            task_type=task_type,
            status="error" if status != "need_more_info" else "need_more_info",
            message=fallback_message,
            structured_result=safe_structured_result,
            retry_count=max_retries,
        )

    def _build_need_more_info_response(
        self,
        *,
        task_type: str,
        route_reason: str,
        missing_fields: list[str],
    ) -> TaskResponse:
        structured_result = {
            "missing_fields": missing_fields,
            "route_reason": route_reason,
        }
        if task_type == "weather_query" and "city" in missing_fields:
            message = "无法识别要查询的城市，请补充城市名称后再试。"
            fallback_message = "请补充要查询的城市名称。"
        else:
            message = f"More information is required to complete {task_type}. Missing: {', '.join(missing_fields)}."
            fallback_message = "More information is required before this task can continue."
        return self._finalize_response(
            task_type=task_type,
            status="need_more_info",
            structured_result=structured_result,
            message=message,
            fallback_message=fallback_message,
            max_retries=0,
        )

    def _get_missing_fields(self, decision: RouteDecision, request: TaskRequest) -> list[str]:
        user_input = request.user_input.strip()

        if decision.steps == ("meeting_extraction", "email_draft"):
            if not request.get_input_value("meeting_text") and not self._looks_like_meeting_notes(user_input):
                return ["meeting_text"]
            return []

        if decision.task_type == "meeting_extraction":
            if not request.get_input_value("meeting_text") and not self._looks_like_meeting_notes(user_input):
                return ["meeting_text"]
            return []

        if decision.task_type == "document_summary":
            file_path = str(request.get_input_value("file_path") or user_input).strip().lower()
            if not file_path.endswith(".txt") and not file_path.endswith(".md"):
                return ["file_path"]
            return []

        if decision.task_type == "weather_query":
            if not self._extract_weather_city(request):
                return ["city"]
            return []

        if decision.task_type == "email_draft":
            if request.get_input_value("subject") or request.get_input_value("purpose"):
                return []
            if self._looks_like_specific_email_request(user_input):
                return []
            return ["purpose"]

        return []

    def _looks_like_meeting_notes(self, text: str) -> bool:
        normalized = text.strip()
        if not normalized:
            return False
        return "\n" in normalized or len(normalized) >= 80

    def _looks_like_specific_email_request(self, text: str) -> bool:
        normalized = text.strip().lower()
        generic_patterns = {
            "write email",
            "draft email",
            "email draft",
            "write an email",
            "help me draft an email",
            "\u5199\u90ae\u4ef6",
            "\u90ae\u4ef6\u8349\u7a3f",
            "\u5199\u4e00\u5c01\u90ae\u4ef6",
        }
        return normalized not in generic_patterns and len(normalized) >= 8

    def _extract_weather_city(self, request: TaskRequest) -> str:
        city = str(request.get_input_value("city") or "").strip()
        if city:
            return city

        return extract_city_from_user_input(request.user_input) or ""

    def _build_email_context_from_meeting(self, meeting_output: dict[str, object]) -> str:
        summary = str(meeting_output.get("summary", "")).strip()
        tasks = meeting_output.get("tasks", [])
        lines = []
        if summary:
            lines.append(f"Meeting summary: {summary}")
        if isinstance(tasks, list) and tasks:
            lines.append("Tasks:")
            for item in tasks:
                if not isinstance(item, dict):
                    continue
                task_name = str(item.get("task_name", "")).strip()
                owner = str(item.get("owner", "")).strip()
                deadline = str(item.get("deadline", "")).strip()
                priority = str(item.get("priority", "")).strip()
                detail = task_name
                if owner:
                    detail += f" | owner: {owner}"
                if deadline:
                    detail += f" | deadline: {deadline}"
                if priority:
                    detail += f" | priority: {priority}"
                lines.append(f"- {detail}")
        return "\n".join(lines).strip()
