from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter
from andromeda.infrastructure.database import Base, create_engine_for_url
from andromeda.infrastructure.database.models import CurriculumItemModel, IngestRunModel, ProgramModel
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository


def test_ingest_is_atomic_on_identity_conflict(tmp_path: Path) -> None:
    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw")
    finally:
        adapter.close()
    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'atomic.db').as_posix()}")
    Base.metadata.create_all(engine)
    repository = SqlAlchemyIngestionRepository(engine)
    repository.ingest(raw, canonical)
    conflict = canonical.model_copy(
        update={"programs": (canonical.programs[0].model_copy(update={"code": "09.03.01-99"}), *canonical.programs[1:])}
    )
    try:
        repository.ingest(raw, conflict)
    except Exception:
        pass
    else:
        raise AssertionError("identity conflict must fail")
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(IngestRunModel)) == 1
        assert session.scalar(select(func.count()).select_from(ProgramModel)) == 2


def test_ingest_updates_mutable_projection_and_removes_stale_items(tmp_path: Path) -> None:
    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw")
    finally:
        adapter.close()
    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'refresh.db').as_posix()}")
    Base.metadata.create_all(engine)
    repository = SqlAlchemyIngestionRepository(engine)
    repository.ingest(raw, canonical)

    original_curriculum = canonical.curricula[0]
    shortened_curriculum = original_curriculum.model_copy(update={"items": original_curriculum.items[:-1]})
    updated = canonical.model_copy(
        update={
            "programs": (canonical.programs[0].model_copy(update={"name": "Обновлённая программа"}), *canonical.programs[1:]),
            "curricula": (shortened_curriculum, *canonical.curricula[1:]),
        }
    )
    repository.ingest(raw, updated)

    with Session(engine) as session:
        assert session.get(ProgramModel, canonical.programs[0].id).name == "Обновлённая программа"
        item_count = session.scalar(
            select(func.count()).select_from(CurriculumItemModel).where(CurriculumItemModel.curriculum_id == original_curriculum.id)
        )
        assert item_count == len(shortened_curriculum.items)


def test_ingest_is_idempotent_for_same_canonical_snapshot(tmp_path: Path) -> None:
    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw")
    finally:
        adapter.close()
    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'idempotent.db').as_posix()}")
    Base.metadata.create_all(engine)
    repository = SqlAlchemyIngestionRepository(engine)

    repository.ingest(raw, canonical)
    repository.ingest(raw, canonical)

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(IngestRunModel)) == 2
        assert session.scalar(select(func.count()).select_from(ProgramModel)) == 2
