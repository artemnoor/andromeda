from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from andromeda.infrastructure.database import Base, create_engine_for_url
from andromeda.infrastructure.database.models import AdmissionOfferingModel, AdmissionPassingScoreModel
from andromeda.infrastructure.repositories.admissions import SqlAlchemyAdmissionRepository
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository
from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter
from andromeda.modules.admissions.contracts.public import (
    AdmissionCompetitionType,
    PassingScore,
    PassingScoreStatus,
    PassingScoreType,
)


def test_admission_projection_round_trips_through_repository_and_preserves_fk(tmp_path: Path) -> None:
    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw")
    finally:
        adapter.close()

    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'admissions.db').as_posix()}")
    Base.metadata.create_all(engine)
    SqlAlchemyIngestionRepository(engine).ingest(raw, canonical)

    with Session(engine) as session:
        admissions = SqlAlchemyAdmissionRepository(session).get_for_program("program:09.03.01-02")
        offering_ids = [offering.id for offering in admissions.offerings]
        persisted_program_ids = session.scalars(
            select(AdmissionOfferingModel.program_id).where(AdmissionOfferingModel.id.in_(offering_ids))
        ).all()

    assert len(admissions.offerings) == 10
    assert set(persisted_program_ids) == {"program:09.03.01-02"}
    assert all(offering.program_id == "program:09.03.01-02" for offering in admissions.offerings)
    assert any(offering.tuition for offering in admissions.offerings)
    assert any(offering.passing_scores for offering in admissions.offerings)
    foreign_keys = inspect(engine).get_foreign_keys("admission_offerings")
    assert any(foreign_key["referred_table"] == "educational_programs" and foreign_key["constrained_columns"] == ["program_id"] for foreign_key in foreign_keys)


def test_route_aware_passing_scores_round_trip_and_stale_children_are_removed(tmp_path: Path) -> None:
    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw")
    finally:
        adapter.close()

    target_program = next(item for item in canonical.admissions if item.program_id == "program:09.03.01-02")
    target_offering = next(item for item in target_program.offerings if item.admission_year == 2026 and item.funding_type.value == "budget")
    source = target_offering.provenance[0]
    route_scores = (
        PassingScore(
            score_type=PassingScoreType.BUDGET,
            competition_type=AdmissionCompetitionType.GENERAL,
            score=Decimal("220"),
            provenance=source,
        ),
        PassingScore(
            score_type=PassingScoreType.BUDGET,
            competition_type=AdmissionCompetitionType.TARGETED,
            score=Decimal("195"),
            provenance=source,
        ),
        PassingScore(
            score_type=PassingScoreType.BUDGET,
            competition_type=AdmissionCompetitionType.SEPARATE_QUOTA,
            status=PassingScoreStatus.BVI,
            score=None,
            provenance=source,
        ),
    )
    updated_offering = target_offering.model_copy(update={"passing_scores": route_scores})
    updated_program = target_program.model_copy(update={"offerings": (updated_offering, *[item for item in target_program.offerings if item.id != target_offering.id])})
    updated_canonical = canonical.model_copy(
        update={
            "admissions": (updated_program, *[item for item in canonical.admissions if item.program_id != target_program.program_id]),
        }
    )

    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'route-aware-admissions.db').as_posix()}")
    try:
        Base.metadata.create_all(engine)
        ingestion = SqlAlchemyIngestionRepository(engine)
        ingestion.ingest(raw, updated_canonical)
        ingestion.ingest(raw, updated_canonical)

        with Session(engine) as session:
            rows = session.scalars(
                select(AdmissionPassingScoreModel).where(AdmissionPassingScoreModel.offering_id == target_offering.id)
            ).all()
            loaded = SqlAlchemyAdmissionRepository(session).get_for_program("program:09.03.01-02")

        assert len(rows) == 3
        assert {(row.competition_type, row.status, row.score) for row in rows} == {
            ("general", "numeric", Decimal("220.00")),
            ("targeted", "numeric", Decimal("195.00")),
            ("separate_quota", "bvi", None),
        }
        loaded_offering = next(item for item in loaded.offerings if item.id == target_offering.id)
        assert {(item.competition_type.value, item.status.value, item.score) for item in loaded_offering.passing_scores} == {
            ("general", "numeric", Decimal("220.00")),
            ("targeted", "numeric", Decimal("195.00")),
            ("separate_quota", "bvi", None),
        }

        replacement = updated_offering.model_copy(update={"passing_scores": (route_scores[0],)})
        replaced_program = target_program.model_copy(update={"offerings": (replacement, *[item for item in target_program.offerings if item.id != target_offering.id])})
        replaced_canonical = updated_canonical.model_copy(
            update={
                "admissions": (replaced_program, *[item for item in updated_canonical.admissions if item.program_id != target_program.program_id]),
            }
        )
        ingestion.ingest(raw, replaced_canonical)
        with Session(engine) as session:
            remaining = session.scalars(
                select(AdmissionPassingScoreModel).where(AdmissionPassingScoreModel.offering_id == target_offering.id)
            ).all()
        assert len(remaining) == 1
        assert remaining[0].competition_type == "general"
    finally:
        engine.dispose()
