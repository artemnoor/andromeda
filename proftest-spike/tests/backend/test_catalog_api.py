from __future__ import annotations

import json

from fastapi.testclient import TestClient

from proftest_spike.api_client.contracts import CurriculumResponse, ProgramListResponse
from proftest_spike.api_client.errors import ApiUnavailable
from proftest_spike.api.main import create_app
from proftest_spike.catalog.service import CatalogService
from proftest_spike.composition.container import Container
from proftest_spike.composition.settings import Settings
from proftest_spike.profiling.profile_builder import UserProfileBuilder
from proftest_spike.questions.service import QuestionService

from .test_program_fingerprints import _curriculum, _program


class FakeReader:
    def __init__(self, curricula: tuple[CurriculumResponse, ...], *, fail: bool = False) -> None:
        self.curricula = {item.program.id: item for item in curricula}
        self.fail = fail

    async def get_programs_contract(self) -> ProgramListResponse:
        return ProgramListResponse(items=tuple(_program(item.program.code) for item in self.curricula.values()))

    async def get_curriculum(self, program_id: str) -> CurriculumResponse:
        if self.fail:
            raise ApiUnavailable("upstream down", endpoint="/programs/{id}/curriculum")
        return self.curricula[program_id]


def _app_for(reader: FakeReader):
    settings = Settings(andromeda_api_base_url="https://andromeda.test")
    fake_andromeda = reader
    questions = QuestionService()
    container = Container(
        settings=settings,
        andromeda=fake_andromeda,
        catalog=CatalogService(reader, ttl_seconds=300),
        questions=questions,
        profile_builder=UserProfileBuilder(questions.list_base()),
    )
    return create_app(container)


def test_catalog_api_returns_typed_fingerprint_summaries() -> None:
    app = _app_for(FakeReader((_curriculum("first"), _curriculum("second", hours=(100, 0)))))
    with TestClient(app) as client:
        response = client.get("/api/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["programCount"] == 2
    assert payload["curriculumItemCount"] == 4
    assert payload["programs"][0]["areaShare"]
    assert payload["programs"][0]["distinctiveSubjects"]
    assert "evidence" not in payload["programs"][0]


def test_empty_catalog_is_explicit_not_an_error() -> None:
    app = _app_for(FakeReader(()))
    with TestClient(app) as client:
        response = client.get("/api/catalog")

    assert response.status_code == 200
    assert response.json()["status"] == "empty"
    assert response.json()["programs"] == []


def test_upstream_failure_is_mapped_to_typed_error_state() -> None:
    app = _app_for(FakeReader((_curriculum("first"),), fail=True))
    with TestClient(app) as client:
        response = client.get("/api/catalog")

    assert response.status_code == 200
    assert response.json()["status"] == "empty"
    assert response.json()["failedProgramCount"] == 1


def test_partial_catalog_is_explicit() -> None:
    class PartialReader(FakeReader):
        async def get_curriculum(self, program_id: str) -> CurriculumResponse:
            if program_id.endswith("second"):
                raise ApiUnavailable("missing", endpoint="/programs/{id}/curriculum")
            return await super().get_curriculum(program_id)

    app = _app_for(PartialReader((_curriculum("first"), _curriculum("second"))))
    with TestClient(app) as client:
        response = client.get("/api/catalog")

    assert response.status_code == 200
    assert response.json()["status"] == "partial"
    assert response.json()["programCount"] == 1
    assert response.json()["failedProgramCount"] == 1
