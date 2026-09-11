from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TypeAlias

from pydantic import Field, HttpUrl

from ...shared.contracts.base import ContractModel

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class RawSourceSnapshot(ContractModel):
    source_kind: str = Field(min_length=1, max_length=128)
    requested_url: HttpUrl
    final_url: HttpUrl
    status_code: int = Field(strict=True, ge=200, le=599)
    content_type: str | None = Field(default=None, max_length=256)
    captured_at: datetime
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    body: bytes = Field(min_length=1)


class SourceLocator(ContractModel):
    source_url: HttpUrl
    page: int | None = Field(default=None, strict=True, ge=1)
    row: int | None = Field(default=None, strict=True, ge=1)
    field: str | None = Field(default=None, min_length=1, max_length=128)


class RawUniversityRecord(ContractModel):
    name: str = Field(min_length=1)
    city: str = Field(min_length=1)
    address: str = Field(min_length=1)
    official_site: HttpUrl
    locator: SourceLocator


class RawDirectionRecord(ContractModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    education_level: str = Field(min_length=1)
    locator: SourceLocator


class RawProgramRecord(ContractModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    direction_code: str = Field(min_length=1)
    education_level: str = Field(min_length=1)
    education_year: int = Field(strict=True, ge=2000, le=2100)
    study_plan_url: HttpUrl
    source_url: HttpUrl
    locator: SourceLocator


class RawCurriculumRow(ContractModel):
    program_code: str = Field(min_length=1)
    discipline: str = Field(min_length=1)
    semester: int | None = Field(default=None, strict=True, ge=1, le=12)
    hours: int = Field(strict=True, ge=0, le=2_000)
    credits: str | float | int | None = None
    assessment: str | None = None
    subject_group: str | None = None
    source_position: int | None = Field(default=None, strict=True, ge=1, le=10_000)
    source_url: HttpUrl
    locator: SourceLocator


class RawAdmissionExamRequirement(ContractModel):
    subject: str = Field(min_length=1, max_length=256)
    source_name: str = Field(min_length=1, max_length=256)
    minimum_score: Decimal | None = Field(default=None, strict=True, ge=0, le=100, max_digits=5, decimal_places=2)
    is_choice: bool = False
    is_required: bool = True


class RawAdmissionQuota(ContractModel):
    quota_type: str = Field(min_length=1, max_length=64)
    source_name: str = Field(min_length=1, max_length=256)
    places: int = Field(strict=True, ge=0, le=100_000)


class RawAdmissionPassingScore(ContractModel):
    score_type: str = Field(min_length=1, max_length=64)
    score: Decimal = Field(strict=True, ge=0, le=400, max_digits=6, decimal_places=2)


class RawAdmissionTuition(ContractModel):
    amount: Decimal = Field(strict=True, ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=1, max_length=16)
    academic_year: str | None = Field(default=None, min_length=4, max_length=32)
    period: str | None = Field(default=None, min_length=1, max_length=512)
    study_form: str | None = Field(default=None, min_length=1, max_length=64)
    is_discounted: bool = False


class RawAdmissionRecord(ContractModel):
    id: str = Field(min_length=1, max_length=384)
    program_code: str = Field(min_length=1, max_length=64)
    program_name: str | None = Field(default=None, min_length=1, max_length=512)
    admission_year: int = Field(strict=True, ge=2000, le=2100)
    study_form: str | None = Field(default=None, min_length=1, max_length=64)
    funding_type: str | None = Field(default=None, min_length=1, max_length=64)
    scope: str = Field(default="program", min_length=1, max_length=32)
    places: int | None = Field(default=None, strict=True, ge=0, le=100_000)
    exams: tuple[RawAdmissionExamRequirement, ...] = ()
    quotas: tuple[RawAdmissionQuota, ...] = ()
    passing_scores: tuple[RawAdmissionPassingScore, ...] = ()
    tuition: tuple[RawAdmissionTuition, ...] = ()
    source_kind: str = Field(min_length=1, max_length=256)
    source_url: HttpUrl
    locator: SourceLocator


class RawTracerBundle(ContractModel):
    snapshots: tuple[RawSourceSnapshot, ...] = Field(min_length=1)
    university: RawUniversityRecord
    direction: RawDirectionRecord
    programs: tuple[RawProgramRecord, ...] = Field(min_length=1)
    curriculum_rows: tuple[RawCurriculumRow, ...] = Field(min_length=1)
    admissions: tuple[RawAdmissionRecord, ...] = ()
