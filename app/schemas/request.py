from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    user_input: str = Field(..., description="Raw user input for the task.")
    task_type: str | None = Field(default=None, description="Optional task type hint.")
    context: dict[str, Any] | None = Field(default=None, description="Optional execution context.")
    additional_inputs: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured inputs that take priority over free-form text parsing.",
    )

    def get_context(self) -> dict[str, Any]:
        return self.context or {}

    def get_additional_inputs(self) -> dict[str, Any]:
        return self.additional_inputs or {}

    def get_input_value(self, key: str) -> Any:
        additional_inputs = self.get_additional_inputs()
        if key in additional_inputs and additional_inputs[key] not in (None, ""):
            return additional_inputs[key]

        context = self.get_context()
        if key in context and context[key] not in (None, ""):
            return context[key]

        return None
