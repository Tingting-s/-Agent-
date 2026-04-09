from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.prompts.validator_prompt import VALIDATOR_SYSTEM_PROMPT
from app.schemas.response import TaskResponse


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    payload: dict[str, Any] | None = None
    error_message: str | None = None
    retryable: bool = True


class ValidatorAgent:
    def __init__(self, system_prompt: str = VALIDATOR_SYSTEM_PROMPT) -> None:
        self.system_prompt = system_prompt

    def validate(self, content: str) -> ValidationResult:
        raw_content = content.strip()
        if not raw_content:
            return ValidationResult(
                is_valid=False,
                error_message="Generated response is empty.",
                retryable=True,
            )

        try:
            payload = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            return ValidationResult(
                is_valid=False,
                error_message=f"Generated response is not valid JSON: {exc.msg}.",
                retryable=True,
            )

        if not isinstance(payload, dict):
            return ValidationResult(
                is_valid=False,
                error_message="Generated response must be a JSON object.",
                retryable=True,
            )

        missing_fields = [
            field
            for field in ("task_type", "status", "structured_result")
            if field not in payload or payload[field] is None or payload[field] == ""
        ]
        if missing_fields:
            return ValidationResult(
                is_valid=False,
                payload=payload,
                error_message=f"Generated response is missing required fields: {', '.join(missing_fields)}.",
                retryable=True,
            )

        if not isinstance(payload["structured_result"], dict):
            return ValidationResult(
                is_valid=False,
                payload=payload,
                error_message="structured_result must be a JSON object.",
                retryable=True,
            )

        if not payload.get("message"):
            payload["message"] = "Unable to generate a detailed message, returning the available result."

        try:
            TaskResponse.model_validate(
                {
                    "task_type": payload["task_type"],
                    "status": payload["status"],
                    "message": payload["message"],
                    "structured_result": payload["structured_result"],
                    "retry_count": payload.get("retry_count", 0),
                }
            )
        except ValidationError as exc:
            return ValidationResult(
                is_valid=False,
                payload=payload,
                error_message=f"Generated response failed schema validation: {exc.errors()[0]['msg']}.",
                retryable=True,
            )

        return ValidationResult(
            is_valid=True,
            payload=payload,
            error_message=None,
            retryable=False,
        )
