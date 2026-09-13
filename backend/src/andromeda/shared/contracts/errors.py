from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from pydantic import Field

from .base import ContractModel


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    SOURCE_CONTRACT_ERROR = "SOURCE_CONTRACT_ERROR"
    CONTRACT_ERROR = "CONTRACT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(ContractModel):
    path: str = Field(min_length=1, max_length=256)
    message: str = Field(min_length=1, max_length=512)
    type: str = Field(min_length=1, max_length=128)


class ErrorResponse(ContractModel):
    code: ErrorCode
    message: str = Field(min_length=1, max_length=512)
    details: tuple[ErrorDetail, ...] = ()


class AndromedaError(Exception):
    """Base exception translated into the public API error contract."""

    def __init__(self, code: ErrorCode, message: str, details: Sequence[ErrorDetail] = ()) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = tuple(details)

    def response(self) -> ErrorResponse:
        return ErrorResponse(code=self.code, message=self.message, details=self.details)


class ContractError(AndromedaError):
    pass


class NotFoundError(AndromedaError):
    def __init__(self, message: str, details: Sequence[ErrorDetail] = ()) -> None:
        super().__init__(ErrorCode.NOT_FOUND, message, details)


class ConflictError(AndromedaError):
    def __init__(self, message: str, details: Sequence[ErrorDetail] = ()) -> None:
        super().__init__(ErrorCode.CONFLICT, message, details)


class ValidationError(AndromedaError):
    def __init__(self, message: str, details: Sequence[ErrorDetail] = ()) -> None:
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details)


def details_from_validation(errors: Sequence[Mapping[str, object]]) -> tuple[ErrorDetail, ...]:
    details: list[ErrorDetail] = []
    for error in errors:
        location = error.get("loc", ())
        path = ".".join(str(part) for part in location) if isinstance(location, (tuple, list)) else str(location)
        details.append(
            ErrorDetail(
                path=path or "contract",
                message=str(error.get("msg", "invalid value")),
                type=str(error.get("type", "value_error")),
            )
        )
    return tuple(details)
