"""Public typed fingerprint contracts."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from proftest_spike.api_client.contracts import AssessmentType
from proftest_spike.domain.areas import AreaCode
from proftest_spike.domain.values import ZERO


class FingerprintModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)


class ActivityCode(StrEnum):
    ANALYTICAL = "analytical"
    SOFTWARE_CREATION = "software_creation"
    SYSTEM_DESIGN = "system_design"
    RESEARCH = "research"
    PHYSICAL_ENGINEERING = "physical_engineering"
    COMMUNICATION = "communication"
    CREATIVE = "creative"
    BUSINESS = "business"
    DATA = "data"


class CurriculumEvidence(FingerprintModel):
    source_name: str = Field(min_length=1, max_length=256)
    normalized_name: str = Field(min_length=1, max_length=256)
    hours: int = Field(strict=True, ge=0)
    credits: Decimal | None = Field(default=None, ge=ZERO)
    semester: int | None = Field(default=None, ge=1, le=12)
    subject_group: str = Field(min_length=1, max_length=256)
    assessment_types: tuple[AssessmentType, ...] | None = None
    workload: Decimal = Field(strict=True, ge=ZERO)
    area_weights: dict[AreaCode, Decimal]


class DistinctiveSubject(FingerprintModel):
    source_name: str = Field(min_length=1, max_length=256)
    normalized_name: str = Field(min_length=1, max_length=256)
    primary_area: AreaCode
    workload: Decimal = Field(strict=True, ge=ZERO)
    share: Decimal = Field(strict=True, ge=ZERO, le=1)
    rarity: Decimal = Field(strict=True, ge=ZERO, le=1)
    distinctiveness: Decimal = Field(strict=True, ge=ZERO, le=1)


class ProgramFingerprint(FingerprintModel):
    program_id: str = Field(min_length=1, max_length=128)
    program_code: str = Field(min_length=1, max_length=128)
    program_name: str = Field(min_length=1, max_length=512)
    basis: Literal["hours", "credits"]
    total_hours: int = Field(strict=True, ge=0)
    total_credits: Decimal = Field(strict=True, ge=ZERO)
    total_workload: Decimal = Field(strict=True, ge=ZERO)
    area_hours: dict[AreaCode, Decimal]
    area_share: dict[AreaCode, Decimal]
    subject_group_hours: dict[str, Decimal]
    subject_group_share: dict[str, Decimal]
    semester_distribution: dict[str, Decimal]
    activity_signals: dict[ActivityCode, Decimal]
    evidence: tuple[CurriculumEvidence, ...]
    distinctive_subjects: tuple[DistinctiveSubject, ...] = ()

    @model_validator(mode="after")
    def validate_vectors(self) -> Self:
        if self.total_workload > ZERO:
            for vector_name, vector in (
                ("area_share", self.area_share),
                ("subject_group_share", self.subject_group_share),
                ("semester_distribution", self.semester_distribution),
                ("activity_signals", self.activity_signals),
            ):
                if abs(sum(vector.values(), ZERO) - Decimal("1")) > Decimal("0.001"):
                    raise ValueError(f"{vector_name} must sum to one for a non-empty fingerprint")
        if self.basis == "hours" and self.total_workload != Decimal(self.total_hours):
            raise ValueError("hours basis must use total_hours as total_workload")
        if self.basis == "credits" and self.total_workload != self.total_credits:
            raise ValueError("credits basis must use total_credits as total_workload")
        return self


__all__ = [
    "ActivityCode",
    "CurriculumEvidence",
    "DistinctiveSubject",
    "FingerprintModel",
    "ProgramFingerprint",
]
