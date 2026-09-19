"""Stable contracts shared by the admissions module and its adapters."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import Field, HttpUrl, model_validator

from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import EducationYear, NonEmptyText, ProgramId, ShortText, SourceHash


ZERO = Decimal("0")


class StudyForm(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    EVENING = "evening"
    ONLINE = "online"
    UNKNOWN = "unknown"


class FundingType(StrEnum):
    BUDGET = "budget"
    PAID = "paid"
    TARGETED = "targeted"
    UNKNOWN = "unknown"


class AdmissionScope(StrEnum):
    PROGRAM = "program"
    DIRECTION = "direction"


class QuotaType(StrEnum):
    SPECIAL = "special"
    SEPARATE = "separate"
    TARGETED = "targeted"
    OTHER = "other"


class PassingScoreType(StrEnum):
    BUDGET = "budget"
    PAID = "paid"
    AVERAGE = "average"
    OTHER = "other"


class AdmissionCompetitionType(StrEnum):
    GENERAL = "general"
    SPECIAL_QUOTA = "special_quota"
    SEPARATE_QUOTA = "separate_quota"
    TARGETED = "targeted"
    BVI = "bvi"
    OTHER = "other"


class PassingScoreStatus(StrEnum):
    NUMERIC = "numeric"
    BVI = "bvi"


class AdmissionProvenance(ContractModel):
    source_kind: ShortText
    source_url: HttpUrl
    captured_at: datetime
    content_sha256: SourceHash
    locator: ShortText | None = None
    source_name: NonEmptyText | None = None
    university_id: str | None = None
    run_id: str | None = None
    field: ShortText | None = None
    record_key: ShortText | None = None
    inferred: bool = False


class ExamRequirement(ContractModel):
    subject: NonEmptyText
    source_name: NonEmptyText
    minimum_score: Decimal | None = Field(default=None, strict=True, ge=ZERO, le=Decimal("100"), max_digits=5, decimal_places=2)
    is_choice: bool = False
    is_required: bool = True
    provenance: AdmissionProvenance


class Quota(ContractModel):
    quota_type: QuotaType
    source_name: NonEmptyText
    places: int = Field(strict=True, ge=0, le=100_000)
    provenance: AdmissionProvenance


class PassingScore(ContractModel):
    score_type: PassingScoreType
    competition_type: AdmissionCompetitionType = AdmissionCompetitionType.GENERAL
    status: PassingScoreStatus = PassingScoreStatus.NUMERIC
    score: Decimal | None = Field(default=None, strict=True, ge=ZERO, le=Decimal("400"), max_digits=6, decimal_places=2)
    provenance: AdmissionProvenance

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        if self.status is PassingScoreStatus.NUMERIC and self.score is None:
            raise ValueError("numeric passing score must contain score")
        if self.status is PassingScoreStatus.BVI:
            if self.score is not None:
                raise ValueError("BVI passing score must not contain score")
            if self.competition_type not in {
                AdmissionCompetitionType.BVI,
                AdmissionCompetitionType.SPECIAL_QUOTA,
                AdmissionCompetitionType.SEPARATE_QUOTA,
                AdmissionCompetitionType.TARGETED,
            }:
                raise ValueError("BVI passing score must use a BVI or quota competition type")
        return self


class TuitionCost(ContractModel):
    amount: Decimal = Field(strict=True, ge=ZERO, max_digits=12, decimal_places=2)
    currency: ShortText
    academic_year: str | None = Field(default=None, min_length=4, max_length=32)
    period: NonEmptyText | None = None
    study_form: StudyForm | None = None
    is_discounted: bool = False
    provenance: AdmissionProvenance


class AdmissionOffering(ContractModel):
    id: NonEmptyText
    program_id: ProgramId
    admission_year: EducationYear
    study_form: StudyForm | None = None
    funding_type: FundingType | None = None
    scope: AdmissionScope
    places: int | None = Field(default=None, strict=True, ge=0, le=100_000)
    exams: tuple[ExamRequirement, ...] = ()
    quotas: tuple[Quota, ...] = ()
    passing_scores: tuple[PassingScore, ...] = ()
    tuition: tuple[TuitionCost, ...] = ()
    provenance: tuple[AdmissionProvenance, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if not self.id.startswith("admission-offering:"):
            raise ValueError("admission offering id must use the admission-offering namespace")
        if self.funding_type is FundingType.BUDGET and self.tuition:
            raise ValueError("budget offering cannot contain tuition costs")
        if self.funding_type is FundingType.PAID and self.places is not None and self.places < 0:
            raise ValueError("paid offering places cannot be negative")
        return self


class ProgramAdmissions(ContractModel):
    """All source-backed admission facts currently known for one program."""

    program_id: ProgramId
    offerings: tuple[AdmissionOffering, ...] = ()

    @model_validator(mode="after")
    def validate_program_identity(self) -> Self:
        if any(offering.program_id != self.program_id for offering in self.offerings):
            raise ValueError("all admission offerings must belong to the envelope program")
        ids = tuple(offering.id for offering in self.offerings)
        if len(ids) != len(set(ids)):
            raise ValueError("admission offerings must have unique ids")
        return self


__all__ = [
    "AdmissionOffering",
    "AdmissionCompetitionType",
    "AdmissionProvenance",
    "AdmissionScope",
    "ExamRequirement",
    "FundingType",
    "PassingScore",
    "PassingScoreStatus",
    "ProgramAdmissions",
    "Quota",
    "PassingScoreType",
    "QuotaType",
    "StudyForm",
    "TuitionCost",
]
