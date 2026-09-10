from __future__ import annotations

from pathlib import Path

import pytest

from bmstu_parser.contracts.domain import NormalizedTracerSnapshot
from bmstu_parser.contracts.raw import RawTracerBundle
from bmstu_parser.db.base import Base, create_engine_for_url
from bmstu_parser.tracer import TracerSource, parse_sources
from bmstu_parser.tracer.ingest import TracerIngestService

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "tracer" / "raw"
PROGRAM_A = "program:09.03.01-02"
PROGRAM_B = "program:09.03.01-12"


@pytest.fixture
def parsed_bundle() -> tuple[RawTracerBundle, NormalizedTracerSnapshot]:
    return parse_sources(TracerSource(), mode="fixture", fixture_dir=FIXTURE_DIR)


@pytest.fixture
def ingested_db(tmp_path: Path, parsed_bundle: tuple[RawTracerBundle, NormalizedTracerSnapshot]) -> tuple[str, RawTracerBundle, NormalizedTracerSnapshot]:
    raw, normalized = parsed_bundle
    database_url = f"sqlite:///{(tmp_path / 'tracer.db').as_posix()}"
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    TracerIngestService(engine).ingest(raw, normalized)
    return database_url, raw, normalized
