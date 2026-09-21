from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

from andromeda.api.main import create_app

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from run_andromeda_bmstu import run_ingest  # noqa: E402, I001


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "tracer" / "raw"


def _client(tmp_path: Path) -> TestClient:
    database_url = f"sqlite:///{(tmp_path / 'assistant-api.db').as_posix()}"
    run_ingest(mode="fixture", fixture_dir=FIXTURE_DIR, database_url=database_url, program_codes=())
    return TestClient(create_app(database_url))


def test_assistant_admission_flow_keeps_typed_session_state(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        first = client.post("/assistant/query", json={"text": "Куда я прохожу с 270?"})
        assert first.status_code == 200, first.text
        first_payload = first.json()
        assert first_payload["state"] == "needs_clarification"
        assert first_payload["missing_slots"] == ["exams"]

        second = client.post(
            "/assistant/query",
            json={
                "text": "русский 90, математика 90, информатика 90",
                "sessionId": first_payload["session_id"],
                "expectedRevision": first_payload["revision"],
            },
        )
        assert second.status_code == 200, second.text
        second_payload = second.json()
        assert second_payload["state"] == "needs_clarification"
        assert second_payload["missing_slots"] == ["university_scope"]

        third = client.post(
            "/assistant/query",
            json={
                "text": "university:bmstu",
                "sessionId": second_payload["session_id"],
                "expectedRevision": second_payload["revision"],
            },
        )
        assert third.status_code == 200, third.text
        third_payload = third.json()
        assert third_payload["state"] == "complete"
        assert third_payload["admission_request"]["program_ids"]
        assert third_payload["admission_result"]["by_program_id"]
        assert third_payload["response"]["template"] == "admission-fit-summary"


def test_assistant_analytics_flow_returns_channel_neutral_envelope(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post(
            "/assistant/query",
            json={
                "text": "Где больше математики между program:bmstu:09.03.01-02 и program:bmstu:09.03.01-12?",
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["state"] == "complete"
        assert payload["query"]["scope"] == "program"
        assert payload["response"]["response_type"] == "image"
        assert payload["response"]["template"] == "metric-comparison"
