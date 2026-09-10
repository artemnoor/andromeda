from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ...contracts.api import (
    CompareResponse,
    CompareRowResponse,
    DisciplineResponse,
    parse_program_ids as parse_program_ids_contract,
    SourceAttributionResponse,
    WorkloadResponse,
)
from ...contracts.enums import AssessmentType, CompareStatus, SourceKind
from ...contracts.constraints import http_url
from ...contracts.errors import ContractError, ErrorCode, ErrorDetail
from ...db.repositories import get_curriculum, get_curriculum_items, get_program, get_source_for_url
from .program_service import program_summary

logger = logging.getLogger("api.compare")


@dataclass(frozen=True, slots=True)
class WorkloadEntry:
    discipline: DisciplineResponse
    workload: WorkloadResponse


def parse_program_ids(value: str) -> tuple[str, str]:
    try:
        parts = parse_program_ids_contract(value)
    except ValueError as exc:
        raise ContractError(
            ErrorCode.VALIDATION_ERROR,
            "programIds must contain exactly two distinct valid program ids",
            [ErrorDetail(path="programIds", message="expected two distinct ProgramId values", type="value_error")],
        ) from exc
    return parts[0], parts[1]


def build_compare_response(session: Session, raw_program_ids: str) -> CompareResponse:
    program_a_id, program_b_id = parse_program_ids(raw_program_ids)
    program_a = get_program(session, program_a_id)
    program_b = get_program(session, program_b_id)
    if program_a is None or program_b is None:
        missing = program_a_id if program_a is None else program_b_id
        raise ContractError(ErrorCode.NOT_FOUND, "Program was not found", [ErrorDetail(path="programIds", message=f"unknown program {missing}", type="not_found")])
    curriculum_a = get_curriculum(session, program_a_id)
    curriculum_b = get_curriculum(session, program_b_id)
    if curriculum_a is None or curriculum_b is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Curriculum was not found", [ErrorDetail(path="programIds", message="both programs must have curriculum", type="not_found")])
    source_a = get_source_for_url(session, curriculum_a.source_url)
    source_b = get_source_for_url(session, curriculum_b.source_url)
    if source_a is None or source_b is None:
        raise ContractError(ErrorCode.CONTRACT_ERROR, "Comparison provenance is incomplete")
    left = _workloads(session, curriculum_a.id)
    right = _workloads(session, curriculum_b.id)
    keys = sorted(set(left) | set(right), key=lambda key: (key[0], key[1] is None, key[1] or 0))
    rows = tuple(_compare_row(key, left.get(key), right.get(key)) for key in keys)
    result = CompareResponse(
        program_a=program_summary(program_a),
        program_b=program_summary(program_b),
        rows=rows,
        sources=(
            SourceAttributionResponse(kind=SourceKind(source_a.source_kind), url=http_url(source_a.requested_url), captured_at=source_a.captured_at, content_sha256=source_a.content_sha256),
            SourceAttributionResponse(kind=SourceKind(source_b.source_kind), url=http_url(source_b.requested_url), captured_at=source_b.captured_at, content_sha256=source_b.content_sha256),
        ),
    )
    status_counts = Counter(row.status.value for row in rows)
    logger.info(
        "compare_complete program_a=%s program_b=%s rows=%d status_counts=%s",
        program_a_id,
        program_b_id,
        len(rows),
        dict(status_counts),
    )
    return result


def _workloads(session: Session, curriculum_id: str) -> dict[tuple[str, int | None], WorkloadEntry]:
    result: dict[tuple[str, int | None], WorkloadEntry] = {}
    for item, discipline, assessment_ids in get_curriculum_items(session, curriculum_id):
        key = (discipline.normalized_name, item.semester)
        if key in result:
            raise ContractError(ErrorCode.CONTRACT_ERROR, "Duplicate comparison identity in database")
        result[key] = WorkloadEntry(
            discipline=DisciplineResponse(
                id=discipline.id,
                name=discipline.name,
                normalized_name=discipline.normalized_name,
            ),
            workload=WorkloadResponse(
                semester=item.semester,
                hours=item.hours,
                credits=item.credits,
                assessment_types=_assessment_types(assessment_ids),
                subject_group=item.subject_group,
            ),
        )
    return result


def _compare_row(key: tuple[str, int | None], left: WorkloadEntry | None, right: WorkloadEntry | None) -> CompareRowResponse:
    _, semester = key
    if left is None:
        status = CompareStatus.ONLY_B
    elif right is None:
        status = CompareStatus.ONLY_A
    elif left.workload == right.workload:
        status = CompareStatus.BOTH
    else:
        status = CompareStatus.DIFFERENT
    entry = left or right
    if entry is None:
        raise ContractError(ErrorCode.CONTRACT_ERROR, "Comparison row has no workload")
    return CompareRowResponse(
        discipline=entry.discipline,
        semester=semester,
        a=left.workload if left else None,
        b=right.workload if right else None,
        status=status,
    )


def _assessment_types(values: tuple[str, ...]) -> tuple[AssessmentType, ...] | None:
    try:
        result = tuple(sorted((AssessmentType(value) for value in values), key=lambda value: value.value))
    except ValueError as exc:
        raise ContractError(
            ErrorCode.CONTRACT_ERROR,
            "Persisted assessment type does not satisfy the contract",
            [ErrorDetail(path="compare.rows.assessmentTypes", message="unknown assessment type", type="enum")],
        ) from exc
    return result or None
