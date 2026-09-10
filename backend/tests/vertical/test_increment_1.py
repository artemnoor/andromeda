from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bmstu_parser.api.main import create_app
from bmstu_parser.db.base import Base, create_engine_for_url
from bmstu_parser.tracer import TracerSource, parse_sources
from bmstu_parser.tracer.ingest import TracerIngestService


def test_first_real_program_crosses_parser_db_and_api(tmp_path: Path) -> None:
    raw, normalized = parse_sources(
        TracerSource(),
        mode="fixture",
        fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw",
        program_codes=("09.03.01-02",),
    )
    database_url = f"sqlite:///{(tmp_path / 'increment-1.db').as_posix()}"
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    TracerIngestService(engine).ingest(raw, normalized)

    response = TestClient(create_app(database_url)).get("/programs/program:09.03.01-02")

    assert response.status_code == 200
    payload = response.json()
    assert payload["program"]["id"] == "program:09.03.01-02"
    assert payload["direction"]["code"] == "09.03.01"
    assert payload["source"]["kind"] == "bmstu_major_detail"
