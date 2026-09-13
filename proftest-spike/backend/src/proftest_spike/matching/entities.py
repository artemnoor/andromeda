"""Internal and future-public matching contracts."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from proftest_spike.program_fingerprints.entities import ProgramFingerprint


class MatchingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)


class ScoreBreakdown(MatchingModel):
    subject_fit: Decimal = Field(strict=True, ge=0, le=100)
    activity_fit: Decimal = Field(strict=True, ge=0, le=100)
    distinctive_fit: Decimal = Field(strict=True, ge=0, le=100)
    anti_penalty: Decimal = Field(strict=True, ge=0, le=100)
    raw_content_fit: Decimal = Field(strict=True, ge=-100, le=200)


class MatchScore(MatchingModel):
    program_id: str = Field(min_length=1, max_length=128)
    program_code: str = Field(min_length=1, max_length=128)
    content_fit: int = Field(strict=True, ge=0, le=100)
    breakdown: ScoreBreakdown


class Metric(MatchingModel):
    code: Literal["workload_readiness", "career_fit", "admission_fit"]
    label: str = Field(min_length=1, max_length=128)
    value: int | None = Field(default=None, ge=0, le=100)
    status: Literal["not_available", "available"]


class Recommendation(MatchingModel):
    program: ProgramFingerprint
    score: MatchScore
    reasons: tuple[object, ...]
    metrics: tuple[Metric, ...]


__all__ = ["MatchScore", "Metric", "Recommendation", "ScoreBreakdown"]
