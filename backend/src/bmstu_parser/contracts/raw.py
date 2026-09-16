from __future__ import annotations

from datetime import datetime
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class RawBase(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class RawSourceSnapshot(RawBase):
    source_kind: str = Field(min_length=1, max_length=128)
    requested_url: HttpUrl
    final_url: HttpUrl
    status_code: int = Field(ge=200, le=599)
    content_type: str | None = Field(default=None, max_length=256)
    captured_at: datetime
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    body: bytes = Field(min_length=1)


class SourceLocator(RawBase):
    source_url: HttpUrl
    page: int | None = Field(default=None, ge=1)
    row: int | None = Field(default=None, ge=1)
    field: str | None = Field(default=None, min_length=1, max_length=128)


class RawUniversityRecord(RawBase):
    name: str
    city: str
    address: str
    official_site: HttpUrl
    locator: SourceLocator


class RawDirectionRecord(RawBase):
    code: str
    name: str
    education_level: str
    locator: SourceLocator


class RawSourceGap(RawBase):
    id: str
    entity_type: str
    entity_key: str
    reason: str
    source_url: HttpUrl
    locator: SourceLocator


class RawProgramRecord(RawBase):
    code: str
    name: str
    direction_code: str
    education_level: str
    education_year: int
    study_plan_url: HttpUrl
    source_url: HttpUrl
    locator: SourceLocator
    source_code: str | None = None


class RawCurriculumRow(RawBase):
    program_code: str
    discipline: str
    semester: int | None = Field(default=None, ge=1, le=12)
    hours: int
    credits: str | float | int | None
    assessment: str | None
    source_position: int | None = Field(default=None, ge=1)
    source_url: HttpUrl
    locator: SourceLocator
    source_program_code: str | None = None


class RawTracerBundle(RawBase):
    snapshots: tuple[RawSourceSnapshot, ...] = Field(min_length=1)
    university: RawUniversityRecord
    direction: RawDirectionRecord
    programs: tuple[RawProgramRecord, ...] = Field(min_length=1)
    curriculum_rows: tuple[RawCurriculumRow, ...] = ()
    directions: tuple[RawDirectionRecord, ...] = ()
    source_gaps: tuple[RawSourceGap, ...] = ()
