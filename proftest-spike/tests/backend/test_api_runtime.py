from __future__ import annotations

from fastapi.testclient import TestClient

from proftest_spike.api.main import create_app
from proftest_spike.composition.container import build_container
from proftest_spike.composition.settings import Settings


def test_health_and_bootstrap_are_typed_public_contracts() -> None:
    container = build_container(Settings(andromeda_api_base_url="https://andromeda.test"))
    app = create_app(container)
    with TestClient(app) as client:
        health = client.get("/api/health")
        bootstrap = client.get("/api/test/bootstrap")
    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "service": "andromeda-proftest-spike",
        "version": "0.1.0",
        "dataSource": "andromeda_http_api",
    }
    assert bootstrap.status_code == 200
    assert bootstrap.json()["catalogStatus"] == "not_loaded"
    assert bootstrap.json()["questions"]
    assert bootstrap.json()["totalBase"] == len(bootstrap.json()["questions"])


def test_api_schema_rejects_unknown_response_fields() -> None:
    container = build_container(Settings(andromeda_api_base_url="https://andromeda.test"))
    app = create_app(container)
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert "unexpected" not in response.json()
