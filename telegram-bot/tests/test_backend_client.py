from __future__ import annotations

import json

import httpx
import pytest

from andromeda_telegram.clients.backend import BackendHttpClient
from andromeda_telegram.clients.errors import BackendError


@pytest.mark.asyncio
async def test_backend_client_keeps_rotated_profile_cookie() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["cookie"] == "andromeda_profile_session=old"
        return httpx.Response(
            200,
            json={"items": []},
            headers={"set-cookie": "andromeda_profile_session=new; Path=/; HttpOnly"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await BackendHttpClient("http://backend", client=client).list_programs(session_cookie="old")

    assert result.value.items == []
    assert result.session_cookie == "new"


@pytest.mark.asyncio
async def test_backend_client_maps_conflict_without_response_body() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"profile": "private"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(BackendError, match="stale") as error:
            await BackendHttpClient("http://backend", client=client).get_suggestions()

        assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_backend_client_forwards_channel_neutral_assistant_query() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/assistant/query"
        assert request.headers["cookie"] == "andromeda_profile_session=opaque"
        assert json.loads(request.read()) == {"text": "Где больше математики?"}
        return httpx.Response(
            200,
            json={
                "state": "needs_clarification",
                "session_id": "query-session:" + "a" * 32,
                "revision": 2,
                "question": "Какую программу взять?",
                "options": [],
                "missing_slots": ["entity"],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await BackendHttpClient("http://backend", client=client).assistant_query(
            "Где больше математики?",
            session_cookie="opaque",
        )

    assert result.value.state == "needs_clarification"
    assert result.value.revision == 2


@pytest.mark.asyncio
async def test_backend_client_retries_transient_backend_failure_with_bounded_policy() -> None:
    attempts = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, request=_request)
        return httpx.Response(200, json={"items": []}, request=_request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await BackendHttpClient(
            "http://backend",
            retry_attempts=2,
            retry_backoff_seconds=0,
            client=client,
        ).list_programs()

    assert attempts == 2
    assert result.value.items == []
