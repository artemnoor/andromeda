"""Typed catalog response contracts exposed to the Spike frontend."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from proftest_spike.catalog.service import CatalogSnapshot
from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode, DistinctiveSubject

from .common import ApiModel


class CatalogProgramResponse(ApiModel):
    program_id: str = Field(min_length=1, max_length=128)
    program_code: str = Field(min_length=1, max_length=128)
    program_name: str = Field(min_length=1, max_length=512)
    basis: Literal["hours", "credits"]
    total_hours: int = Field(strict=True, ge=0)
    total_credits: Decimal = Field(strict=True, ge=0)
    total_workload: Decimal = Field(strict=True, ge=0)
    area_share: dict[AreaCode, Decimal]
    subject_group_share: dict[str, Decimal]
    semester_distribution: dict[str, Decimal]
    activity_signals: dict[ActivityCode, Decimal]
    distinctive_subjects: tuple["DistinctiveSubjectResponse", ...]


class DistinctiveSubjectResponse(ApiModel):
    source_name: str = Field(min_length=1, max_length=256)
    normalized_name: str = Field(min_length=1, max_length=256)
    primary_area: AreaCode
    workload: Decimal = Field(strict=True, ge=0)
    share: Decimal = Field(strict=True, ge=0, le=1)
    rarity: Decimal = Field(strict=True, ge=0, le=1)
    distinctiveness: Decimal = Field(strict=True, ge=0, le=1)


class CatalogResponse(ApiModel):
    status: Literal["ready", "partial", "empty"]
    data_source: Literal["andromeda_http_api"]
    program_count: int = Field(strict=True, ge=0)
    requested_program_count: int = Field(strict=True, ge=0)
    failed_program_count: int = Field(strict=True, ge=0)
    curriculum_item_count: int = Field(strict=True, ge=0)
    programs: tuple[CatalogProgramResponse, ...]
    note: str = Field(min_length=1, max_length=512)


def distinctive_response(subject: DistinctiveSubject) -> DistinctiveSubjectResponse:
    return DistinctiveSubjectResponse.model_validate(subject.model_dump())


def catalog_response(snapshot: CatalogSnapshot) -> CatalogResponse:
    """Map internal fingerprints to the only catalog payload frontend needs."""

    programs = tuple(
        CatalogProgramResponse.model_validate(
            {
                "program_id": fingerprint.program_id,
                "program_code": fingerprint.program_code,
                "program_name": fingerprint.program_name,
                "basis": fingerprint.basis,
                "total_hours": fingerprint.total_hours,
                "total_credits": fingerprint.total_credits,
                "total_workload": fingerprint.total_workload,
                "area_share": fingerprint.area_share,
                "subject_group_share": fingerprint.subject_group_share,
                "semester_distribution": fingerprint.semester_distribution,
                "activity_signals": fingerprint.activity_signals,
                "distinctive_subjects": tuple(distinctive_response(subject) for subject in fingerprint.distinctive_subjects),
            }
        )
        for fingerprint in snapshot.fingerprints
    )
    note = (
        "Каталог загружен из Andromeda API."
        if snapshot.status == "ready"
        else "Каталог загружен частично; некоторые программы недоступны."
        if snapshot.status == "partial"
        else "В Andromeda API пока нет доступных учебных планов."
    )
    return CatalogResponse(
        status=snapshot.status,
        data_source="andromeda_http_api",
        program_count=len(programs),
        requested_program_count=snapshot.requested_program_count,
        failed_program_count=snapshot.failed_program_count,
        curriculum_item_count=snapshot.curriculum_item_count,
        programs=programs,
        note=note,
    )


__all__ = ["CatalogProgramResponse", "CatalogResponse", "DistinctiveSubjectResponse", "catalog_response", "distinctive_response"]
