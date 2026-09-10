from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bmstu_parser.db.base import create_engine_for_url
from bmstu_parser.db.models import EducationalProgramModel, IngestRunModel
from bmstu_parser.tracer.ingest import TracerIngestService
from bmstu_parser.tracer.parser import parse_sources
from bmstu_parser.tracer import TracerSource


def test_replay_is_idempotent_for_domain_rows(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).parents[1] / "fixtures" / "tracer" / "raw"
    raw, normalized = parse_sources(TracerSource(), mode="fixture", fixture_dir=fixture_dir)
    database_url = f"sqlite:///{(tmp_path / 'replay.db').as_posix()}"
    engine = create_engine_for_url(database_url)
    from bmstu_parser.db.base import Base

    Base.metadata.create_all(engine)
    service = TracerIngestService(engine)
    service.ingest(raw, normalized)
    service.ingest(raw, normalized)

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(IngestRunModel)) == 2
        assert session.scalar(select(func.count()).select_from(EducationalProgramModel)) == 2


def test_partial_ingest_rolls_back_when_identity_conflicts(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).parents[1] / "fixtures" / "tracer" / "raw"
    raw, normalized = parse_sources(TracerSource(), mode="fixture", fixture_dir=fixture_dir)
    database_url = f"sqlite:///{(tmp_path / 'rollback.db').as_posix()}"
    engine = create_engine_for_url(database_url)
    from bmstu_parser.db.base import Base

    Base.metadata.create_all(engine)
    service = TracerIngestService(engine)
    service.ingest(raw, normalized)
    conflicting_program = normalized.programs[0].model_copy(update={"name": "contract-conflict"})
    conflicting = normalized.model_copy(update={"programs": (conflicting_program, *normalized.programs[1:])})

    try:
        service.ingest(raw, conflicting)
    except Exception:
        pass
    else:
        raise AssertionError("conflicting identity must fail")

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(IngestRunModel)) == 1
