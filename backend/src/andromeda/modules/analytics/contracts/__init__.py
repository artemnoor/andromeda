"""Stable public contracts of the analytics module."""

from .metrics import MetricAggregation, MetricDefinition, MetricDomain, MetricEntityType
from .public import (
    ActivitySignalCode,
    AssessmentSummary,
    ProgramProjection,
    ProjectionBuild,
    ProjectionDataQuality,
    ProjectionDataQualityStatus,
    ProjectionMetric,
    ProjectionMetricEvidence,
    ProjectionTimeline,
    WorkloadSummary,
)
from .results import AnalyticsResult, AnalyticsResultStatus, AnalyticsRow

__all__ = [
    "ActivitySignalCode",
    "AssessmentSummary",
    "ProjectionDataQuality",
    "ProjectionDataQualityStatus",
    "ProjectionBuild",
    "ProjectionMetric",
    "ProjectionMetricEvidence",
    "ProjectionTimeline",
    "ProgramProjection",
    "WorkloadSummary",
    "MetricAggregation",
    "MetricDefinition",
    "MetricDomain",
    "MetricEntityType",
    "AnalyticsResult",
    "AnalyticsResultStatus",
    "AnalyticsRow",
]
