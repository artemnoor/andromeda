"""Explainable channel-neutral analytics results."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import DirectionId, ProgramId, UniversityId
from andromeda.shared.contracts.provenance import SourceAttribution, SourceGapReference
from andromeda.shared.contracts.versions import ANALYTICS_PROJECTION_SCHEMA_VERSION

from .metrics import MetricDefinition
from .public import ProjectionDataQuality, ProjectionMetric, ProjectionMetricEvidence
from .query import QuerySpec


class AnalyticsResultStatus(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    INSUFFICIENT_DATA = "insufficient_data"
    UNAVAILABLE = "unavailable"


class AnalyticsRow(ContractModel):
    entity_id: str
    university_id: UniversityId | None = None
    direction_id: DirectionId | None = None
    program_ids: tuple[ProgramId, ...] = Field(default=(), max_length=100)
    metrics: dict[str, ProjectionMetric]
    quality: ProjectionDataQuality
    evidence: tuple[ProjectionMetricEvidence, ...] = Field(default=(), max_length=1000)


class AnalyticsResult(ContractModel):
    query: QuerySpec
    rows: tuple[AnalyticsRow, ...] = Field(default=(), max_length=100)
    metric_definitions: tuple[MetricDefinition, ...] = Field(default=(), max_length=8)
    status: AnalyticsResultStatus
    coverage: Decimal = Field(strict=True, ge=Decimal("0"), le=Decimal("1"))
    confidence: Decimal = Field(strict=True, ge=Decimal("0"), le=Decimal("1"))
    projection_schema_version: str = ANALYTICS_PROJECTION_SCHEMA_VERSION
    semantic_versions: tuple[str, ...] = ()
    classifier_versions: tuple[str, ...] = ()
    provenance: tuple[SourceAttribution, ...] = Field(default=(), max_length=1000)
    source_gaps: tuple[SourceGapReference, ...] = Field(default=(), max_length=1000)


__all__ = ["AnalyticsResult", "AnalyticsResultStatus", "AnalyticsRow"]
