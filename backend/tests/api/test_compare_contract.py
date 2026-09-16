from __future__ import annotations

from fastapi.testclient import TestClient

from andromeda.api.main import create_app


def test_compare_contract_exposes_both_programs(ingested_db: tuple[str, object, object]) -> None:
    database_url, _, _ = ingested_db
    response = TestClient(create_app(database_url)).get(
        "/compare?programIds=program:09.03.01-02,program:09.03.01-12"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["programA"]["code"] == "09.03.01-02"
    assert payload["programB"]["code"] == "09.03.01-12"
    assert all(row["status"] in {"both", "only_a", "only_b", "different"} for row in payload["rows"])
