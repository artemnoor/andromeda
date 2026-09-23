from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

from andromeda.api.main import create_app

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from run_andromeda_bmstu import run_ingest  # noqa: I001


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
        assert third_payload["state"] == "needs_clarification"
        assert third_payload["missing_slots"] == ["funding"]
        assert "бюджет или платное" in third_payload["question"].casefold()
        assert third_payload["options"] == ["Бюджет", "Платное"]

        fourth = client.post(
            "/assistant/query",
            json={
                "text": "бюджет",
                "sessionId": third_payload["session_id"],
                "expectedRevision": third_payload["revision"],
            },
        )
        assert fourth.status_code == 200, fourth.text
        fourth_payload = fourth.json()
        assert fourth_payload["state"] == "complete"
        assert fourth_payload["admission_request"]["program_ids"]
        assert fourth_payload["admission_result"]["by_program_id"]
        assert fourth_payload["admission_request"]["admission_year"] == 2026
        assert fourth_payload["admission_request"]["study_form"] == "full_time"
        assert fourth_payload["admission_request"]["funding_type"] == "budget"
        assert fourth_payload["response"]["template"] == "admission-fit-summary"
        assert "2026" in fourth_payload["response"]["text"]
        assert "очная" in fourth_payload["response"]["text"]
        assert "последний опубликованный год" in fourth_payload["response"]["text"]
        assert fourth_payload["response"]["metadata"]["assumptions"] == [
            "Год приёма: 2026 (последний опубликованный год)",
            "Форма обучения: очная (по умолчанию)",
        ]


def test_assistant_uses_explicit_admission_filters_without_reasking(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        result = client.post(
            "/assistant/query",
            json={
                "text": (
                    "Куда поступить в 2026 году очно на бюджет: русский 90, "
                    "математика 90, физика 90, university:bmstu"
                )
            },
        )

        assert result.status_code == 200, result.text
        payload = result.json()
        assert payload["state"] == "complete"
        request = payload["admission_request"]
        assert request["admission_year"] == 2026
        assert request["study_form"] == "full_time"
        assert request["funding_type"] == "budget"
        assert "последний опубликованный год" not in payload["response"]["text"]
        assert payload["response"]["metadata"]["assumptions"] == []


def test_assistant_accepts_any_university_scope_and_checks_full_fixture_catalog(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        first = client.post(
            "/assistant/query",
            json={"text": "Куда я прохожу с 270: русский 90, математика 90, информатика 90"},
        )
        assert first.status_code == 200, first.text
        first_payload = first.json()
        assert first_payload["state"] == "needs_clarification"
        assert first_payload["missing_slots"] == ["university_scope"]

        result = client.post(
            "/assistant/query",
            json={
                "text": "Любые вузы",
                "sessionId": first_payload["session_id"],
                "expectedRevision": first_payload["revision"],
            },
        )

        assert result.status_code == 200, result.text
        clarification = result.json()
        assert clarification["state"] == "needs_clarification"
        assert clarification["missing_slots"] == ["funding"]

        result = client.post(
            "/assistant/query",
            json={
                "text": "платное",
                "sessionId": clarification["session_id"],
                "expectedRevision": clarification["revision"],
            },
        )
        assert result.status_code == 200, result.text
        payload = result.json()
        assert payload["state"] == "complete"
        assert payload["admission_request"]["funding_type"] == "paid"
        assert payload["admission_request"]["admission_year"] == 2026
        assert payload["admission_request"]["study_form"] == "full_time"
        assert payload["admission_result"]["by_program_id"]
        submitted_ids = tuple(
            program_id
            for batch in payload["admission_requests"]
            for program_id in batch["program_ids"]
        )
        assert set(payload["admission_result"]["by_program_id"]) == set(submitted_ids)


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
