"""FastAPI application factory for the standalone Spike."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from starlette.responses import JSONResponse, Response

from proftest_spike.api_client.errors import ApiClientError, ApiContractError, ApiNotFound, ApiUnavailable
from proftest_spike.composition.container import Container, build_container
from proftest_spike.composition.settings import Settings, configure_logging

from .routes.health import router as health_router
from .routes.catalog import router as catalog_router
from .routes.results import router as results_router
from .routes.test import router as test_router
from .schemas.common import ErrorResponse

logger = logging.getLogger("proftest_spike.api.request")


def create_app(container: Container | None = None) -> FastAPI:
    """Create a stateless app; the optional container makes API tests isolated."""

    settings = container.settings if container is not None else Settings.from_environment()
    configure_logging(settings.log_level)
    owned_container = container is None
    resolved_container = container or build_container(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("spike_startup data_source=andromeda_http_api")
        yield
        if owned_container:
            await app.state.container.close()
        logger.info("spike_shutdown")

    app = FastAPI(
        title="Andromeda Proftest Spike API",
        version="0.1.0",
        description="Stateless profile matching against real Andromeda curricula.",
        lifespan=lifespan,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    app.state.container = resolved_container
    app.state.settings = settings
    origins = tuple(filter(None, settings.spike_cors_origin.split(",")))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(origins),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        correlation_id = request.headers.get("X-Correlation-Id", uuid4().hex)
        request.state.correlation_id = correlation_id
        logger.debug("request_start method=%s path=%s", request.method, request.url.path)
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        logger.debug("request_complete method=%s path=%s status=%d", request.method, request.url.path, response.status_code)
        return response

    @app.exception_handler(ApiUnavailable)
    async def unavailable_handler(request: Request, exc: ApiUnavailable) -> JSONResponse:
        del request
        logger.warning("upstream_unavailable endpoint_template=%s", _endpoint_template(exc.endpoint))
        return _error_response(503, "upstream_unavailable", "Andromeda API is temporarily unavailable")

    @app.exception_handler(ApiNotFound)
    async def not_found_handler(request: Request, exc: ApiNotFound) -> JSONResponse:
        del request
        logger.info("upstream_not_found endpoint_template=%s", _endpoint_template(exc.endpoint))
        return _error_response(404, "not_found", "The requested Andromeda resource was not found")

    @app.exception_handler(ApiContractError)
    async def contract_handler(request: Request, exc: ApiContractError) -> JSONResponse:
        del request
        logger.error(
            "upstream_contract_error endpoint_template=%s error_path=%s",
            _endpoint_template(exc.endpoint),
            exc.error_path or "unknown",
        )
        return _error_response(502, "upstream_contract_error", "Andromeda API returned an incompatible contract")

    @app.exception_handler(ApiClientError)
    async def client_error_handler(request: Request, exc: ApiClientError) -> JSONResponse:
        del request
        logger.error("upstream_request_error endpoint_template=%s", _endpoint_template(exc.endpoint))
        return _error_response(502, "upstream_request_error", "Andromeda API request failed")

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        del request
        del exc
        return _error_response(422, "validation_error", "Request validation failed")

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        del request
        logger.exception("spike_contract_error", exc_info=exc)
        return _error_response(500, "contract_error", "Spike contract validation failed")

    app.include_router(health_router)
    app.include_router(catalog_router)
    app.include_router(test_router)
    app.include_router(results_router)
    return app


def _endpoint_template(endpoint: str) -> str:
    if endpoint == "/programs":
        return endpoint
    if endpoint == "/discipline-areas":
        return endpoint
    if endpoint.startswith("/programs/") and endpoint.endswith("/curriculum"):
        return "/programs/{id}/curriculum"
    return "/unknown"


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    payload = ErrorResponse(code=code, message=message)
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json", by_alias=True))


app = create_app()

__all__ = ["app", "create_app"]
