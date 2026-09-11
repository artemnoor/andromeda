"""Stable public contracts of the Admission Fit module."""

from ..domain.entities import ApplicantAdmissionProfile, ApplicantSubjectScore
from .requests import AdmissionFitRequest
from .results import (
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
    "AdmissionFitDataQuality",
    "AdmissionFitMetric",
    "AdmissionFitMetricStatus",
    "AdmissionFitReason",
    "AdmissionFitReasonKind",
    "AdmissionFitRequest",
    "AdmissionFitResult",
    "AdmissionFitStatus",
    "ApplicantAdmissionProfile",
    "ApplicantSubjectScore",
]
