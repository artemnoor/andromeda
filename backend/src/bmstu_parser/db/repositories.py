from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..contracts.domain import CurriculumItem, NormalizedTracerSnapshot
from ..contracts.enums import AssessmentType, EducationLevel
from ..contracts.errors import ContractError, ErrorCode
from ..contracts.raw import RawTracerBundle
from .models import (
    AssessmentTypeModel,
    CurriculumItemAssessmentModel,
    CurriculumItemModel,
    CurriculumModel,
    DirectionModel,
    DisciplineModel,
    EducationalProgramModel,
    EducationLevelModel,
    IngestRunModel,
    RawSourceRecordModel,
    SourceSnapshotModel,
    UniversityModel,
)

logger = logging.getLogger("tracer.ingest")


def seed_reference_tables(session: Session) -> None:
    for level_value in EducationLevel:
        if session.get(EducationLevelModel, level_value.value) is None:
            session.add(EducationLevelModel(id=level_value.value))
    for assessment_value in AssessmentType:
        if session.get(AssessmentTypeModel, assessment_value.value) is None:
            session.add(AssessmentTypeModel(id=assessment_value.value))


def get_program(session: Session, program_id: str) -> EducationalProgramModel | None:
    return session.get(EducationalProgramModel, program_id)


def get_direction(session: Session, direction_id: str) -> DirectionModel | None:
    return session.get(DirectionModel, direction_id)


def get_university(session: Session, university_id: str) -> UniversityModel | None:
    return session.get(UniversityModel, university_id)


def get_curriculum(session: Session, program_id: str) -> CurriculumModel | None:
    return session.execute(
        select(CurriculumModel).where(CurriculumModel.program_id == program_id).order_by(CurriculumModel.education_year.desc())
    ).scalars().first()


def get_source_for_url(session: Session, url: str) -> SourceSnapshotModel | None:
    return session.execute(
        select(SourceSnapshotModel).where(SourceSnapshotModel.requested_url == url).order_by(SourceSnapshotModel.captured_at.desc())
    ).scalars().first()


def get_curriculum_items(session: Session, curriculum_id: str) -> list[tuple[CurriculumItemModel, DisciplineModel, tuple[str, ...]]]:
    rows = session.execute(
        select(CurriculumItemModel, DisciplineModel)
        .join(DisciplineModel, DisciplineModel.id == CurriculumItemModel.discipline_id)
        .where(CurriculumItemModel.curriculum_id == curriculum_id)
        .order_by(CurriculumItemModel.semester.is_(None), CurriculumItemModel.semester, CurriculumItemModel.source_position, DisciplineModel.normalized_name)
    ).all()
    result: list[tuple[CurriculumItemModel, DisciplineModel, tuple[str, ...]]] = []
    for item, discipline in rows:
        assessments = tuple(
            row.assessment_type_id
            for row in session.execute(
                select(CurriculumItemAssessmentModel).where(CurriculumItemAssessmentModel.curriculum_item_id == item.id)
            ).scalars()
        )
        result.append((item, discipline, assessments))
    return result


def ingest_snapshot(session: Session, raw: RawTracerBundle, normalized: NormalizedTracerSnapshot) -> str:
    run_id = f"ingest:{uuid4().hex}"
    started_at = datetime.now(timezone.utc)
    logger.info("ingest_transaction_start run_id=%s", run_id)
    session.add(IngestRunModel(id=run_id, started_at=started_at, status="running"))
    seed_reference_tables(session)
    session.flush()
    for snapshot in raw.snapshots:
        _insert_snapshot(session, run_id, snapshot)
    session.flush()
    _insert_raw_records(session, raw)
    _insert_domain(session, normalized)
    session.flush()
    run = session.get(IngestRunModel, run_id)
    if run is None:
        raise ContractError(ErrorCode.CONTRACT_ERROR, "Ingest run disappeared before commit")
    run.status = "completed"
    run.finished_at = datetime.now(timezone.utc)
    logger.info(
        "ingest_transaction_commit run_id=%s programs=%d curriculum_items=%d",
        run_id,
        len(normalized.programs),
        sum(len(curriculum.items) for curriculum in normalized.curricula),
    )
    return run_id


def _insert_snapshot(session: Session, run_id: str, snapshot: object) -> None:
    from ..contracts.raw import RawSourceSnapshot

    typed = snapshot if isinstance(snapshot, RawSourceSnapshot) else None
    if typed is None:
        raise ContractError(ErrorCode.CONTRACT_ERROR, "Expected validated raw source snapshot")
    existing = session.get(SourceSnapshotModel, typed.content_sha256)
    if existing is not None:
        if existing.body != typed.body:
            raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Source hash collision with different body")
        return
    session.add(
        SourceSnapshotModel(
            content_sha256=typed.content_sha256,
            ingest_run_id=run_id,
            source_kind=typed.source_kind,
            requested_url=str(typed.requested_url),
            final_url=str(typed.final_url),
            status_code=typed.status_code,
            content_type=typed.content_type,
            captured_at=typed.captured_at,
            body=typed.body,
        )
    )


