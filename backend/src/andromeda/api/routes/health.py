"""Process and database readiness probes for deploys and orchestrators."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text


router = APIRouter(tags=["health"])


@router.get("/health/live", include_in_schema=True)
def live() -> dict[str, str]:
    return {"status": "live"}


@router.get("/health/ready", include_in_schema=True, response_model=None)
def ready(request: Request) -> JSONResponse | dict[str, str]:
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            revision = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()
        if not revision:
            raise RuntimeError("schema revision is missing")
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready", "schema": str(revision)}


__all__ = ["router"]
