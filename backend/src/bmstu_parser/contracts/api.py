from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints
from pydantic import TypeAdapter, ValidationError

from .constraints import (
    Credits,
    CurriculumId,
    CurriculumItemId,
    DisciplineId,
    DirectionCode,
    DirectionId,
    EducationYear,
    HourCount,
    NonEmptyText,
    ProgramCode,
    ProgramId,
    Semester,
    ShortText,
    Sha256,
    SourcePosition,
    UniversityId,
)
from .enums import AssessmentType, CompareStatus, EducationLevel, SourceKind
from .errors import ErrorResponse


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class ApiBase(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", populate_by_name=True, alias_generator=to_camel)


class SourceAttributionResponse(ApiBase):
    kind: SourceKind
    url: HttpUrl
    captured_at: datetime
    content_sha256: Sha256


class UniversityResponse(ApiBase):
    id: UniversityId
    name: NonEmptyText
    city: ShortText
    official_site: HttpUrl
    address: NonEmptyText


class DirectionResponse(ApiBase):
    id: DirectionId
    university_id: UniversityId
    code: DirectionCode
    name: NonEmptyText
    education_level: EducationLevel


class ProgramSummaryResponse(ApiBase):
    id: ProgramId
    direction_id: DirectionId
    code: ProgramCode
    name: NonEmptyText
    education_year: EducationYear
    study_plan_url: HttpUrl
    source_url: HttpUrl


class ProgramResponse(ApiBase):
    university: UniversityResponse
    direction: DirectionResponse
    program: ProgramSummaryResponse
    source: SourceAttributionResponse


class DisciplineResponse(ApiBase):
    id: DisciplineId
    name: NonEmptyText
    normalized_name: ShortText


class CurriculumMetadataResponse(ApiBase):
    id: CurriculumId
    program_id: ProgramId
    education_year: EducationYear
    source_url: HttpUrl
    captured_at: datetime


class CurriculumItemResponse(ApiBase):
    id: CurriculumItemId
    discipline: DisciplineResponse
    semester: Semester | None = None
    hours: HourCount
    credits: Credits | None = None
    assessment_types: tuple[AssessmentType, ...] | None = None
    source_position: SourcePosition | None = None


class CurriculumResponse(ApiBase):
    program: ProgramSummaryResponse
    curriculum: CurriculumMetadataResponse
    items: tuple[CurriculumItemResponse, ...] = Field(min_length=1)
    source: SourceAttributionResponse


class WorkloadResponse(ApiBase):
    semester: Semester | None = None
    hours: HourCount
    credits: Credits | None = None
    assessment_types: tuple[AssessmentType, ...] | None = None


class CompareRowResponse(ApiBase):
    discipline: DisciplineResponse
    semester: int | None = None
    a: WorkloadResponse | None = None
    b: WorkloadResponse | None = None
    status: CompareStatus


class CompareResponse(ApiBase):
    program_a: ProgramSummaryResponse
    program_b: ProgramSummaryResponse
    rows: tuple[CompareRowResponse, ...]
    sources: tuple[SourceAttributionResponse, ...] = Field(min_length=1)


ProgramIdsQuery = Annotated[str, StringConstraints(min_length=1, max_length=512)]


PublicError = ErrorResponse


def parse_program_ids(value: ProgramIdsQuery) -> tuple[ProgramId, ProgramId]:
    parts = tuple(part.strip() for part in value.split(","))
    if len(parts) != 2 or parts[0] == parts[1]:
        raise ValueError("programIds must contain exactly two distinct ids")
    adapter = TypeAdapter(ProgramId)
    try:
        return adapter.validate_python(parts[0]), adapter.validate_python(parts[1])
    except ValidationError as exc:
        raise ValueError("programIds must contain valid ProgramId values") from exc
