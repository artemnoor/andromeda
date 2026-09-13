"""Strict result contracts for the browser client."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode, DistinctiveSubject, ProgramFingerprint

from .catalog import CatalogProgramResponse, distinctive_response
from .common import ApiModel
from .questions import TestAnswersRequest


class ReasonResponse(ApiModel):
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


class ScoreBreakdownResponse(ApiModel):
    subject_fit: Decimal = Field(strict=True, ge=0, le=100)
    activity_fit: Decimal = Field(strict=True, ge=0, le=100)
    distinctive_fit: Decimal = Field(strict=True, ge=0, le=100)
    anti_penalty: Decimal = Field(strict=True, ge=0, le=100)
    raw_content_fit: Decimal = Field(strict=True, ge=-100, le=200)


class MetricResponse(ApiModel):
    code: Literal["workload_readiness", "career_fit", "admission_fit"]
    label: str = Field(min_length=1, max_length=128)
    value: int | None = Field(default=None, ge=0, le=100)
    status: Literal["not_available", "available"]


class RecommendationResponse(ApiModel):
    rank: int = Field(strict=True, ge=1)
    program: CatalogProgramResponse
    content_fit: int = Field(strict=True, ge=0, le=100)
    breakdown: ScoreBreakdownResponse
    reasons: tuple[ReasonResponse, ...]
    metrics: tuple[MetricResponse, ...]


class ResultsResponse(ApiModel):
    status: Literal["ready", "empty"]
    data_source: Literal["andromeda_http_api"]
    catalog_program_count: int = Field(strict=True, ge=0)
    profile_confidence: Decimal = Field(strict=True, ge=0, le=1)
    recommendations: tuple[RecommendationResponse, ...]
    note: str = Field(min_length=1, max_length=512)


def result_program(fingerprint: ProgramFingerprint) -> CatalogProgramResponse:
    return CatalogProgramResponse.model_validate(
        {
            "program_id": fingerprint.program_id,
            "program_code": fingerprint.program_code,
            "program_name": fingerprint.program_name,
            "basis": fingerprint.basis,
            "total_hours": fingerprint.total_hours,
            "total_credits": fingerprint.total_credits,
            "total_workload": fingerprint.total_workload,
            "area_share": fingerprint.area_share,
            "subject_group_share": fingerprint.subject_group_share,
            "semester_distribution": fingerprint.semester_distribution,
            "activity_signals": fingerprint.activity_signals,
            "distinctive_subjects": tuple(distinctive_response(subject) for subject in fingerprint.distinctive_subjects),
        }
    )


__all__ = [
    "MetricResponse",
    "ReasonResponse",
    "RecommendationResponse",
    "ResultsResponse",
    "ScoreBreakdownResponse",
    "TestAnswersRequest",
    "result_program",
]
