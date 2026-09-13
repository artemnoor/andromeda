"""Strict DTOs for the existing Andromeda read API.

These are Spike-owned contracts. They intentionally do not import ORM/domain
models from the main Andromeda application.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl

from proftest_spike.domain.areas import AreaCode


def to_camel(value: str) -> str:
    """Convert internal snake_case names to the public Andromeda JSON shape."""

    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class ApiModel(BaseModel):
    """Strict model base for every external DTO."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
        strict=True,
    )


class AssessmentType(StrEnum):
    EXAM = "exam"
    CREDIT = "credit"
    GRADED_CREDIT = "graded_credit"
    COURSEWORK = "coursework"
    COURSE_PROJECT = "course_project"
    STATE_EXAM = "state_exam"


class ProgramSummary(ApiModel):
    id: str = Field(min_length=1, max_length=128)
    direction_id: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=512)
    education_year: int = Field(strict=True, ge=2000, le=2200)
    study_plan_url: HttpUrl
    source_url: HttpUrl


class ProgramListResponse(ApiModel):
    items: tuple[ProgramSummary, ...]


class AreaWeight(ApiModel):
    # The current Andromeda API calls this field `code`; test fixtures and the
    # canonical Spike vocabulary use `area`. Accept both at this boundary.
    area: AreaCode = Field(validation_alias=AliasChoices("area", "code"))
    name: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=512)
    weight: Decimal = Field(strict=True, gt=Decimal("0"), le=Decimal("1"), max_digits=5, decimal_places=4)


class DisciplineSnapshot(ApiModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    normalized_name: str = Field(min_length=1, max_length=256)
    area_weights: tuple[AreaWeight, ...] = Field(min_length=1)
    primary_area: AreaCode


class CurriculumItem(ApiModel):
    id: str = Field(min_length=1, max_length=128)
    discipline: DisciplineSnapshot
    source_name: str = Field(min_length=1, max_length=256)
    semester: int | None = Field(default=None, ge=1, le=12)
    hours: int = Field(strict=True, ge=0, le=100_000)
    credits: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("1_000"), max_digits=8, decimal_places=4)
    assessment_types: tuple[AssessmentType, ...] | None = None
    subject_group: str | None = Field(default=None, min_length=1, max_length=256)
    source_position: int | None = Field(default=None, strict=True, ge=1)


class CurriculumResponse(ApiModel):
    program: ProgramSummary
    curriculum_id: str = Field(min_length=1, max_length=128)
    education_year: int = Field(strict=True, ge=2000, le=2200)
    source_url: HttpUrl
    captured_at: datetime
    items: tuple[CurriculumItem, ...]


class DisciplineAreaDefinition(ApiModel):
    code: AreaCode
    name: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=512)
    position: int = Field(strict=True, ge=1, le=22)


class DisciplineAreaCatalogResponse(ApiModel):
    items: tuple[DisciplineAreaDefinition, ...]


__all__ = [
    "ApiModel",
    "AreaWeight",
    "AssessmentType",
    "CurriculumItem",
    "CurriculumResponse",
    "DisciplineAreaCatalogResponse",
    "DisciplineAreaDefinition",
    "DisciplineSnapshot",
    "ProgramListResponse",
    "ProgramSummary",
    "to_camel",
]
