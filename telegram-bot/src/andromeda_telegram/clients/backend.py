"""Async HTTP-only adapter for the canonical Andromeda API."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Generic, TypeVar

import httpx
from pydantic import BaseModel

from .errors import BackendError, BackendTransportError
from .models import AnalyticsAccepted, ComparisonSummary, DecisionContext, DecisionSuggestions, MutationResponse, Program, ProgramList, ProgramResponse, RefinementResponse


logger = logging.getLogger("andromeda_telegram.backend")
ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class BackendResult(Generic[ModelT]):
    value: ModelT
    session_cookie: str | None


class BackendHttpClient:
    """Call only public HTTP endpoints; no backend package imports are allowed."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 15.0, retry_attempts: int = 2, retry_backoff_seconds: float = 0.25, client: httpx.AsyncClient | None = None) -> None:
        if not 1 <= retry_attempts <= 3:
            raise ValueError("retry_attempts must be between 1 and 3")
        if not 0 <= retry_backoff_seconds <= 5:
            raise ValueError("retry_backoff_seconds must be between 0 and 5")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._retry_attempts = retry_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._client = client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def list_programs(self, *, session_cookie: str | None = None) -> BackendResult[ProgramList]:
        return await self._request("GET", "/programs", ProgramList, session_cookie=session_cookie)

    async def get_program(self, program_id: str, *, session_cookie: str | None = None) -> BackendResult[Program]:
        result = await self._request("GET", f"/programs/{_path_part(program_id)}", ProgramResponse, session_cookie=session_cookie)
        return BackendResult(result.value.program, result.session_cookie)

    async def get_context(self, *, session_cookie: str | None = None) -> BackendResult[DecisionContext]:
        return await self._request("GET", "/decision/context", DecisionContext, session_cookie=session_cookie)

    async def get_suggestions(self, *, session_cookie: str | None = None) -> BackendResult[DecisionSuggestions]:
        return await self._request("GET", "/decision/suggestions", DecisionSuggestions, session_cookie=session_cookie)

    async def compare_summary(self, program_ids: tuple[str, ...], *, session_cookie: str | None = None) -> BackendResult[ComparisonSummary]:
        if not 2 <= len(program_ids) <= 3:
            raise ValueError("comparison requires two or three programs")
        return await self._request("GET", "/compare/summary", ComparisonSummary, params={"programIds": ",".join(program_ids)}, session_cookie=session_cookie)

    async def answer_refinement(self, question_id: str, option_id: str, expected_revision: int, *, session_cookie: str | None = None) -> BackendResult[RefinementResponse]:
        return await self._request(
            "POST",
            "/decision/refinement/answer",
            RefinementResponse,
            json={"questionId": question_id, "optionId": option_id, "expectedRevision": expected_revision},
            session_cookie=session_cookie,
        )

    async def add_shortlist(self, program_id: str, expected_revision: int, *, session_cookie: str | None = None) -> BackendResult[MutationResponse]:
        return await self._request("POST", "/decision/shortlist", MutationResponse, json={"programId": program_id, "role": "primary", "expectedRevision": expected_revision}, session_cookie=session_cookie)

    async def remove_shortlist(self, program_id: str, expected_revision: int, *, session_cookie: str | None = None) -> BackendResult[MutationResponse]:
        return await self._request("DELETE", f"/decision/shortlist/{_path_part(program_id)}", MutationResponse, json={"expectedRevision": expected_revision}, session_cookie=session_cookie)

    async def set_shortlist_role(self, program_id: str, role: str, expected_revision: int, *, session_cookie: str | None = None) -> BackendResult[MutationResponse]:
        return await self._request("PATCH", f"/decision/shortlist/{_path_part(program_id)}", MutationResponse, json={"role": role, "expectedRevision": expected_revision}, session_cookie=session_cookie)

    async def update_constraints(self, scores: list[dict[str, str | int]], expected_revision: int, *, session_cookie: str | None = None) -> BackendResult[MutationResponse]:
        return await self._request(
            "PUT",
            "/decision/constraints",
            MutationResponse,
            json={"constraints": {"version": 1, "applicant": {"version": 1, "scores": scores}}, "expectedRevision": expected_revision},
            session_cookie=session_cookie,
        )

    async def record_analytics(self, payload: dict[str, Any], *, session_cookie: str | None = None) -> BackendResult[AnalyticsAccepted]:
        return await self._request("POST", "/decision/analytics", AnalyticsAccepted, json=payload, session_cookie=session_cookie)

    async def _request(
        self,
        method: str,
        path: str,
        model: type[ModelT],
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        session_cookie: str | None,
    ) -> BackendResult[ModelT]:
        headers = {"Accept": "application/json"}
        if session_cookie:
            headers["Cookie"] = f"andromeda_profile_session={session_cookie}"
        response: httpx.Response | None = None
        for attempt in range(1, self._retry_attempts + 1):
            try:
                if self._client is not None:
                    response = await self._client.request(method, f"{self._base_url}{path}", params=params, json=json, headers=headers, timeout=self._timeout)
                else:
                    async with httpx.AsyncClient(follow_redirects=True) as client:
                        response = await client.request(method, f"{self._base_url}{path}", params=params, json=json, headers=headers, timeout=self._timeout)
            except httpx.HTTPError as exc:
                if attempt == self._retry_attempts:
                    logger.warning("backend_request_failed path=%s error_type=%s", path, type(exc).__name__)
                    raise BackendTransportError() from exc
                await asyncio.sleep(self._retry_backoff_seconds * (2 ** (attempt - 1)))
                logger.warning("backend_request_retry path=%s attempt=%d reason=transport", path, attempt)
                continue
            if response.status_code not in {429, 502, 503, 504} or attempt == self._retry_attempts:
                break
            retry_after = _retry_after_seconds(response)
            await asyncio.sleep(retry_after if retry_after is not None else self._retry_backoff_seconds * (2 ** (attempt - 1)))
            logger.warning("backend_request_retry path=%s attempt=%d status=%d", path, attempt, response.status_code)
        assert response is not None
        if response.status_code >= 400:
            raise BackendError(response.status_code, _safe_error_message(response))
        try:
            parsed = model.model_validate(response.json())
        except (ValueError, TypeError) as exc:
            logger.error("backend_response_invalid path=%s error_type=%s", path, type(exc).__name__)
            raise BackendError(502, "backend returned an invalid response") from exc
        cookie = response.cookies.get("andromeda_profile_session")
        logger.debug("backend_request_complete method=%s path=%s status=%d", method, path, response.status_code)
        return BackendResult(parsed, cookie or session_cookie)


def _path_part(value: str) -> str:
    from urllib.parse import quote

    return quote(value, safe="")


def _safe_error_message(response: httpx.Response) -> str:
    if response.status_code == 401:
        return "backend authorization failed"
    if response.status_code == 404:
        return "requested backend resource was not found"
    if response.status_code == 409:
        return "backend state is stale"
    return f"backend request failed with status {response.status_code}"


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return min(max(parsed, 0.0), 5.0)


__all__ = ["BackendHttpClient", "BackendResult"]
