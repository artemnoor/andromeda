"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from proftest_spike import __version__

from ..schemas.common import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="andromeda-proftest-spike",
        version=__version__,
        data_source="andromeda_http_api",
    )


__all__ = ["router"]
