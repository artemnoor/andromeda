from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from andromeda.ingestion.contracts.normalized import CanonicalSnapshot
from andromeda.ingestion.contracts.raw import RawSourceSnapshot, RawTracerBundle
from andromeda.ingestion.contracts.source import CapturedSources
from andromeda.modules.disciplines.contracts.public import DisciplineAreaWeight, area_catalog
from andromeda.shared.contracts.enums import AssessmentType, EducationLevel
from andromeda.shared.contracts.errors import AndromedaError, ContractError, ErrorCode

from ..database.models import (
    AssessmentTypeModel,
    CurriculumItemAssessmentModel,
    CurriculumItemModel,
    CurriculumModel,
    DisciplineAreaModel,
    DisciplineAreaWeightModel,
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
from .admissions import SqlAlchemyAdmissionRepository
from .events import SqlAlchemyEventRepository
from .campus import SqlAlchemyCampusPointRepository


logger = logging.getLogger("andromeda.infrastructure.repositories.ingestion")


@dataclass(slots=True)
class _SyncStats:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0

    def record(self, outcome: str) -> None:
        if outcome == "inserted":
            self.inserted += 1
        elif outcome == "updated":
            self.updated += 1
        else:
            self.unchanged += 1


class SqlAlchemyIngestionRepository:
    """Atomic write adapter from canonical DTOs to infrastructure models."""

    def __init__(self, engine: Any) -> None:
        self._factory = session_factory(engine)

    def start_run(self, run_id: str | None = None) -> str:
        resolved_run_id = run_id or f"ingest:{uuid4().hex}"
        self._create_run(
            resolved_run_id,
            datetime.now(timezone.utc),
            source_count=0,
            source_hashes=(),
            source_kinds=(),
            program_count=0,
            curriculum_item_count=0,
            event_count=0,
            campus_point_count=0,
        )
        logger.info("ingest_audit_started run_id=%s", resolved_run_id)
        return resolved_run_id

    def record_source_metadata(self, run_id: str, raw: RawTracerBundle) -> None:
        self.record_captured_metadata(run_id, raw.snapshots)
        self._update_run_metadata(
            run_id,
            source_count=len(raw.snapshots),
            source_hashes=tuple(snapshot.content_sha256 for snapshot in raw.snapshots),
            source_kinds=tuple(snapshot.source_kind for snapshot in raw.snapshots),
            program_count=len(raw.programs),
            curriculum_item_count=len(raw.curriculum_rows),
            event_count=len(raw.events),
            campus_point_count=len(raw.campus_points),
        )

    def record_captured_metadata(self, run_id: str, captured: CapturedSources | tuple[RawSourceSnapshot, ...]) -> None:
        snapshots = captured.snapshots if isinstance(captured, CapturedSources) else captured
        self._update_run_metadata(
            run_id,
            source_count=len(snapshots),
            source_hashes=tuple(snapshot.content_sha256 for snapshot in snapshots),
            source_kinds=tuple(snapshot.source_kind for snapshot in snapshots),
        )

    def ingest(self, raw: RawTracerBundle, canonical: CanonicalSnapshot, *, run_id: str | None = None) -> str:
        resolved_run_id = run_id or self.start_run()
        source_hashes = tuple(snapshot.content_sha256 for snapshot in raw.snapshots)
        source_kinds = tuple(snapshot.source_kind for snapshot in raw.snapshots)
        self._update_run_metadata(
            resolved_run_id,
            source_count=len(source_hashes),
            source_hashes=source_hashes,
            source_kinds=source_kinds,
            program_count=len(canonical.programs),
            curriculum_item_count=sum(len(curriculum.items) for curriculum in canonical.curricula),
            event_count=len(canonical.events),
            campus_point_count=len(canonical.campus_points),
        )
        logger.info("ingest_transaction_start run_id=%s", resolved_run_id)
        stats = _SyncStats()
        with self._factory() as session:
            try:
                with session.begin():
                    self._seed_reference_tables(session)
                    session.flush()
                    for snapshot in raw.snapshots:
                        self._insert_snapshot(session, resolved_run_id, snapshot)
                    session.flush()
                    self._insert_raw_records(session, raw)
                    stats = self._insert_domain(
                        session,
                        canonical,
                        event_source_present=any(snapshot.source_kind == "bmstu_events" for snapshot in raw.snapshots),
                        campus_source_present=any(snapshot.source_kind == "bmstu_campus_points" for snapshot in raw.snapshots),
                    )
            except Exception as exc:
                logger.warning("ingest_transaction_rollback run_id=%s error_code=%s", resolved_run_id, _safe_error_code(exc))
                self._mark_failed(resolved_run_id, exc)
                raise
        try:
            self._mark_completed(resolved_run_id, stats)
        except Exception:
            logger.exception("ingest_audit_complete_failed run_id=%s", resolved_run_id)
            raise
        logger.info(
            "ingest_transaction_commit run_id=%s programs=%d curriculum_items=%d inserted=%d updated=%d unchanged=%d removed=%d",
            resolved_run_id,
            len(canonical.programs),
            sum(len(curriculum.items) for curriculum in canonical.curricula),
            stats.inserted,
            stats.updated,
            stats.unchanged,
            stats.removed,
        )
        return resolved_run_id

    def _update_run_metadata(
        self,
        run_id: str,
        *,
        source_count: int,
        source_hashes: tuple[str, ...],
        source_kinds: tuple[str, ...],
        program_count: int | None = None,
        curriculum_item_count: int | None = None,
        event_count: int | None = None,
        campus_point_count: int | None = None,
    ) -> None:
        with self._factory() as session:
            with session.begin():
                run = session.get(IngestRunModel, run_id)
                if run is None or run.status != "running":
                    raise ContractError(ErrorCode.CONTRACT_ERROR, "Ingest audit row is not running")
                run.source_count = source_count
                run.source_hashes_json = json.dumps(source_hashes, separators=(",", ":"))
                run.source_kinds_json = json.dumps(source_kinds, separators=(",", ":"))
                if program_count is not None:
                    run.program_count = program_count
                if curriculum_item_count is not None:
                    run.curriculum_item_count = curriculum_item_count
                if event_count is not None:
                    run.event_count = event_count
                if campus_point_count is not None:
                    run.campus_point_count = campus_point_count

    def _create_run(
        self,
        run_id: str,
        started_at: datetime,
        *,
        source_count: int,
        source_hashes: tuple[str, ...],
        source_kinds: tuple[str, ...],
        program_count: int,
        curriculum_item_count: int,
        event_count: int,
        campus_point_count: int,
    ) -> None:
        with self._factory() as session:
            with session.begin():
                session.add(
                    IngestRunModel(
                        id=run_id,
                        started_at=started_at,
                        status="running",
                        source_count=source_count,
                        source_hashes_json=json.dumps(source_hashes, separators=(",", ":")),
                        source_kinds_json=json.dumps(source_kinds, separators=(",", ":")),
                        program_count=program_count,
                        curriculum_item_count=curriculum_item_count,
                        event_count=event_count,
                        campus_point_count=campus_point_count,
                    )
                )

    def _mark_completed(self, run_id: str, stats: _SyncStats) -> None:
        with self._factory() as session:
            with session.begin():
                run = session.get(IngestRunModel, run_id)
                if run is None:
                    raise ContractError(ErrorCode.CONTRACT_ERROR, "Ingest audit row disappeared")
                run.status = "completed"
                run.finished_at = datetime.now(timezone.utc)
                run.inserted_count = stats.inserted
                run.updated_count = stats.updated
                run.unchanged_count = stats.unchanged
                run.removed_count = stats.removed

    def _mark_failed(self, run_id: str, error: Exception) -> None:
        error_code = _safe_error_code(error)
        error_message = _safe_error_message(error)
        try:
            with self._factory() as session:
                with session.begin():
                    run = session.get(IngestRunModel, run_id)
                    if run is None:
                        logger.error("ingest_audit_failure_missing run_id=%s error_code=%s", run_id, error_code)
                        return
                    run.status = "failed"
                    run.finished_at = datetime.now(timezone.utc)
                    run.error_code = error_code
                    run.error_message = error_message
        except Exception:
            logger.exception("ingest_audit_failure_update_failed run_id=%s error_code=%s", run_id, error_code)

    def mark_failed(self, run_id: str, error: Exception) -> None:
        self._mark_failed(run_id, error)

    @staticmethod
    def _seed_reference_tables(session: Session) -> None:
        for level_value in EducationLevel:
            if session.get(EducationLevelModel, level_value.value) is None:
                session.add(EducationLevelModel(id=level_value.value))
        for assessment_value in AssessmentType:
            if session.get(AssessmentTypeModel, assessment_value.value) is None:
                session.add(AssessmentTypeModel(id=assessment_value.value))
        for definition in area_catalog():
            existing = session.get(DisciplineAreaModel, definition.code.value)
            if existing is None:
                session.add(
                    DisciplineAreaModel(
                        id=definition.code.value,
                        name=definition.name,
                        description=definition.description,
                        position=definition.position,
                    )
                )
            elif (
                existing.name != definition.name
                or existing.description != definition.description
                or existing.position != definition.position
            ):
                raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Identity conflict for discipline area {definition.code.value}")

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
        records.extend(("Admission", admission.model_dump_json(), str(admission.source_url)) for admission in raw.admissions)
        records.extend(("Event", event.model_dump_json(), str(event.source_url)) for event in raw.events)
        records.extend(("CampusPoint", point.model_dump_json(), str(point.source_url)) for point in raw.campus_points)
        for index, (record_type, payload, source_url) in enumerate(records):
            snapshot_hash = hashes_by_url.get(source_url)
            if snapshot_hash is None:
                raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Raw record source is not captured")
            record_id = f"{snapshot_hash}:{record_type}:{index}"
            if session.get(RawSourceRecordModel, record_id) is None:
                session.add(RawSourceRecordModel(id=record_id, snapshot_sha256=snapshot_hash, record_type=record_type, payload_json=payload))

    @classmethod
    def _insert_domain(
        cls,
        session: Session,
        canonical: CanonicalSnapshot,
        *,
        event_source_present: bool = False,
        campus_source_present: bool = False,
    ) -> _SyncStats:
        stats = _SyncStats()
        stats.record(
            cls._upsert(
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
                immutable_fields=(),
            )
        )
        session.flush()
        stats.record(
            cls._upsert(
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
                immutable_fields=("university_id", "code"),
            )
        )
        session.flush()
        for program in canonical.programs:
            stats.record(
                cls._upsert(
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
                    immutable_fields=("direction_id", "code"),
                )
            )
        session.flush()
        SqlAlchemyAdmissionRepository(session).sync(canonical.admissions)
        session.flush()
        event_stats = SqlAlchemyEventRepository(session).sync(
            canonical.events,
            source_scope="bmstu_events" if event_source_present else None,
        )
        stats.inserted += event_stats.inserted + event_stats.venues
        stats.updated += event_stats.updated
        stats.unchanged += event_stats.unchanged
        stats.removed += event_stats.removed
        session.flush()
        campus_stats = SqlAlchemyCampusPointRepository(session).sync(
            canonical.campus_points,
            source_scope="bmstu_campus_points" if campus_source_present else None,
        )
        stats.inserted += campus_stats.inserted
        stats.updated += campus_stats.updated
        stats.unchanged += campus_stats.unchanged
        stats.removed += campus_stats.removed
        session.flush()
        disciplines_by_id = {discipline.id: discipline for discipline in canonical.disciplines}
        for discipline in canonical.disciplines:
            stats.record(
                cls._upsert(
                    session,
                    DisciplineModel,
                    discipline.id,
                    {"id": discipline.id, "name": discipline.name, "normalized_name": discipline.normalized_name},
                    immutable_fields=("normalized_name",),
                )
            )
        session.flush()
        for discipline in canonical.disciplines:
            cls._sync_discipline_area_weights(session, discipline.id, discipline.area_weights, stats)
        session.flush()
        expected_item_ids: dict[str, set[str]] = {}
        pending_assessments: dict[str, set[str]] = {}
        for curriculum in canonical.curricula:
            stats.record(
                cls._upsert(
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
                    immutable_fields=("program_id", "education_year"),
                )
            )
            expected_item_ids[curriculum.id] = set()
        # Models intentionally have no ORM relationships. Flush all parent
        # curricula before inserting child items so SQLite and PostgreSQL see
        # the same FK ordering.
        session.flush()
        for curriculum in canonical.curricula:
            for item in curriculum.items:
                if item.discipline_id not in disciplines_by_id:
                    raise ContractError(ErrorCode.CONTRACT_ERROR, "Curriculum item discipline is missing")
                expected_item_ids[curriculum.id].add(item.id)
                stats.record(
                    cls._upsert(
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
                        immutable_fields=("curriculum_id", "discipline_id", "semester", "semester_identity"),
                    )
                )
                pending_assessments[item.id] = {assessment.value for assessment in item.assessment_types or ()}
        session.flush()
        cls._remove_stale_items(session, expected_item_ids, stats)
        session.flush()
        cls._sync_assessments(session, pending_assessments, stats)
        return stats

    @staticmethod
    def _upsert(
        session: Session,
        model: type[Any],
        identity: str,
        values: dict[str, object],
        *,
        immutable_fields: tuple[str, ...],
    ) -> str:
        existing = session.get(model, identity)
        if existing is None:
            session.add(model(**values))
            logger.debug("ingest_projection_insert model=%s identity=%s", model.__name__, identity)
            return "inserted"
        immutable = set(immutable_fields)
        changed: list[str] = []
        for field, expected in values.items():
            if field == "id":
                continue
            actual = getattr(existing, field)
            if not _values_equal(actual, expected):
                if field in immutable:
                    logger.error("ingest_identity_conflict model=%s identity=%s field=%s", model.__name__, identity, field)
                    raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Identity conflict for {identity}: {field}")
                setattr(existing, field, expected)
                changed.append(field)
        if changed:
            logger.debug("ingest_projection_update model=%s identity=%s fields=%s", model.__name__, identity, ",".join(changed))
            return "updated"
        return "unchanged"

    @staticmethod
    def _remove_stale_items(session: Session, expected_item_ids: dict[str, set[str]], stats: _SyncStats) -> None:
        for curriculum_id, expected_ids in expected_item_ids.items():
            existing_ids = set(
                session.scalars(
                    select(CurriculumItemModel.id).where(CurriculumItemModel.curriculum_id == curriculum_id)
                ).all()
            )
            stale_ids = existing_ids - expected_ids
            if stale_ids:
                session.execute(delete(CurriculumItemAssessmentModel).where(CurriculumItemAssessmentModel.curriculum_item_id.in_(stale_ids)))
                session.execute(delete(CurriculumItemModel).where(CurriculumItemModel.id.in_(stale_ids)))
                stats.removed += len(stale_ids)
                logger.warning("ingest_projection_remove_stale curriculum_id=%s count=%d", curriculum_id, len(stale_ids))

    @staticmethod
    def _sync_assessments(session: Session, expected: dict[str, set[str]], stats: _SyncStats) -> None:
        for item_id, expected_types in expected.items():
            current_rows = session.execute(
                select(CurriculumItemAssessmentModel).where(CurriculumItemAssessmentModel.curriculum_item_id == item_id)
            ).scalars().all()
            current_types = {row.assessment_type_id for row in current_rows}
            stale_types = current_types - expected_types
            if stale_types:
                session.execute(
                    delete(CurriculumItemAssessmentModel).where(
                        CurriculumItemAssessmentModel.curriculum_item_id == item_id,
                        CurriculumItemAssessmentModel.assessment_type_id.in_(stale_types),
                    )
                )
                stats.removed += len(stale_types)
            for assessment_type_id in expected_types - current_types:
                session.add(CurriculumItemAssessmentModel(curriculum_item_id=item_id, assessment_type_id=assessment_type_id))
                stats.inserted += 1

    @staticmethod
    def _sync_discipline_area_weights(
        session: Session,
        discipline_id: str,
        area_weights: tuple[DisciplineAreaWeight, ...],
        stats: _SyncStats,
    ) -> None:
        expected = {weight.area.value: weight.weight for weight in area_weights}
        existing_rows = session.execute(
            select(DisciplineAreaWeightModel).where(DisciplineAreaWeightModel.discipline_id == discipline_id)
        ).scalars().all()
        existing = {row.area_id: row for row in existing_rows}
        for area_id in set(existing) - set(expected):
            session.delete(existing[area_id])
            stats.removed += 1
        for area_id, weight in expected.items():
            row = existing.get(area_id)
            if row is None:
                session.add(DisciplineAreaWeightModel(discipline_id=discipline_id, area_id=area_id, weight=weight))
                stats.inserted += 1
            elif not _values_equal(row.weight, weight):
                row.weight = weight
                stats.updated += 1
        logger.debug("ingest_taxonomy_sync discipline_id=%s expected_areas=%d", discipline_id, len(expected))

    @staticmethod
    def _insert_or_validate(session: Session, model: type[Any], identity: str, values: dict[str, object]) -> None:
        """Compatibility shim for older callers; new writes use _upsert."""
        SqlAlchemyIngestionRepository._upsert(session, model, identity, values, immutable_fields=tuple(values))


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


def _safe_error_code(error: Exception) -> str:
    if isinstance(error, AndromedaError):
        return error.code.value
    return "INGESTION_FAILED"


def _safe_error_message(error: Exception) -> str:
    del error
    return "Ingestion failed"
