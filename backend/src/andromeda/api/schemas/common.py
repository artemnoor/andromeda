from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from andromeda.shared.contracts.enums import AssessmentType, CompareStatus, ComparisonScope, EducationLevel


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class ApiModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", populate_by_name=True, alias_generator=to_camel)


class ProgramSummaryResponse(ApiModel):
    id: str
    direction_id: str
    code: str
    name: str
    education_year: int
    study_plan_url: HttpUrl
    source_url: HttpUrl


class ProgramListResponse(ApiModel):
    items: tuple[ProgramSummaryResponse, ...]


class ProgramResponse(ApiModel):
    program: ProgramSummaryResponse


class DisciplineResponse(ApiModel):
    id: str
    name: str
    normalized_name: str


class CurriculumItemResponse(ApiModel):
    id: str
    discipline: DisciplineResponse
    source_name: str
    semester: int | None = None
    hours: int
    credits: Decimal | None = None
    assessment_types: tuple[AssessmentType, ...] | None = None
    subject_group: str | None = None
    source_position: int | None = None


class CurriculumResponse(ApiModel):
    program: ProgramSummaryResponse
    curriculum_id: str
    education_year: int
    source_url: HttpUrl
    captured_at: datetime
    items: tuple[CurriculumItemResponse, ...]


class WorkloadResponse(ApiModel):
    semester: int | None = None
    hours: int
    credits: Decimal | None = None
    assessment_types: tuple[AssessmentType, ...] | None = None
    subject_group: str | None = None


class ComparisonRowResponse(ApiModel):
    discipline: DisciplineResponse
    semester: int | None = None
    subject_group: str | None = None
    a: WorkloadResponse | None = None
    b: WorkloadResponse | None = None
    status: CompareStatus
    hours_delta: int | None = None
    credits_delta: Decimal | None = None


class ComparisonTotalsResponse(ApiModel):
    hours: int
    credits: Decimal


class ComparisonBlockResponse(ApiModel):
    name: str
    totals_a: ComparisonTotalsResponse
    totals_b: ComparisonTotalsResponse
    hours_delta: int
    credits_delta: Decimal


class ComparisonResponse(ApiModel):
    program_a: ProgramSummaryResponse
    program_b: ProgramSummaryResponse
    scope: ComparisonScope
    semester: int | None = None
    rows: tuple[ComparisonRowResponse, ...]
    totals_a: ComparisonTotalsResponse
    totals_b: ComparisonTotalsResponse
    blocks: tuple[ComparisonBlockResponse, ...]
