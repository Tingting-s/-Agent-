from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.task_result import (
    DocumentSummaryResult,
    EmailDraftResult,
    MeetingExtractResult,
)
from app.services.retry_service import default_retry_decorator


class LLMServiceError(RuntimeError):
    """Base exception for LLM service failures."""


class LLMRequestError(LLMServiceError):
    """Raised when the remote LLM request fails."""


class LLMResponseParseError(LLMServiceError):
    """Raised when the model response cannot be parsed or validated."""


class QwenLLMService:
    def __init__(self, client: Any | None = None) -> None:
        self.settings = get_settings()
        self.model_name = self.settings.QWEN_MODEL
        self.timeout = self.settings.LLM_TIMEOUT
        self._client = client

    def generate_email(self, subject: str, purpose: str, context: str, tone: str) -> dict[str, Any]:
        payload = self._request_json(
            system_prompt=(
                "You are an office assistant. Return JSON only. "
                "Generate a professional email draft based on the user's request. "
                'The JSON object must contain exactly these top-level fields: "subject", "body", "tone".'
            ),
            user_prompt=(
                f"Subject: {subject}\n"
                f"Purpose: {purpose}\n"
                f"Context: {context}\n"
                f"Tone: {tone}\n"
                "Return valid JSON only."
            ),
        )
        return self._validate_payload(EmailDraftResult, payload, "Email draft")

    def extract_meeting_tasks(self, meeting_text: str) -> dict[str, Any]:
        payload = self._request_json(
            system_prompt=(
                "You are an office assistant that extracts structured meeting results. "
                "Return JSON only. "
                'Required top-level fields: "summary", "participants", "decisions", "tasks". '
                'The "tasks" field must be a list. Each task item must contain '
                '"task_name", "owner", "deadline", "priority". '
                "Use empty strings when a task field is not explicitly provided. "
                "Use empty arrays when participants, decisions, or tasks are missing."
            ),
            user_prompt=(
                "Extract meeting tasks from the following meeting notes and return valid JSON only:\n"
                f"{meeting_text}"
            ),
        )
        return self._validate_payload(MeetingExtractResult, payload, "Meeting extraction")

    def summarize_document(self, content: str) -> dict[str, Any]:
        payload = self._request_json(
            system_prompt=(
                "You are an office assistant that summarizes documents. "
                "Return JSON only. "
                'Required top-level fields: "summary", "key_points", "risks". '
                'The "key_points" field must be a list of concise strings. '
                'The "risks" field must be a list of concise strings.'
            ),
            user_prompt=(
                "Summarize the following document and return valid JSON only:\n"
                f"{content}"
            ),
        )
        return self._validate_payload(DocumentSummaryResult, payload, "Document summary")

    def _get_client(self) -> Any:
        if self._client is None:
            api_key = self.settings.DASHSCOPE_API_KEY.strip()
            if not api_key:
                raise LLMServiceError(
                    "DASHSCOPE_API_KEY is not configured. Please update your .env file before using text tools."
                )
            self._client = OpenAI(
                api_key=api_key,
                base_url=self.settings.DASHSCOPE_BASE_URL,
                timeout=self.timeout,
            )
        return self._client

    @default_retry_decorator(attempts=3, wait_seconds=1, retry_on=LLMRequestError)
    def _create_chat_completion(self, messages: list[dict[str, str]]) -> str:
        try:
            response = self._get_client().chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
        except LLMServiceError:
            raise
        except Exception as exc:
            raise LLMRequestError(
                f"Failed to call Qwen model '{self.model_name}' via DashScope: {exc}"
            ) from exc

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, KeyError, TypeError) as exc:
            raise LLMRequestError("The Qwen API response did not include a valid message payload.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMRequestError("The Qwen model returned an empty response.")
        return content

    def _request_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        raw_content = self._create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return self._parse_json_response(raw_content)

    def _parse_json_response(self, raw_content: str) -> dict[str, Any]:
        cleaned_content = self._strip_markdown_code_fence(raw_content).strip()
        candidates = [cleaned_content]

        start_index = cleaned_content.find("{")
        end_index = cleaned_content.rfind("}")
        if start_index != -1 and end_index != -1 and end_index > start_index:
            extracted = cleaned_content[start_index : end_index + 1]
            if extracted != cleaned_content:
                candidates.append(extracted)

        for candidate in candidates:
            if not candidate:
                continue
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload

        raise LLMResponseParseError(
            "The Qwen model returned content that could not be parsed as JSON. "
            "Please try again with clearer input."
        )

    def _strip_markdown_code_fence(self, raw_content: str) -> str:
        match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", raw_content.strip(), flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
        return raw_content

    def _validate_payload(
        self,
        schema_model: type[EmailDraftResult] | type[MeetingExtractResult] | type[DocumentSummaryResult],
        payload: dict[str, Any],
        label: str,
    ) -> dict[str, Any]:
        try:
            validated = schema_model.model_validate(payload)
        except ValidationError as exc:
            missing_fields = sorted(
                {
                    ".".join(str(part) for part in error["loc"])
                    for error in exc.errors()
                    if error.get("loc")
                }
            )
            raise LLMResponseParseError(
                f"{label} response is missing required JSON fields or contains invalid values: "
                f"{', '.join(missing_fields)}."
            ) from exc
        return validated.model_dump()


@lru_cache
def get_qwen_llm_service() -> QwenLLMService:
    return QwenLLMService()