def _insert_raw_records(session: Session, raw: RawTracerBundle) -> None:
    hashes_by_url = {str(snapshot.requested_url): snapshot.content_sha256 for snapshot in raw.snapshots}
    records: list[tuple[str, str, str]] = [
        ("University", raw.university.model_dump_json(), str(raw.university.locator.source_url)),
        ("Direction", raw.direction.model_dump_json(), str(raw.direction.locator.source_url)),
    ]
    records.extend(("Program", program.model_dump_json(), str(program.source_url)) for program in raw.programs)
    records.extend(("CurriculumRow", row.model_dump_json(), str(row.source_url)) for row in raw.curriculum_rows)
    for index, (record_type, payload, source_url) in enumerate(records):
        snapshot_hash = hashes_by_url.get(source_url)
        if snapshot_hash is None:
            raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Raw record source is not captured: {source_url}")
        record_id = f"{snapshot_hash}:{record_type}:{index}"
        if session.get(RawSourceRecordModel, record_id) is None:
            session.add(RawSourceRecordModel(id=record_id, snapshot_sha256=snapshot_hash, record_type=record_type, payload_json=payload))


def _insert_domain(session: Session, normalized: NormalizedTracerSnapshot) -> None:
    _insert_or_validate(session, UniversityModel, normalized.university.id, {
        "id": normalized.university.id,
        "name": normalized.university.name,
        "city": normalized.university.city,
        "official_site": str(normalized.university.official_site),
        "address": normalized.university.address,
    })
    session.flush()
    _insert_or_validate(session, DirectionModel, normalized.direction.id, {
        "id": normalized.direction.id,
        "university_id": normalized.direction.university_id,
        "code": normalized.direction.code,
        "name": normalized.direction.name,
        "education_level": normalized.direction.education_level.value,
    })
    session.flush()
    for program in normalized.programs:
        _insert_or_validate(session, EducationalProgramModel, program.id, {
            "id": program.id,
            "direction_id": program.direction_id,
            "code": program.code,
            "name": program.name,
            "education_year": program.education_year,
            "study_plan_url": str(program.study_plan_url),
            "source_url": str(program.source_url),
        })
    session.flush()
    disciplines_by_id = {discipline.id: discipline for discipline in normalized.disciplines}
    for discipline in normalized.disciplines:
        _insert_or_validate(session, DisciplineModel, discipline.id, {
            "id": discipline.id,
            "name": discipline.name,
            "normalized_name": discipline.normalized_name,
        })
    session.flush()
    pending_assessments: list[dict[str, str]] = []
    for curriculum in normalized.curricula:
        _insert_or_validate(session, CurriculumModel, curriculum.id, {
            "id": curriculum.id,
            "program_id": curriculum.program_id,
            "education_year": curriculum.education_year,
            "source_url": str(curriculum.source_url),
            "captured_at": curriculum.captured_at,
        })
    session.flush()
    for curriculum in normalized.curricula:
        for item in curriculum.items:
            if item.discipline_id not in disciplines_by_id:
                raise ContractError(ErrorCode.CONTRACT_ERROR, f"Discipline {item.discipline_id} is missing")
            _insert_or_validate(session, CurriculumItemModel, item.id, {
                "id": item.id,
                "curriculum_id": curriculum.id,
                "discipline_id": item.discipline_id,
                "source_name": item.source_name,
                "semester": item.semester,
                "semester_identity": _semester_identity(item.semester),
                "hours": item.hours,
                "credits": item.credits,
                "source_position": item.source_position,
            })
            for assessment in item.assessment_types or ():
                pending_assessments.append({"curriculum_item_id": item.id, "assessment_type_id": assessment.value})

    # The association mapper intentionally stays small and has no ORM
    # relationships, so make the FK dependency explicit before inserting it.
    session.flush()
    for association_id in pending_assessments:
        exists = session.execute(select(CurriculumItemAssessmentModel).filter_by(**association_id)).scalar_one_or_none()
        if exists is None:
            session.add(CurriculumItemAssessmentModel(**association_id))


def _insert_or_validate(session: Session, model: type[object], identity: str, values: dict[str, object]) -> None:
    existing = session.get(model, identity)
    if existing is None:
        session.add(model(**values))
        return
    for field, expected in values.items():
        actual = getattr(existing, field)
        if not _same_value(actual, expected):
            raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Identity conflict for {identity}: {field}")


def _same_value(actual: object, expected: object) -> bool:
    if isinstance(actual, datetime) and isinstance(expected, datetime):
        actual_utc = actual.replace(tzinfo=timezone.utc) if actual.tzinfo is None else actual.astimezone(timezone.utc)
        expected_utc = expected.replace(tzinfo=timezone.utc) if expected.tzinfo is None else expected.astimezone(timezone.utc)
        return actual_utc == expected_utc
    return actual == expected or str(actual) == str(expected)


def _semester_identity(semester: int | None) -> str:
    return "unassigned" if semester is None else f"semester:{semester}"
