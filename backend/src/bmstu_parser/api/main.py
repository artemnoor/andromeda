from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import Response

from ..contracts.errors import ContractError, ErrorResponse
from ..db.base import create_engine_for_url
from .error_handlers import contract_error_handler, database_error_handler, pydantic_validation_handler, request_validation_handler, response_validation_handler
from .routes.programs import router as programs_router
from .routes.compare import router as compare_router

logger = logging.getLogger("api.request")


def create_app(database_url: str | None = None) -> FastAPI:
    url = database_url or os.environ.get("BMSTU_DATABASE_URL", "sqlite:///./data/tracer.db")
    app = FastAPI(
        title="BMSTU Contract-First Tracer Bullet API",
        version="0.1.0",
        description="Source-backed program and curriculum contracts for the BMSTU tracer bullet.",
        responses={422: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    app.state.engine = create_engine_for_url(url)
    origins = tuple(filter(None, os.environ.get("VITE_FRONTEND_ORIGIN", "http://localhost:5173").split(",")))
    app.add_middleware(CORSMiddleware, allow_origins=list(origins), allow_methods=["GET"], allow_headers=["*"])

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        correlation_id = request.headers.get("X-Correlation-Id", uuid4().hex)
        request.state.correlation_id = correlation_id
        logger.debug("request_start method=%s route=%s correlation_id=%s", request.method, request.url.path, correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        logger.debug("request_end method=%s route=%s status=%d correlation_id=%s", request.method, request.url.path, response.status_code, correlation_id)
        return response

    app.add_exception_handler(ContractError, contract_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, request_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ResponseValidationError, response_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(SQLAlchemyError, database_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, pydantic_validation_handler)  # type: ignore[arg-type]
    app.include_router(programs_router)
    app.include_router(compare_router)
    return app


app = create_app()
