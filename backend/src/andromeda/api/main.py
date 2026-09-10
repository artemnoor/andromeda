from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse, Response

from andromeda.api.routes.compare import router as compare_router
from andromeda.api.routes.disciplines import router as disciplines_router
from andromeda.api.routes.programs import router as programs_router
from andromeda.api.routes.proftest import router as proftest_router
from andromeda.shared.contracts.errors import AndromedaError, ErrorCode, ErrorResponse, details_from_validation
from andromeda.infrastructure.config.settings import Settings
from andromeda.infrastructure.database.base import create_engine_for_url


logger = logging.getLogger("andromeda.api.request")


def create_app(database_url: str | None = None) -> FastAPI:
    settings = Settings.from_environment()
    app = FastAPI(
        title="Andromeda Educational Program Comparison API",
        version="1.0.0",
        description="Strict source-backed contracts for comparing BMSTU educational programmes.",
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    app.state.engine = create_engine_for_url(database_url or settings.database_url)
    origins = tuple(filter(None, settings.frontend_origin.split(",")))
    app.add_middleware(CORSMiddleware, allow_origins=list(origins), allow_methods=["GET", "POST"], allow_headers=["*"])

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        correlation_id = request.headers.get("X-Correlation-Id", uuid4().hex)
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        return response

    @app.exception_handler(AndromedaError)
    async def andromeda_error_handler(request: Request, exc: AndromedaError) -> JSONResponse:
        del request
        status = 404 if exc.code is ErrorCode.NOT_FOUND else 400 if exc.code in (ErrorCode.VALIDATION_ERROR, ErrorCode.CONTRACT_ERROR, ErrorCode.SOURCE_CONTRACT_ERROR) else 500
        return JSONResponse(status_code=status, content=exc.response().model_dump(mode="json", by_alias=True))

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        del request
        response = ErrorResponse(code=ErrorCode.VALIDATION_ERROR, message="Request validation failed", details=details_from_validation(exc.errors()))
        return JSONResponse(status_code=422, content=response.model_dump(mode="json", by_alias=True))

    @app.exception_handler(ResponseValidationError)
    async def response_validation_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
        del request
        logger.exception("response_contract_violation", exc_info=exc)
        response = ErrorResponse(code=ErrorCode.CONTRACT_ERROR, message="Response contract failed")
        return JSONResponse(status_code=500, content=response.model_dump(mode="json", by_alias=True))

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        del request
        response = ErrorResponse(code=ErrorCode.CONTRACT_ERROR, message="Contract validation failed", details=details_from_validation(exc.errors()))
        return JSONResponse(status_code=500, content=response.model_dump(mode="json", by_alias=True))

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        del request
        logger.exception("database_error", exc_info=exc)
        response = ErrorResponse(code=ErrorCode.INTERNAL_ERROR, message="Database operation failed")
        return JSONResponse(status_code=500, content=response.model_dump(mode="json", by_alias=True))

    app.include_router(programs_router)
    app.include_router(disciplines_router)
    app.include_router(compare_router)
    app.include_router(proftest_router)
    return app


app = create_app()
