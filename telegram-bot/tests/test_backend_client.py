from __future__ import annotations

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
