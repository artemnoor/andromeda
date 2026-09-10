from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from .constraints import (
    Credits,
    CurriculumId,
    CurriculumItemId,
    DirectionCode,
    DirectionId,
    DisciplineId,
    EducationYear,
    HourCount,
    NonEmptyText,
    ProgramCode,
    ProgramId,
    Sha256,
    Semester,
    SourcePosition,
    ShortText,
    UniversityId,
)
from .enums import AssessmentType, CompareStatus, EducationLevel, SourceKind


class DomainBase(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", populate_by_name=True)


class University(DomainBase):
    id: UniversityId
    name: NonEmptyText
    city: ShortText
    official_site: HttpUrl
    address: NonEmptyText


class Direction(DomainBase):
    id: DirectionId
    university_id: UniversityId
    code: DirectionCode
    name: NonEmptyText
    education_level: EducationLevel

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.id != f"direction:{self.code}":
            raise ValueError("direction id must equal direction:<code>")
        return self


class EducationalProgram(DomainBase):
    id: ProgramId
    direction_id: DirectionId
    code: ProgramCode
    name: NonEmptyText
    education_year: EducationYear
    study_plan_url: HttpUrl
    source_url: HttpUrl

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.id != f"program:{self.code}":
            raise ValueError("program id must equal program:<code>")
        if not self.code.startswith(self.direction_id.removeprefix("direction:") + "-"):
            raise ValueError("program code must belong to its direction")
        return self


class Discipline(DomainBase):
    id: DisciplineId
    name: NonEmptyText = Field(max_length=256)
    normalized_name: ShortText = Field(max_length=256)

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        expected = sha256(self.normalized_name.encode("utf-8")).hexdigest()[:16]
        if self.id != f"discipline:{expected}":
            raise ValueError("discipline id must derive from normalized_name")
        return self


class SourceAttribution(DomainBase):
    kind: SourceKind
    url: HttpUrl
    captured_at: datetime
    content_sha256: Sha256


class CurriculumItem(DomainBase):
    id: CurriculumItemId
    discipline_id: DisciplineId
    semester: Semester | None = None
    hours: HourCount
    credits: Credits | None = None
    assessment_types: tuple[AssessmentType, ...] | None = None
    subject_group: ShortText | None = None
    source_position: SourcePosition | None = None

    @model_validator(mode="after")
    def validate_assessments(self) -> Self:
        expected_suffix = f":{self.discipline_id}:{self.semester if self.semester is not None else 'unassigned'}"
        if not self.id.startswith("curriculum-item:program:") or not self.id.endswith(expected_suffix):
            raise ValueError("curriculum item id must derive from its discipline and semester")
        if self.assessment_types is not None and not self.assessment_types:
            raise ValueError("assessment_types must be non-empty when present")
        if self.assessment_types is not None and len(set(self.assessment_types)) != len(self.assessment_types):
            raise ValueError("assessment_types must not contain duplicates")
        return self


class Curriculum(DomainBase):
    id: CurriculumId
    program_id: ProgramId
    education_year: EducationYear
    source_url: HttpUrl
    captured_at: datetime
    items: tuple[CurriculumItem, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.id != f"curriculum:{self.program_id.removeprefix('program:')}-{self.education_year}":
            raise ValueError("curriculum id must derive from program and education year")
        identities = [(item.discipline_id, item.semester) for item in self.items]
        if len(identities) != len(set(identities)):
            raise ValueError("curriculum cannot contain duplicate discipline/semester items")
        return self


class NormalizedTracerSnapshot(DomainBase):
    university: University
    direction: Direction
    programs: tuple[EducationalProgram, ...] = Field(min_length=1)
    disciplines: tuple[Discipline, ...] = Field(min_length=1)
    curricula: tuple[Curriculum, ...] = Field(min_length=1)
    sources: tuple[SourceAttribution, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        if self.direction.university_id != self.university.id:
            raise ValueError("direction university foreign key does not resolve")
        programs_by_id = {program.id: program for program in self.programs}
        if len(programs_by_id) != len(self.programs):
            raise ValueError("program ids must be unique")
        disciplines_by_id = {discipline.id: discipline for discipline in self.disciplines}
        if len(disciplines_by_id) != len(self.disciplines):
            raise ValueError("discipline ids must be unique")
        for program in self.programs:
            if program.direction_id != self.direction.id:
                raise ValueError("program direction foreign key does not resolve")
        curriculum_programs = {curriculum.program_id for curriculum in self.curricula}
        if curriculum_programs != set(programs_by_id):
            raise ValueError("every selected program must have exactly one curriculum")
        for curriculum in self.curricula:
            for item in curriculum.items:
                if item.discipline_id not in disciplines_by_id:
                    raise ValueError("curriculum item discipline foreign key does not resolve")
        return self


class CompareWorkload(DomainBase):
    semester: Semester | None = None
    hours: HourCount
    credits: Decimal | None = None
    assessment_types: tuple[AssessmentType, ...] | None = None
    subject_group: ShortText | None = None


CompareStatusValue = CompareStatus
EducationLevelValue = EducationLevel
