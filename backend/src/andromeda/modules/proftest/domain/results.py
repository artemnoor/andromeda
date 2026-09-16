"""Result value objects shared by proftest services and API adapters."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import NonEmptyText, ProgramCode, ProgramId, ShortText

from .adaptive import AdaptiveSelection
from .entities import ActivityCode, ProgramFingerprint, Question, UserProfile


class MetricStatus(StrEnum):
    NOT_AVAILABLE = "not_available"


class ReasonKind(StrEnum):
    FIT = "fit"
    ANTI_FIT = "anti_fit"


class OptionalMetric(ContractModel):
    status: MetricStatus = MetricStatus.NOT_AVAILABLE
    value: int | None = Field(default=None, strict=True, ge=0, le=100)


class ScoreBreakdown(ContractModel):
    subject_fit: Decimal = Field(strict=True, ge=0, le=100)
    activity_fit: Decimal = Field(strict=True, ge=0, le=100)
    distinctive_fit: Decimal = Field(strict=True, ge=0, le=100)
    anti_penalty: Decimal = Field(strict=True, ge=0, le=100)
    raw_content_fit: Decimal


class MatchScore(ContractModel):
    program_id: ProgramId
    program_code: ProgramCode
    content_fit: int = Field(strict=True, ge=0, le=100)
    breakdown: ScoreBreakdown


class MatchReason(ContractModel):
    kind: ReasonKind
    area: DisciplineAreaCode | None = None
    activity: ActivityCode | None = None
    text: NonEmptyText
    workload: Decimal = Field(strict=True, ge=0)
    share: Decimal = Field(strict=True, ge=0, le=1, max_digits=7, decimal_places=4)
    source_names: tuple[ShortText, ...] = ()


class Recommendation(ContractModel):
    program_id: ProgramId
    program_code: ProgramCode
    program_name: NonEmptyText
    content_fit: int = Field(strict=True, ge=0, le=100)
    score: MatchScore
    reasons: tuple[MatchReason, ...] = ()
    anti_fit_reasons: tuple[MatchReason, ...] = ()
    area_share: dict[DisciplineAreaCode, Decimal] = Field(default_factory=dict)
    semester_distribution: dict[str, Decimal] = Field(default_factory=dict)
    distinctive_subjects: tuple[str, ...] = ()
    workload_readiness: OptionalMetric = Field(default_factory=OptionalMetric)
    career_fit: OptionalMetric = Field(default_factory=OptionalMetric)
    admission_fit: OptionalMetric = Field(default_factory=OptionalMetric)

    @classmethod
    def from_fingerprint(cls, fingerprint: ProgramFingerprint, score: MatchScore) -> "Recommendation":
        return cls(
            program_id=fingerprint.program_id,
            program_code=fingerprint.program_code,
            program_name=fingerprint.program_name,
            content_fit=score.content_fit,
            score=score,
            area_share=fingerprint.area_share,
            semester_distribution=fingerprint.semester_distribution,
            distinctive_subjects=tuple(subject.source_name for subject in fingerprint.distinctive_subjects),
        )


class PreviewCandidate(ContractModel):
    program_id: ProgramId
    program_code: ProgramCode
    content_fit: int = Field(strict=True, ge=0, le=100)


class ProftestPreview(ContractModel):
    profile: UserProfile
    adaptive: AdaptiveSelection
    question: Question | None = None
    candidates: tuple[PreviewCandidate, ...] = ()


class ProftestResults(ContractModel):
    profile: UserProfile
    recommendations: tuple[Recommendation, ...] = ()


__all__ = [
    "MatchReason",
    "MatchScore",
    "MetricStatus",
    "OptionalMetric",
    "PreviewCandidate",
    "ProftestPreview",
    "ProftestResults",
    "ReasonKind",
    "Recommendation",
    "ScoreBreakdown",
]
