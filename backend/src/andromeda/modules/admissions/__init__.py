"""Admissions domain module public surface."""

from .contracts.public import (
    AdmissionOffering,
    AdmissionProvenance,
    ExamRequirement,
    FundingType,
    PassingScore,
    PassingScoreType,
    ProgramAdmissions,
    Quota,
    QuotaType,
    StudyForm,
    TuitionCost,
)
from .repository.ports import AdmissionReader, AdmissionRepository, AdmissionWriter

__all__ = [
    "AdmissionOffering",
    "AdmissionProvenance",
    "AdmissionReader",
    "AdmissionRepository",
    "AdmissionWriter",
    "ExamRequirement",
    "FundingType",
    "PassingScore",
    "PassingScoreType",
    "ProgramAdmissions",
    "Quota",
    "QuotaType",
    "StudyForm",
    "TuitionCost",
]
