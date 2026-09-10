from __future__ import annotations

import logging
from collections.abc import Mapping

from fastapi import Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ..contracts.errors import ContractError, ErrorCode, ErrorDetail, ErrorResponse, details_from_validation

logger = logging.getLogger("api.errors")


def _status(code: ErrorCode) -> int:
    return {ErrorCode.NOT_FOUND: 404, ErrorCode.VALIDATION_ERROR: 422, ErrorCode.SOURCE_CONTRACT_ERROR: 500, ErrorCode.CONTRACT_ERROR: 500, ErrorCode.INTERNAL_ERROR: 500}[code]


def _json(response: ErrorResponse) -> JSONResponse:
    return JSONResponse(status_code=_status(response.code), content=response.model_dump(mode="json"))


async def contract_error_handler(request: Request, exc: ContractError) -> JSONResponse:
    logger.warning("contract_error path=%s code=%s", request.url.path, exc.code.value)
    return _json(exc.response())


async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        ErrorDetail(path=".".join(str(part) for part in error.get("loc", ())), message=str(error.get("msg", "invalid value")), type=str(error.get("type", "value_error")))
        for error in exc.errors()
    ]
    logger.warning("request_validation_error path=%s detail_count=%d", request.url.path, len(details))
    return _json(ErrorResponse(code=ErrorCode.VALIDATION_ERROR, message="Request validation failed", details=details))


async def response_validation_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
    logger.error("response_validation_error path=%s detail_count=%d", request.url.path, len(exc.errors()))
    return _json(ErrorResponse(code=ErrorCode.CONTRACT_ERROR, message="Response contract validation failed", details=[ErrorDetail(path="response", message="response does not satisfy contract", type="response_validation")]))


async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("database_error path=%s", request.url.path)
    return _json(ErrorResponse(code=ErrorCode.INTERNAL_ERROR, message="Database operation failed"))


async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    logger.error("boundary_validation_error path=%s detail_count=%d", request.url.path, len(exc.errors()))
    return _json(
        ErrorResponse(
            code=ErrorCode.CONTRACT_ERROR,
            message="Boundary data does not satisfy the contract",
            details=details_from_validation(exc.errors()),
        )
    )
