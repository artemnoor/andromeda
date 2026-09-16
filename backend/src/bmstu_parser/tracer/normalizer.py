from __future__ import annotations

import logging
from datetime import datetime
from hashlib import sha256
import unicodedata
from decimal import Decimal, InvalidOperation

from pydantic import HttpUrl

from ..contracts.domain import (
    Curriculum,
    CurriculumItem,
    Direction,
    Discipline,
    EducationalProgram,
    NormalizedTracerSnapshot,
    SourceAttribution,
    University,
)
from ..contracts.enums import AssessmentType, EducationLevel, SourceKind
from ..contracts.errors import ContractError, ErrorCode, ErrorDetail
from ..contracts.raw import RawTracerBundle
from .identity import direction_codes

logger = logging.getLogger("contracts.validation")

ASSESSMENT_MAPPING: dict[str, tuple[AssessmentType, ...]] = {
    "экз": (AssessmentType.EXAM,),
    "рэкз": (AssessmentType.EXAM,),
    "зчт": (AssessmentType.CREDIT,),
    "дзчт": (AssessmentType.GRADED_CREDIT,),
    "кур": (AssessmentType.COURSEWORK,),
    "куп": (AssessmentType.COURSE_PROJECT,),
    "гэк": (AssessmentType.STATE_EXAM,),
    "экз кур": (AssessmentType.EXAM, AssessmentType.COURSEWORK),
}


def normalize_bundle(raw: RawTracerBundle) -> NormalizedTracerSnapshot:
    university = University(
        id="university:bmstu",
        name=_text(raw.university.name),
        city=_text(raw.university.city),
        official_site=raw.university.official_site,
        address=_text(raw.university.address),
    )
    raw_directions = raw.directions or (raw.direction,)
    directions: list[Direction] = []
    seen_direction_codes: set[str] = set()
    for raw_direction in raw_directions:
        for direction_code in direction_codes(raw_direction.code) or (_code(raw_direction.code),):
            if direction_code in seen_direction_codes:
                continue
            seen_direction_codes.add(direction_code)
            directions.append(
                Direction(
                    id=f"direction:{direction_code}",
                    university_id=university.id,
                    code=direction_code,
                    name=_text(raw_direction.name),
                    education_level=_level(raw_direction.education_level),
                )
            )
    if not directions:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "BMSTU source has no canonical directions")
    direction = directions[0]
    directions_by_code = {item.code: item for item in directions}
    programs = tuple(
        EducationalProgram(
            id=f"program:{_code(program.code)}",
            direction_id=f"direction:{_program_direction(program, directions_by_code, direction.code)}",
            code=_code(program.code),
            name=_text(program.name),
            education_year=program.education_year,
            study_plan_url=program.study_plan_url,
            source_url=program.source_url,
        )
        for program in raw.programs
    )
    programs_by_code = {program.code: program for program in programs}
    if len(programs_by_code) != len(programs):
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Duplicate selected program code")

    items_by_program: dict[str, list[CurriculumItem]] = {program.code: [] for program in programs}
    disciplines: dict[str, Discipline] = {}
    for row in raw.curriculum_rows:
        program_code = _code(row.program_code)
        program = programs_by_code.get(program_code)
        if program is None:
            raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Curriculum row points to unknown program {program_code}")
        normalized_name = _text(row.discipline).casefold()
        normalized_name = " ".join(normalized_name.split())
        normalized_name = unicodedata.normalize("NFKC", normalized_name)
        discipline_id = f"discipline:{sha256(normalized_name.encode('utf-8')).hexdigest()[:16]}"
        discipline = disciplines.setdefault(
            discipline_id,
            Discipline(id=discipline_id, name=_text(row.discipline), normalized_name=normalized_name),
        )
        assessment_types = _assessment(row.assessment)
        semester_key = str(row.semester) if row.semester is not None else "unassigned"
        item_id = f"curriculum-item:{program.id}:{discipline.id}:{semester_key}"
        item = CurriculumItem(
            id=item_id,
            discipline_id=discipline.id,
            source_name=_text(row.discipline),
            semester=row.semester,
            hours=row.hours,
            credits=_credits(row.credits, row.locator.field or "credits"),
            assessment_types=assessment_types,
            source_position=row.source_position,
        )
        _append_curriculum_item(items_by_program[program.code], item)

    curricula = tuple(
        Curriculum(
            id=f"curriculum:{program.code}-{program.education_year}",
            program_id=program.id,
            education_year=program.education_year,
            source_url=program.study_plan_url,
            captured_at=_captured_at(raw, program.code),
            items=tuple(items_by_program[program.code]),
        )
        for program in programs
        if items_by_program[program.code]
    )
    sources = tuple(
        SourceAttribution(
            kind=_source_kind(snapshot.source_kind),
            url=snapshot.requested_url,
            captured_at=snapshot.captured_at,
            content_sha256=snapshot.content_sha256,
        )
        for snapshot in raw.snapshots
    )
    result = NormalizedTracerSnapshot(
        university=university,
        direction=direction,
        programs=programs,
        disciplines=tuple(disciplines.values()),
        curricula=curricula,
        sources=sources,
        directions=tuple(directions),
        source_gaps=tuple(raw.source_gaps),
    )
    logger.debug("boundary_validated boundary=normalized programs=%d disciplines=%d", len(programs), len(disciplines))
    return result


