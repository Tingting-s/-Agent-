from __future__ import annotations

from pydantic import BaseModel, Field


class MeetingTaskItem(BaseModel):
    task_name: str = Field(..., description="Extracted meeting task name.")
    owner: str | None = Field(default=None, description="Responsible owner.")
    deadline: str | None = Field(default=None, description="Task deadline if provided.")
    priority: str | None = Field(default=None, description="Task priority if provided.")


class MeetingExtractResult(BaseModel):
    summary: str = Field(default="", description="Short meeting summary.")
    participants: list[str] = Field(default_factory=list, description="Meeting participants.")
    decisions: list[str] = Field(default_factory=list, description="Key meeting decisions.")
    tasks: list[MeetingTaskItem] = Field(default_factory=list, description="Extracted task items.")


class DocumentSummaryResult(BaseModel):
    summary: str = Field(..., description="Short document summary.")
    key_points: list[str] = Field(default_factory=list, description="Key points from the document.")
    risks: list[str] = Field(default_factory=list, description="Potential risks identified in the document.")


class EmailDraftResult(BaseModel):
    subject: str = Field(..., description="Email subject.")
    body: str = Field(..., description="Email body.")
    tone: str = Field(default="formal", description="Email tone.")
