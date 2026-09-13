from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from andromeda.infrastructure.database import Base, create_engine_for_url
from andromeda.infrastructure.database.models import AdmissionOfferingModel
from andromeda.infrastructure.repositories.admissions import SqlAlchemyAdmissionRepository
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository
from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter


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
