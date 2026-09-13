"""Bootstrap contract combining public questions and static runtime metadata."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import ApiModel
from .questions import QuestionResponse


class BootstrapResponse(ApiModel):
    status: Literal["ready"]
    service: str = Field(min_length=1, max_length=128)
    test_version: str = Field(min_length=1, max_length=32)
    catalog_status: Literal["not_loaded"]
    data_source: Literal["andromeda_http_api"]
    questions: tuple[QuestionResponse, ...]
    total_base: int = Field(strict=True, ge=1)


__all__ = ["BootstrapResponse"]
