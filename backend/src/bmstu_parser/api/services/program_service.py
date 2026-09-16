from __future__ import annotations

from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from ...contracts.api import (
    CurriculumItemResponse,
    CurriculumMetadataResponse,
    CurriculumResponse,
    DirectionResponse,
    DisciplineResponse,
    ProgramResponse,
    ProgramSummaryResponse,
    SourceAttributionResponse,
    UniversityResponse,
)
from ...contracts.constraints import ProgramId, http_url
from ...contracts.enums import AssessmentType, EducationLevel, SourceKind
from ...contracts.errors import ContractError, ErrorCode, ErrorDetail
from ...db.repositories import (
    get_curriculum,
    get_curriculum_items,
    get_direction,
    get_program,
    get_source_for_url,
    get_university,
)
from ...db.models import (
    DirectionModel,
    EducationalProgramModel,
    SourceSnapshotModel,
    UniversityModel,
)

PROGRAM_ID_ADAPTER = TypeAdapter(ProgramId)


def validate_program_id(value: str) -> str:
    try:
        return PROGRAM_ID_ADAPTER.validate_python(value)
    except ValidationError as exc:
        raise ContractError(
            ErrorCode.VALIDATION_ERROR,
            "Program id validation failed",
            [ErrorDetail(path="id", message="invalid program id", type="value_error")],
        ) from exc


def build_program_response(session: Session, raw_program_id: str) -> ProgramResponse:
    program_id = validate_program_id(raw_program_id)
    program = get_program(session, program_id)
    if program is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Program was not found", [ErrorDetail(path="id", message="unknown program", type="not_found")])
    direction = get_direction(session, program.direction_id)
    university = get_university(session, direction.university_id if direction else "")
    source = get_source_for_url(session, program.source_url)
    if direction is None or university is None or source is None:
        raise ContractError(ErrorCode.CONTRACT_ERROR, "Program provenance graph is incomplete")
    result = ProgramResponse(
        university=university_response(university),
        direction=direction_response(direction),
        program=program_summary(program),
        source=source_response(source),
    )
    return result


def build_curriculum_response(session: Session, raw_program_id: str) -> CurriculumResponse:
    program_id = validate_program_id(raw_program_id)
    program = get_program(session, program_id)
    if program is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Program was not found", [ErrorDetail(path="id", message="unknown program", type="not_found")])
    curriculum = get_curriculum(session, program_id)
    if curriculum is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Curriculum was not found", [ErrorDetail(path="id", message="curriculum not found", type="not_found")])
    source = get_source_for_url(session, curriculum.source_url)
    if source is None:
        raise ContractError(ErrorCode.CONTRACT_ERROR, "Curriculum provenance is incomplete")
    items = tuple(
        CurriculumItemResponse(
            id=item.id,
            discipline=DisciplineResponse(id=discipline.id, name=discipline.name, normalized_name=discipline.normalized_name),
            semester=item.semester,
            hours=item.hours,
            credits=item.credits,
            assessment_types=_assessment_types(assessments),
            source_position=item.source_position,
        )
        for item, discipline, assessments in get_curriculum_items(session, curriculum.id)
    )
    result = CurriculumResponse(
        program=program_summary(program),
        curriculum=CurriculumMetadataResponse(
            id=curriculum.id,
            program_id=curriculum.program_id,
            education_year=curriculum.education_year,
            source_url=http_url(curriculum.source_url),
            captured_at=curriculum.captured_at,
        ),
        items=items,
        source=source_response(source),
    )
    return result


def program_summary(program: EducationalProgramModel) -> ProgramSummaryResponse:
    return ProgramSummaryResponse(
        id=program.id,
        direction_id=program.direction_id,
        code=program.code,
        name=program.name,
        education_year=program.education_year,
        study_plan_url=http_url(program.study_plan_url),
        source_url=http_url(program.source_url),
    )


def university_response(university: UniversityModel) -> UniversityResponse:
    return UniversityResponse(
        id=university.id,
        name=university.name,
        city=university.city,
        official_site=http_url(university.official_site),
        address=university.address,
    )


def direction_response(direction: DirectionModel) -> DirectionResponse:
    try:
        education_level = EducationLevel(direction.education_level)
    except ValueError as exc:
        raise ContractError(
            ErrorCode.CONTRACT_ERROR,
            "Persisted education level does not satisfy the contract",
            [ErrorDetail(path="direction.educationLevel", message="unknown education level", type="enum")],
        ) from exc
    return DirectionResponse(
        id=direction.id,
        university_id=direction.university_id,
        code=direction.code,
        name=direction.name,
        education_level=education_level,
    )


def source_response(source: SourceSnapshotModel) -> SourceAttributionResponse:
    try:
        kind = SourceKind(source.source_kind)
    except ValueError as exc:
        raise ContractError(
            ErrorCode.CONTRACT_ERROR,
            "Persisted source kind does not satisfy the contract",
            [ErrorDetail(path="source.kind", message="unknown source kind", type="enum"),],
        ) from exc
    return SourceAttributionResponse(
        kind=kind,
        url=http_url(source.requested_url),
        captured_at=source.captured_at,
        content_sha256=source.content_sha256,
    )


def _assessment_types(values: tuple[str, ...]) -> tuple[AssessmentType, ...] | None:
    try:
        result = tuple(sorted((AssessmentType(value) for value in values), key=lambda value: value.value))
    except ValueError as exc:
        raise ContractError(
            ErrorCode.CONTRACT_ERROR,
            "Persisted assessment type does not satisfy the contract",
            [ErrorDetail(path="curriculum.items.assessmentTypes", message="unknown assessment type", type="enum")],
        ) from exc
    return result or None
