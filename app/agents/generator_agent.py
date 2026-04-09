from __future__ import annotations

import json
from typing import Any

from app.prompts.generator_prompt import GENERATOR_SYSTEM_PROMPT


class GeneratorAgent:
    def __init__(self) -> None:
        self.system_prompt = GENERATOR_SYSTEM_PROMPT

    def generate(
        self,
        *,
        task_type: str,
        status: str,
        structured_result: dict[str, Any] | None,
        message: str | None = None,
        fallback_message: str | None = None,
    ) -> str:
        payload = {
            "task_type": task_type,
            "status": status,
            "message": self._build_message(
                task_type=task_type,
                status=status,
                message=message,
                fallback_message=fallback_message,
            ),
            "structured_result": dict(structured_result or {}),
        }
        return json.dumps(payload, ensure_ascii=False)

    def _build_message(
        self,
        *,
        task_type: str,
        status: str,
        message: str | None,
        fallback_message: str | None,
    ) -> str:
        normalized_message = (message or "").strip()
        if normalized_message:
            return normalized_message

        if status == "success":
            return f"Completed {task_type} successfully."
        if status == "need_more_info":
            return fallback_message or f"More information is required before {task_type} can be completed."
        return fallback_message or f"Unable to complete {task_type}. Returning the safest fallback response."
