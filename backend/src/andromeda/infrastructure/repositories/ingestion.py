from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from andromeda.ingestion.contracts.normalized import CanonicalSnapshot
from andromeda.ingestion.contracts.raw import RawSourceSnapshot, RawTracerBundle
from andromeda.shared.contracts.enums import AssessmentType, EducationLevel
from andromeda.shared.contracts.errors import ContractError, ErrorCode

from ..database.base import Base
from ..database.models import (
    AssessmentTypeModel,
    CurriculumItemAssessmentModel,
    CurriculumItemModel,
    CurriculumModel,
    DirectionModel,
    DisciplineModel,
    EducationLevelModel,
    IngestRunModel,
    ProgramModel,
    RawSourceRecordModel,
    SourceSnapshotModel,
    UniversityModel,
)
from ..database.session import session_factory


logger = logging.getLogger("andromeda.infrastructure.repositories.ingestion")


class SqlAlchemyIngestionRepository:
    """Atomic write adapter from canonical DTOs to infrastructure models."""

    def __init__(self, engine: Any) -> None:
        self._factory = session_factory(engine)

    def ingest(self, raw: RawTracerBundle, canonical: CanonicalSnapshot) -> str:
        run_id = f"ingest:{uuid4().hex}"
        started_at = datetime.now(timezone.utc)
        logger.info("ingest_transaction_start run_id=%s", run_id)
        with self._factory() as session:
            try:
                with session.begin():
                    session.add(IngestRunModel(id=run_id, started_at=started_at, status="running"))
                    self._seed_reference_tables(session)
                    session.flush()
                    for snapshot in raw.snapshots:
                        self._insert_snapshot(session, run_id, snapshot)
                    session.flush()
                    self._insert_raw_records(session, raw)
                    self._insert_domain(session, canonical)
                    run = session.get(IngestRunModel, run_id)
                    if run is None:
                        raise ContractError(ErrorCode.CONTRACT_ERROR, "Ingest run disappeared before commit")
                    run.status = "completed"
                    run.finished_at = datetime.now(timezone.utc)
            except Exception:
                logger.exception("ingest_transaction_rollback run_id=%s", run_id)
                raise
        logger.info(
            "ingest_transaction_commit run_id=%s programs=%d curriculum_items=%d",
            run_id,
            len(canonical.programs),
            sum(len(curriculum.items) for curriculum in canonical.curricula),
        )
        return run_id

    @staticmethod
    def _seed_reference_tables(session: Session) -> None:
        for level_value in EducationLevel:
            if session.get(EducationLevelModel, level_value.value) is None:
                session.add(EducationLevelModel(id=level_value.value))
        for assessment_value in AssessmentType:
            if session.get(AssessmentTypeModel, assessment_value.value) is None:
                session.add(AssessmentTypeModel(id=assessment_value.value))

    @staticmethod
    def _insert_snapshot(session: Session, run_id: str, snapshot: RawSourceSnapshot) -> None:
        existing = session.get(SourceSnapshotModel, snapshot.content_sha256)
        if existing is not None:
            if existing.body != snapshot.body:
                raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Source hash collision with different body")
            return
        session.add(
            SourceSnapshotModel(
                content_sha256=snapshot.content_sha256,
                ingest_run_id=run_id,
                source_kind=snapshot.source_kind,
                requested_url=str(snapshot.requested_url),
                final_url=str(snapshot.final_url),
                status_code=snapshot.status_code,
                content_type=snapshot.content_type,
                captured_at=snapshot.captured_at,
                body=snapshot.body,
            )
        )

    @staticmethod
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
                raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Raw record source is not captured")
            record_id = f"{snapshot_hash}:{record_type}:{index}"
            if session.get(RawSourceRecordModel, record_id) is None:
                session.add(RawSourceRecordModel(id=record_id, snapshot_sha256=snapshot_hash, record_type=record_type, payload_json=payload))

    @classmethod
    def _insert_domain(cls, session: Session, canonical: CanonicalSnapshot) -> None:
        cls._insert_or_validate(
            session,
            UniversityModel,
            canonical.university.id,
            {
                "id": canonical.university.id,
                "name": canonical.university.name,
                "city": canonical.university.city,
                "official_site": str(canonical.university.official_site),
                "address": canonical.university.address,
            },
        )
        session.flush()
        cls._insert_or_validate(
            session,
            DirectionModel,
            canonical.direction.id,
            {
                "id": canonical.direction.id,
                "university_id": canonical.direction.university_id,
                "code": canonical.direction.code,
                "name": canonical.direction.name,
                "education_level": canonical.direction.education_level.value,
            },
        )
        session.flush()
        for program in canonical.programs:
            cls._insert_or_validate(
                session,
                ProgramModel,
                program.id,
                {
                    "id": program.id,
                    "direction_id": program.direction_id,
                    "code": program.code,
                    "name": program.name,
                    "education_year": program.education_year,
                    "study_plan_url": str(program.study_plan_url),
                    "source_url": str(program.source_url),
                },
            )
        session.flush()
        disciplines_by_id = {discipline.id: discipline for discipline in canonical.disciplines}
        for discipline in canonical.disciplines:
            cls._insert_or_validate(
                session,
                DisciplineModel,
                discipline.id,
                {"id": discipline.id, "name": discipline.name, "normalized_name": discipline.normalized_name},
            )
        session.flush()
        for curriculum in canonical.curricula:
            cls._insert_or_validate(
                session,
                CurriculumModel,
                curriculum.id,
                {
                    "id": curriculum.id,
                    "program_id": curriculum.program_id,
                    "education_year": curriculum.education_year,
                    "source_url": str(curriculum.source_url),
                    "captured_at": curriculum.captured_at,
                },
            )
        session.flush()
        pending_assessments: list[dict[str, str]] = []
        for curriculum in canonical.curricula:
            for item in curriculum.items:
                if item.discipline_id not in disciplines_by_id:
                    raise ContractError(ErrorCode.CONTRACT_ERROR, "Curriculum item discipline is missing")
                cls._insert_or_validate(
                    session,
                    CurriculumItemModel,
                    item.id,
                    {
                        "id": item.id,
                        "curriculum_id": curriculum.id,
                        "discipline_id": item.discipline_id,
                        "source_name": item.source_name,
                        "semester": item.semester,
                        "semester_identity": _semester_identity(item.semester),
                        "hours": item.hours,
                        "credits": item.credits,
                        "subject_group": item.subject_group,
                        "source_position": item.source_position,
                    },
                )
                pending_assessments.extend(
                    {"curriculum_item_id": item.id, "assessment_type_id": assessment.value}
                    for assessment in item.assessment_types or ()
                )
        session.flush()
        for association_id in pending_assessments:
            exists = session.execute(select(CurriculumItemAssessmentModel).filter_by(**association_id)).scalar_one_or_none()
            if exists is None:
                session.add(CurriculumItemAssessmentModel(**association_id))

    @staticmethod
    def _insert_or_validate(session: Session, model: type[Any], identity: str, values: dict[str, object]) -> None:
        existing = session.get(model, identity)
        if existing is None:
            session.add(model(**values))
            return
        for field, expected in values.items():
            if field == "id":
                continue
            actual = getattr(existing, field)
            if not _values_equal(actual, expected):
                raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Identity conflict for {identity}: {field}")


def _semester_identity(semester: int | None) -> str:
    return "unassigned" if semester is None else f"semester:{semester}"


def _values_equal(actual: object, expected: object) -> bool:
    """Compare persisted values without treating SQLite's timezone loss as drift."""
    if expected == "unassigned" and isinstance(actual, str) and actual.startswith("legacy:"):
        # 0002 preserves pre-existing nullable-semester duplicates with a stable
        # legacy identity. The canonical snapshot has one unassigned item, so
        # the primary key remains the authoritative identity on re-ingest.
        return True
    if isinstance(actual, datetime) and isinstance(expected, datetime):
        actual_utc = actual.replace(tzinfo=timezone.utc) if actual.tzinfo is None else actual.astimezone(timezone.utc)
        expected_utc = expected.replace(tzinfo=timezone.utc) if expected.tzinfo is None else expected.astimezone(timezone.utc)
        return actual_utc == expected_utc
    return actual == expected or str(actual) == str(expected)
