"""Stable public contracts of the Admission Fit module."""

from __future__ import annotations

from typing import Protocol

from ..domain.entities import ApplicantAdmissionProfile, ApplicantSubjectScore
from .requests import AdmissionFitRequest, BatchAdmissionFitRequest
from .results import (
    BatchAdmissionFitOutcome,
    BatchAdmissionFitResult,
    AdmissionFitBreakdown,
    AdmissionFitDataQuality,
    AdmissionFitMetric,
    AdmissionFitMetricStatus,
    AdmissionFitReason,
    AdmissionFitReasonKind,
    AdmissionFitResult,
    AdmissionFitStatus,
)

__all__ = [
    "AdmissionFitBreakdown",
    "BatchAdmissionFitOutcome",
    "BatchAdmissionFitRequest",
    "BatchAdmissionFitResult",
    "AdmissionFitDataQuality",
    "AdmissionFitMetric",
    "AdmissionFitMetricStatus",
    "AdmissionFitReason",
    "AdmissionFitReasonKind",
    "AdmissionFitRequest",
    "AdmissionFitResult",
    "AdmissionFitStatus",
    "AdmissionFitBatchEvaluator",
    "ApplicantAdmissionProfile",
    "ApplicantSubjectScore",
]


class AdmissionFitBatchEvaluator(Protocol):
    """Public batch evaluator consumed by candidate orchestration."""

    def evaluate_batch(self, request: BatchAdmissionFitRequest) -> BatchAdmissionFitResult: ...
