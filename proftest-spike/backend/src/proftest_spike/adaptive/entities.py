"""Typed adaptive-selection contracts."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AdaptiveModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)


class AdaptiveDimension(AdaptiveModel):
    code: str = Field(min_length=3, max_length=128)
    label: str = Field(min_length=1, max_length=256)
    kind: Literal["area", "activity"]
    spread: Decimal = Field(strict=True, ge=0, le=1)
    significance: Decimal = Field(strict=True, ge=0, le=1)


class AdaptiveOption(AdaptiveModel):
    id: Literal["more_first", "balanced", "more_second"]
    label: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=512)
    first_weight: Decimal = Field(strict=True, ge=0, le=1)
    second_weight: Decimal = Field(strict=True, ge=0, le=1)


class AdaptiveQuestion(AdaptiveModel):
    id: str = Field(min_length=1, max_length=256)
    prompt: str = Field(min_length=1, max_length=1_000)
    helper_text: str = Field(min_length=1, max_length=512)
    first_dimension: AdaptiveDimension
    second_dimension: AdaptiveDimension
    options: tuple[AdaptiveOption, ...] = Field(min_length=3, max_length=3)


class AdaptiveSelection(AdaptiveModel):
    status: Literal["ready", "skipped"]
    reason: str | None = Field(default=None, max_length=512)
    candidate_count: int = Field(strict=True, ge=0)
    top_candidate_count: int = Field(strict=True, ge=0)
    dimensions: tuple[AdaptiveDimension, ...] = ()
    question: AdaptiveQuestion | None = None


__all__ = ["AdaptiveDimension", "AdaptiveOption", "AdaptiveQuestion", "AdaptiveSelection"]
