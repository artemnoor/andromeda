"""Typed reasons generated from the same score evidence."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode


class ExplanationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)


class Reason(ExplanationModel):
    kind: Literal["positive", "negative", "distinctive", "neutral"]
    code: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=256)
    detail: str = Field(min_length=1, max_length=1_000)
    area: AreaCode | None = None
    activity: ActivityCode | None = None
    workload: Decimal = Field(strict=True, ge=0)
    share: Decimal = Field(strict=True, ge=0, le=1)
    impact: Decimal = Field(strict=True, ge=-100, le=100)
    source_names: tuple[str, ...] = ()


__all__ = ["Reason"]
