"""API schemas for adaptive preview."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from proftest_spike.adaptive.entities import AdaptiveQuestion, AdaptiveSelection

from .common import ApiModel
from .questions import TestAnswersRequest


class AdaptiveDimensionResponse(ApiModel):
    code: str = Field(min_length=3, max_length=128)
    label: str = Field(min_length=1, max_length=256)
    kind: Literal["area", "activity"]
    spread: Decimal = Field(strict=True, ge=0, le=1)
    significance: Decimal = Field(strict=True, ge=0, le=1)


class AdaptiveOptionResponse(ApiModel):
    id: Literal["more_first", "balanced", "more_second"]
    label: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=512)


class AdaptiveQuestionResponse(ApiModel):
    id: str = Field(min_length=1, max_length=256)
    prompt: str = Field(min_length=1, max_length=1_000)
    helper_text: str = Field(min_length=1, max_length=512)
    first_dimension: AdaptiveDimensionResponse
    second_dimension: AdaptiveDimensionResponse
    options: tuple[AdaptiveOptionResponse, ...] = Field(min_length=3, max_length=3)


class AdaptiveResponse(ApiModel):
    status: Literal["ready", "skipped"]
    reason: str | None = Field(default=None, max_length=512)
    candidate_count: int = Field(strict=True, ge=0)
    top_candidate_count: int = Field(strict=True, ge=0)
    question: AdaptiveQuestionResponse | None = None


class ProgressResponse(ApiModel):
    answered_base: int = Field(strict=True, ge=0)
    total_base: int = Field(strict=True, ge=0)
    answered_adaptive: int = Field(strict=True, ge=0)
    total_steps: int = Field(strict=True, ge=1)


class PreviewResponse(ApiModel):
    status: Literal["ready", "empty"]
    catalog_program_count: int = Field(strict=True, ge=0)
    profile_confidence: Decimal = Field(strict=True, ge=0, le=1)
    adaptive: AdaptiveResponse | None = None
    progress: ProgressResponse


def adaptive_response(selection: AdaptiveSelection, question: AdaptiveQuestionResponse | None) -> AdaptiveResponse:
    return AdaptiveResponse(
        status=selection.status,
        reason=selection.reason,
        candidate_count=selection.candidate_count,
        top_candidate_count=selection.top_candidate_count,
        question=question,
    )


__all__ = [
    "AdaptiveDimensionResponse",
    "AdaptiveOptionResponse",
    "AdaptiveQuestionResponse",
    "AdaptiveResponse",
    "PreviewResponse",
    "ProgressResponse",
    "adaptive_response",
]
