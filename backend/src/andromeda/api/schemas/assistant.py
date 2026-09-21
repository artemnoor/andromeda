"""Strict HTTP DTOs for the channel-neutral assistant endpoint."""

from __future__ import annotations

from pydantic import Field

from .common import ApiModel


class AssistantQueryRequest(ApiModel):
    text: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, pattern=r"^query-session:[0-9a-f]{32}$")
    expected_revision: int | None = Field(default=None, ge=1)
    interactive: bool = False


__all__ = ["AssistantQueryRequest"]
