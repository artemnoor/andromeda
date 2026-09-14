from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from andromeda.api.main import create_app
from andromeda.infrastructure.database import Base, create_engine_for_url
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository
from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter


OPS_KEY = "test-only-admin-ops-key"


def _database_with_fixture(tmp_path: Path) -> str:
    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw")
    finally:
        adapter.close()
    database_url = f"sqlite:///{(tmp_path / 'admin-ops-api.db').as_posix()}"
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    SqlAlchemyIngestionRepository(engine).ingest(raw, canonical)
    return database_url


def test_admin_ops_api_is_not_discoverable_without_configured_key(tmp_path: Path, monkeypatch, caplog) -> None:
    monkeypatch.delenv("ANDROMEDA_OPS_API_KEY", raising=False)
    client = TestClient(create_app(_database_with_fixture(tmp_path)))
    response = client.get("/ops/ingestion/runs")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert OPS_KEY not in caplog.text


def test_admin_ops_api_exposes_bounded_read_contract_only_with_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ANDROMEDA_OPS_API_KEY", OPS_KEY)
    database_url = _database_with_fixture(tmp_path)
    client = TestClient(create_app(database_url))

    headers = {"X-Andromeda-Ops-Key": OPS_KEY}
    listing = client.get("/ops/ingestion/runs", params={"limit": 1}, headers=headers)
    assert listing.status_code == 200, listing.text
    payload = listing.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    run_id = payload["items"][0]["id"]

    detail = client.get(f"/ops/ingestion/runs/{run_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    run = detail.json()["run"]
    assert run["status"] == "completed"
    assert run["sourceHashes"]
    assert "body" not in detail.text
    assert "payload_json" not in detail.text

    wrong_key = client.get("/ops/ingestion/runs", headers={"X-Andromeda-Ops-Key": "wrong"})
    invalid_limit = client.get("/ops/ingestion/runs", params={"limit": 101}, headers=headers)
    missing = client.get("/ops/ingestion/runs/ingest:" + "f" * 32, headers=headers)
    assert wrong_key.status_code == 404
    assert invalid_limit.status_code == 422
    assert missing.status_code == 404
