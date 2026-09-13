from __future__ import annotations

import json

import httpx
import pytest

from proftest_spike.api_client.client import AndromedaApiClient
from proftest_spike.api_client.errors import ApiContractError, ApiNotFound, ApiUnavailable


def _program() -> dict[str, object]:
    return {
        "id": "program:iu7-01",
        "directionId": "direction:iu7",
        "code": "iu7-01",
        "name": "Информатика и системы управления",
        "educationYear": 2025,
        "studyPlanUrl": "https://bmstu.example/plan",
        "sourceUrl": "https://bmstu.example/program",
    }


def _curriculum() -> dict[str, object]:
    return {
        "program": _program(),
        "curriculumId": "curriculum:iu7-01",
        "educationYear": 2025,
        "sourceUrl": "https://bmstu.example/curriculum",
        "capturedAt": "2026-09-10T10:00:00Z",
        "items": [
            {
                "id": "item:1",
                "discipline": {
                    "id": "discipline:1",
                    "name": "Программирование",
                    "normalizedName": "программирование",
                    "areaWeights": [{"area": "computer_science_data", "weight": 1.0}],
                    "primaryArea": "computer_science_data",
                },
                "sourceName": "Программирование",
                "semester": 1,
                "hours": 144,
                "credits": 4.0,
                "assessmentTypes": ["exam"],
                "subjectGroup": "Профессиональный цикл",
                "sourcePosition": 1,
            }
        ],
    }


@pytest.mark.asyncio
async def test_get_programs_validates_strict_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/programs"
        return httpx.Response(200, json={"items": [_program()]})

    client = AndromedaApiClient("https://andromeda.test", transport=httpx.MockTransport(handler))
    try:
        result = await client.get_programs_contract()
    finally:
        await client.aclose()
    assert result.items[0].id == "program:iu7-01"


@pytest.mark.asyncio
async def test_get_curriculum_validates_nested_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/programs/program:iu7-01/curriculum"
        return httpx.Response(200, json=_curriculum())

    client = AndromedaApiClient("https://andromeda.test", transport=httpx.MockTransport(handler))
    try:
        result = await client.get_curriculum("program:iu7-01")
    finally:
        await client.aclose()
    assert result.items[0].hours == 144


@pytest.mark.asyncio
async def test_current_api_area_vector_code_maps_to_canonical_area() -> None:
    payload = _curriculum()
    item = payload["items"][0]
    assert isinstance(item, dict)
    discipline = item["discipline"]
    assert isinstance(discipline, dict)
    discipline["areaWeights"] = [
        {
            "code": "computer_science_data",
            "name": "Компьютерные науки и данные",
            "description": "Программирование и цифровые системы",
            "weight": "1.0000",
        }
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json=payload)

    client = AndromedaApiClient("https://andromeda.test", transport=httpx.MockTransport(handler))
    try:
        result = await client.get_curriculum("program:iu7-01")
    finally:
        await client.aclose()
    assert result.items[0].discipline.area_weights[0].area.value == "computer_science_data"


@pytest.mark.asyncio
async def test_timeout_is_typed_as_unavailable() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        raise httpx.ReadTimeout("timed out")

    client = AndromedaApiClient("https://andromeda.test", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ApiUnavailable):
            await client.get_programs_contract()
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_not_found_is_typed() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(404, json={"detail": "not found"})

    client = AndromedaApiClient("https://andromeda.test", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ApiNotFound):
            await client.get_curriculum("program:missing")
    finally:
        await client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"items": [{"id": "program:1"}]},
        {"items": [{**_program(), "unexpected": True}]},
    ],
)
async def test_missing_or_unknown_field_fails_closed(payload: dict[str, object]) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json=payload)

    client = AndromedaApiClient("https://andromeda.test", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ApiContractError) as error:
            await client.get_programs_contract()
    finally:
        await client.aclose()
    assert error.value.error_path


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value["items"][0].update({"educationYear": "2025"}),
        lambda value: value["items"][0].update({"studyPlanUrl": "not a url"}),
    ],
)
async def test_invalid_program_scalar_fails_contract(mutator) -> None:
    payload = {"items": [_program()]}
    mutator(payload)

    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, content=json.dumps(payload).encode("utf-8"))

    client = AndromedaApiClient("https://andromeda.test", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ApiContractError):
            await client.get_programs_contract()
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_non_json_response_fails_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, content=b"not-json", headers={"content-type": "text/plain"})

    client = AndromedaApiClient("https://andromeda.test", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ApiContractError):
            await client.get_programs_contract()
    finally:
        await client.aclose()
