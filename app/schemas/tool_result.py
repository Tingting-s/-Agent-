from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    tool_name: str = Field(..., description="Tool identifier.")
    status: Literal["success", "error"] = Field(..., description="Tool execution status.")
    message: str = Field(..., description="High-level tool message.")
    output: dict[str, Any] = Field(default_factory=dict, description="Structured tool output payload.")
    error: str | None = Field(default=None, description="Tool error details when execution fails.")
