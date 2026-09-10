"""Async HTTP client for the current Andromeda read contracts."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from .contracts import (
    CurriculumResponse,
    DisciplineAreaCatalogResponse,
    ProgramListResponse,
)
from .errors import ApiClientError, ApiContractError, ApiNotFound, ApiUnavailable

logger = logging.getLogger("proftest_spike.api_client")

ModelT = TypeVar("ModelT", bound=BaseModel)


class AndromedaApiClient:
    """Read-only, bounded client for the public Andromeda API."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 15.0,
        max_programs: int = 500,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("Andromeda API base URL must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_programs < 1:
            raise ValueError("max_programs must be positive")
        self._base_url = base_url.rstrip("/")
        self._max_programs = max_programs
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
            headers={"Accept": "application/json"},
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""

        logger.debug("http_client_close")
        await self._http.aclose()

    async def get_programs(self) -> tuple[Mapping[str, object], ...]:
        """Fetch the bounded program catalog for fingerprint construction."""

        payload = await self._get("/programs", ProgramListResponse)
        items = payload.items
        if len(items) > self._max_programs:
            logger.warning(
                "program_catalog_truncated received_count=%d max_programs=%d",
                len(items),
                self._max_programs,
            )
            items = items[: self._max_programs]
        logger.info("program_catalog_received program_count=%d", len(items))
        return tuple(item.model_dump(mode="python", by_alias=False) for item in items)

    async def get_programs_contract(self) -> ProgramListResponse:
        """Fetch the typed program list for callers that need full DTOs."""

        payload = await self._get("/programs", ProgramListResponse)
        logger.info("program_catalog_received program_count=%d", len(payload.items))
        return payload

    async def get_curriculum(self, program_id: str) -> CurriculumResponse:
        """Fetch one program curriculum by its public id."""

        if not program_id.strip():
            raise ValueError("program_id must not be empty")
        endpoint = f"/programs/{quote(program_id, safe='')}/curriculum"
        payload = await self._get(endpoint, CurriculumResponse)
        logger.info(
            "curriculum_received program_id=%s item_count=%d",
            _safe_identifier(program_id),
            len(payload.items),
        )
        return payload

    async def get_discipline_areas(self) -> DisciplineAreaCatalogResponse:
        """Fetch the optional public area catalog."""

        return await self._get("/discipline-areas", DisciplineAreaCatalogResponse)

    async def _get(self, endpoint: str, model_type: type[ModelT]) -> ModelT:
        logger.debug("http_request_start method=GET endpoint=%s", _endpoint_template(endpoint))
        started = time.perf_counter()
        try:
            response = await self._http.get(endpoint)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError) as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            logger.error(
                "http_request_unavailable endpoint=%s duration_ms=%s error_type=%s",
                _endpoint_template(endpoint),
                duration_ms,
                type(exc).__name__,
            )
            raise ApiUnavailable("Andromeda API is unavailable", endpoint=endpoint) from exc
        except httpx.HTTPError as exc:
            logger.error("http_request_error endpoint=%s error_type=%s", _endpoint_template(endpoint), type(exc).__name__)
            raise ApiUnavailable("Andromeda API request failed", endpoint=endpoint) from exc

        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        logger.debug(
            "http_request_complete method=GET endpoint=%s status=%d duration_ms=%s",
            _endpoint_template(endpoint),
            response.status_code,
            duration_ms,
        )
        if response.status_code == 404:
            logger.warning("http_request_not_found endpoint=%s", _endpoint_template(endpoint))
            raise ApiNotFound("Andromeda resource was not found", endpoint=endpoint)
        if response.status_code >= 500:
            logger.warning("http_request_retryable_failure endpoint=%s status=%d", _endpoint_template(endpoint), response.status_code)
            raise ApiUnavailable("Andromeda API returned a transient error", endpoint=endpoint)
        if response.status_code >= 400:
            logger.error("http_request_rejected endpoint=%s status=%d", _endpoint_template(endpoint), response.status_code)
            raise ApiClientError("Andromeda API rejected the request", endpoint=endpoint)
        if response.status_code != 200:
            logger.error("http_request_unexpected_status endpoint=%s status=%d", _endpoint_template(endpoint), response.status_code)
            raise ApiContractError("Unexpected Andromeda response status", endpoint=endpoint)

        try:
            payload = model_type.model_validate_json(response.content)
        except ValidationError as exc:
            error_path = _validation_path(exc)
            logger.error(
                "http_contract_invalid endpoint=%s error_path=%s",
                _endpoint_template(endpoint),
                error_path or "unknown",
            )
            raise ApiContractError(
                "Andromeda response violated the read contract",
                endpoint=endpoint,
                error_path=error_path,
            ) from exc
        logger.debug("http_contract_valid endpoint=%s", _endpoint_template(endpoint))
        return payload


def _endpoint_template(endpoint: str) -> str:
    if endpoint == "/programs":
        return endpoint
    if endpoint == "/discipline-areas":
        return endpoint
    if endpoint.startswith("/programs/") and endpoint.endswith("/curriculum"):
        return "/programs/{id}/curriculum"
    return "/unknown"


def _safe_identifier(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ")[:128]


def _validation_path(exc: ValidationError) -> str | None:
    errors = exc.errors()
    if not errors:
        return None
    location = errors[0].get("loc", ())
    return ".".join(str(part) for part in location)[:256] or None


__all__ = ["AndromedaApiClient"]
