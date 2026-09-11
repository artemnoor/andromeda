from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from andromeda.api.main import create_app
from andromeda.infrastructure.database import create_engine_for_url
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository
from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter


def test_postgresql_supports_the_existing_api_vertical_slice() -> None:
    database_url = os.environ.get("ANDROMEDA_POSTGRES_TEST_URL")
    if not database_url or not database_url.startswith(("postgresql://", "postgresql+")):
        pytest.skip("ANDROMEDA_POSTGRES_TEST_URL is not configured")

    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw")
    finally:
        adapter.close()

    engine = create_engine_for_url(database_url)
    try:
        SqlAlchemyIngestionRepository(engine).ingest(raw, canonical)
    finally:
        engine.dispose()

    client = TestClient(create_app(database_url))
    programs = client.get("/programs")
    curriculum = client.get("/programs/program:09.03.01-02/curriculum")
    comparison = client.get(
        "/compare",
        params={"programIds": "program:09.03.01-02,program:09.03.01-12", "scope": "semester", "semester": 1},
    )
    answers = {
        "answers": [
            {"questionId": "interest_free_day", "optionIds": ["software_tool"]},
            {"questionId": "interest_investigation", "optionIds": ["prove_model"]},
            {"questionId": "activity_build", "optionIds": ["system_scheme"]},
            {"questionId": "activity_working_style", "optionIds": ["analyze_options"]},
            {"questionId": "anti_subjects", "optionIds": ["avoid_physics"], "intensity": 0.9},
            {"questionId": "activity_depth", "optionIds": ["practical_prototype"]},
        ]
    }
    proftest = client.post("/proftest/results", json=answers)

    assert programs.status_code == 200
    assert len(programs.json()["items"]) == 2
    assert curriculum.status_code == 200
    assert curriculum.json()["items"]
    assert comparison.status_code == 200
    assert comparison.json()["rows"]
    assert proftest.status_code == 200
    profile = proftest.json()["profile"]
    recommendations = client.post("/recommendations", json={"profile": profile, "limit": 2})
    assert recommendations.status_code == 200
    assert len(recommendations.json()["recommendations"]) == 2
