from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from proftest_spike.questions.bank import BASE_QUESTIONS

from .test_catalog_api import FakeReader, _app_for
from .test_program_fingerprints import _curriculum


def _payload(*, physics_anti: str | None = None) -> dict[str, object]:
    answers: list[dict[str, object]] = []
    for question in BASE_QUESTIONS:
        if question.id == "anti_interest_areas":
            if physics_anti is not None:
                answers.append({"questionId": question.id, "optionId": "anti_physics", "intensity": physics_anti})
            continue
        answers.append({"questionId": question.id, "optionId": question.options[0].id})
    return {"answers": answers, "adaptiveAnswers": []}


def test_preview_exposes_adaptive_contract_after_base_profile() -> None:
    app = _app_for(FakeReader((_curriculum("first"), _curriculum("second", hours=(100, 0)))))
    with TestClient(app) as client:
        response = client.post("/api/test/preview", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["progress"]["answeredBase"] == 5
    assert body["adaptive"]["status"] in {"ready", "skipped"}
    if body["adaptive"]["status"] == "ready":
        assert len(body["adaptive"]["question"]["options"]) == 3


def test_results_are_explainable_and_optional_metrics_are_unavailable() -> None:
    app = _app_for(FakeReader((_curriculum("first"), _curriculum("second", hours=(100, 0)))))
    with TestClient(app) as client:
        response = client.post("/api/test/results", json=_payload(physics_anti="0.95"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["recommendations"]
    recommendation = body["recommendations"][0]
    assert isinstance(recommendation["contentFit"], int)
    assert all(metric["value"] is None and metric["status"] == "not_available" for metric in recommendation["metrics"])
    assert any(reason["kind"] in {"positive", "negative", "distinctive"} for reason in recommendation["reasons"])


def test_empty_catalog_results_have_explicit_empty_state() -> None:
    app = _app_for(FakeReader(()))
    with TestClient(app) as client:
        response = client.post("/api/test/results", json=_payload())

    assert response.status_code == 200
    assert response.json()["status"] == "empty"
    assert response.json()["recommendations"] == []