def _text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value.replace("\xa0", " "))
    value = " ".join(value.strip().split())
    if not value:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Required source text is empty")
    return value


def _nullable_text(value: str | None) -> str | None:
    return _text(value) if value and value.strip() else None


def _code(value: str) -> str:
    return _text(value).replace("–", "-").replace("—", "-").replace("/", "-").replace(" ", "")


def _level(value: str) -> EducationLevel:
    mapping = {"бакалавриат": EducationLevel.BACHELOR, "bachelor": EducationLevel.BACHELOR}
    try:
        return mapping[_text(value).casefold()]
    except KeyError as exc:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Unsupported education level: {value}") from exc


def _assessment(value: str | None) -> tuple[AssessmentType, ...] | None:
    if not value or not value.strip():
        return None
    key = " ".join(value.casefold().replace("ё", "е").split())
    try:
        return ASSESSMENT_MAPPING[key]
    except KeyError:
        inferred: list[AssessmentType] = []
        if any(token in key for token in ("экз", "экзам")):
            inferred.append(AssessmentType.EXAM)
        if any(token in key for token in ("зчт", "зач", "зет")):
            inferred.append(AssessmentType.GRADED_CREDIT if "дзч" in key or "диф" in key else AssessmentType.CREDIT)
        if "куп" in key or "проект" in key:
            inferred.append(AssessmentType.COURSE_PROJECT)
        elif "кур" in key:
            inferred.append(AssessmentType.COURSEWORK)
        if any(token in key for token in ("гэк", "гос экзам", "государственн")):
            inferred.append(AssessmentType.STATE_EXAM)
        if inferred:
            return tuple(dict.fromkeys(inferred))
        logger.warning("unsupported_bmstu_assessment_mark value=%s", value)
        return None


def _credits(value: str | float | int | None, path: str) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        parsed = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Credits value is not numeric", [ErrorDetail(path=path, message="numeric value expected", type="source_value")]) from exc
    return parsed


def _source_kind(value: str) -> SourceKind:
    aliases = {"bmstu_major_catalog": SourceKind.BMSTU_MAJOR_CATALOG}
    try:
        return aliases.get(value, SourceKind(value))
    except ValueError as exc:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Unknown source kind: {value}") from exc


def _captured_at(raw: RawTracerBundle, program_code: str) -> datetime:
    program = next((item for item in raw.programs if item.code == program_code), None)
    matching = [
        snapshot.captured_at
        for snapshot in raw.snapshots
        if snapshot.source_kind == "bmstu_curriculum_document"
        and program is not None
        and str(snapshot.requested_url) == str(program.study_plan_url)
    ]
    return matching[0] if matching else raw.snapshots[0].captured_at


def _program_direction(program: object, directions: dict[str, Direction], fallback: str) -> str:
    value = getattr(program, "direction_code", "")
    candidates = direction_codes(value) if isinstance(value, str) else ()
    for candidate in candidates:
        if candidate in directions:
            return candidate
    code = getattr(program, "code", "")
    candidates = direction_codes(code) if isinstance(code, str) else ()
    return next((candidate for candidate in candidates if candidate in directions), fallback)


def _append_curriculum_item(items: list[CurriculumItem], item: CurriculumItem) -> None:
    """Collapse repeated PDF rows without losing workload/control facts."""
    for index, existing in enumerate(items):
        if (existing.discipline_id, existing.semester) != (item.discipline_id, item.semester):
            continue
        existing_assessments = existing.assessment_types or ()
        item_assessments = item.assessment_types or ()
        assessment_types = tuple(dict.fromkeys((*existing_assessments, *item_assessments))) or None
        items[index] = existing.model_copy(
            update={
                "hours": max(existing.hours, item.hours),
                "credits": existing.credits if existing.credits is not None else item.credits,
                "assessment_types": assessment_types,
                "source_position": min(
                    value for value in (existing.source_position, item.source_position) if value is not None
                ) if existing.source_position is not None or item.source_position is not None else None,
            }
        )
        logger.warning(
            "duplicate_curriculum_row_collapsed program_item=%s semester=%s",
            existing.discipline_id,
            existing.semester,
        )
        return
    items.append(item)
