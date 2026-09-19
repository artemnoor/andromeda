from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse, Response

from andromeda.api.routes.compare import router as compare_router
from andromeda.api.routes.admission_fit import router as admission_fit_router
from andromeda.api.routes.admissions import router as admissions_router
from andromeda.api.routes.disciplines import router as disciplines_router
from andromeda.api.routes.programs import router as programs_router
from andromeda.api.routes.proftest import router as proftest_router
from andromeda.api.routes.recommendations import router as recommendations_router
from andromeda.api.routes.events import router as events_router
from andromeda.api.routes.campus import router as campus_router
from andromeda.api.routes.personal_route import router as personal_route_router
from andromeda.api.routes.admin_ops import router as admin_ops_router
from andromeda.api.routes.analytics_ops import router as analytics_ops_router
from andromeda.api.routes.auth import router as auth_router
from andromeda.api.routes.decision import router as decision_router
from andromeda.api.routes.health import expected_schema_revision, router as health_router
from andromeda.api.request_controls import SlidingWindowRateLimiter, enforce_rate_limit, enforce_trusted_origin, normalize_correlation_id
from andromeda.shared.contracts.errors import AndromedaError, ErrorCode, ErrorResponse, details_from_validation
from andromeda.composition import build_container
from andromeda.infrastructure.config.settings import Settings
from andromeda.infrastructure.database.base import create_engine_for_url


logger = logging.getLogger("andromeda.api.request")

SECURITY_HEADERS = {
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}
API_CONTENT_SECURITY_POLICY = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
DOCS_CONTENT_SECURITY_POLICY = "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'"
HSTS_HEADER = "max-age=31536000; includeSubDomains"


def _andromeda_error_response(request: Request, exc: AndromedaError, settings: Settings) -> JSONResponse:
    status = 429 if exc.code is ErrorCode.RATE_LIMITED else 401 if exc.code is ErrorCode.UNAUTHORIZED else 404 if exc.code is ErrorCode.NOT_FOUND else 409 if exc.code is ErrorCode.CONFLICT else 400 if exc.code in (ErrorCode.VALIDATION_ERROR, ErrorCode.CONTRACT_ERROR, ErrorCode.SOURCE_CONTRACT_ERROR) else 500
    if exc.code is ErrorCode.RATE_LIMITED:
        logger.warning("request_rate_limited path=%s correlation_id=%s", request.url.path, getattr(request.state, "correlation_id", "unknown"))
    headers = {"Retry-After": str(settings.rate_limit_window_seconds)} if status == 429 else None
    return JSONResponse(status_code=status, headers=headers, content=exc.response().model_dump(mode="json", by_alias=True))


def create_app(database_url: str | None = None) -> FastAPI:
    settings = Settings.from_environment(database_url)
    app = FastAPI(
        title="Andromeda Decision Support API",
        version="1.0.0",
        description="Strict source-backed contracts for discovering, comparing and choosing educational programmes across supported universities.",
        responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    app.state.settings = settings
    app.state.rate_limiter = SlidingWindowRateLimiter(settings.rate_limit_window_seconds)
    app.state.engine = create_engine_for_url(settings.database_url, **settings.engine_options)
    app.state.container = build_container(app.state.engine, settings)
    try:
        app.state.expected_schema_revision = expected_schema_revision()
    except RuntimeError:
        logger.exception("schema_head_discovery_failed")
        app.state.expected_schema_revision = None
    origins = tuple(filter(None, settings.frontend_origin.split(",")))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(origins),
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        started_at = perf_counter()
        correlation_id = normalize_correlation_id(request.headers.get("X-Correlation-Id"))
        request.state.correlation_id = correlation_id
        response: Response | None = None
        try:
            enforce_trusted_origin(request, settings)
            enforce_rate_limit(request, app.state.rate_limiter, settings)
            response = await call_next(request)
        except AndromedaError as exc:
            response = _andromeda_error_response(request, exc, settings)
        except Exception as exc:
            logger.error("unhandled_exception exception_type=%s correlation_id=%s", type(exc).__name__, correlation_id)
            response = JSONResponse(status_code=500, content=ErrorResponse(code=ErrorCode.INTERNAL_ERROR, message="Internal server error").model_dump(mode="json", by_alias=True))
        profile_cookie_header = getattr(request.state, "profile_cookie_header", None)
        if isinstance(profile_cookie_header, str) and profile_cookie_header not in response.headers.getlist("set-cookie"):
            response.headers.append("set-cookie", profile_cookie_header)
        response.headers["X-Correlation-Id"] = correlation_id
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        response.headers["Content-Security-Policy"] = DOCS_CONTENT_SECURITY_POLICY if response.headers.get("content-type", "").startswith("text/html") else API_CONTENT_SECURITY_POLICY
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = HSTS_HEADER
        logger.info(
            "request_complete method=%s path=%s status=%d duration_ms=%.2f correlation_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            (perf_counter() - started_at) * 1000,
            correlation_id,
        )
        return response

    @app.exception_handler(AndromedaError)
    async def andromeda_error_handler(request: Request, exc: AndromedaError) -> JSONResponse:
        return _andromeda_error_response(request, exc, settings)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        response = ErrorResponse(code=ErrorCode.VALIDATION_ERROR, message="Request validation failed", details=details_from_validation(exc.errors()))
        return JSONResponse(status_code=422, content=response.model_dump(mode="json", by_alias=True))

    @app.exception_handler(ResponseValidationError)
    async def response_validation_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
        logger.error("response_contract_violation exception_type=%s correlation_id=%s", type(exc).__name__, getattr(request.state, "correlation_id", "unknown"))
        response = ErrorResponse(code=ErrorCode.CONTRACT_ERROR, message="Response contract failed")
        return JSONResponse(status_code=500, content=response.model_dump(mode="json", by_alias=True))

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        response = ErrorResponse(code=ErrorCode.CONTRACT_ERROR, message="Contract validation failed", details=details_from_validation(exc.errors()))
        return JSONResponse(status_code=500, content=response.model_dump(mode="json", by_alias=True))

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error("database_error exception_type=%s correlation_id=%s", type(exc).__name__, getattr(request.state, "correlation_id", "unknown"))
        response = ErrorResponse(code=ErrorCode.INTERNAL_ERROR, message="Database operation failed")
        return JSONResponse(status_code=500, content=response.model_dump(mode="json", by_alias=True))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception exception_type=%s correlation_id=%s", type(exc).__name__, getattr(request.state, "correlation_id", "unknown"))
        response = ErrorResponse(code=ErrorCode.INTERNAL_ERROR, message="Internal server error")
        return JSONResponse(status_code=500, content=response.model_dump(mode="json", by_alias=True))

    app.include_router(programs_router)
    app.include_router(admissions_router)
    app.include_router(admission_fit_router)
    app.include_router(disciplines_router)
    app.include_router(compare_router)
    app.include_router(proftest_router)
    app.include_router(recommendations_router)
    app.include_router(events_router)
    app.include_router(campus_router)
    app.include_router(personal_route_router)
    app.include_router(admin_ops_router)
    app.include_router(analytics_ops_router)
    app.include_router(auth_router)
    app.include_router(decision_router)
    app.include_router(health_router)
    return app


app = create_app()
