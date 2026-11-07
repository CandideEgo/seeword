"""Tutor conversation wire shapes; a chat is not a grading fact."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="", max_length=120)


class ConversationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, max_length=120)
    status: Literal["active", "archived"] | None = None


class ConversationTask(BaseModel):
    session_id: str
    status: str
    created_at: datetime


class ConversationSummary(BaseModel):
    id: str
    title: str
    status: str
    kind: str
    created_at: datetime
    updated_at: datetime
    tasks: list[ConversationTask] = Field(default_factory=list)


class ConversationPage(BaseModel):
    items: list[ConversationSummary]
    page: int
    page_size: int
    has_more: bool


class SendMessage(BaseModel):
    """A task-bound turn keeps the legacy optimistic-concurrency contract."""

    model_config = ConfigDict(extra="forbid")
    operation_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    expected_revision: int | None = Field(default=None, ge=1)
