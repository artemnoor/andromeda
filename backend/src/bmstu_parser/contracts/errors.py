from __future__ import annotations

from enum import StrEnum
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import ErrorDetails


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    SOURCE_CONTRACT_ERROR = "SOURCE_CONTRACT_ERROR"
    CONTRACT_ERROR = "CONTRACT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    path: str = Field(min_length=1, max_length=256)
    message: str = Field(min_length=1, max_length=512)
    type: str = Field(min_length=1, max_length=128)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: ErrorCode
    message: str = Field(min_length=1, max_length=512)
    details: list[ErrorDetail] = Field(default_factory=list)


class ContractError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: Sequence[ErrorDetail] = ()) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = list(details)

    def response(self) -> ErrorResponse:
        return ErrorResponse(code=self.code, message=self.message, details=self.details)


def details_from_validation(errors: Sequence[ErrorDetails]) -> list[ErrorDetail]:
    return [
        ErrorDetail(
            path=".".join(str(part) for part in error.get("loc", ())) or "value",
            message=str(error.get("msg", "invalid value")),
            type=str(error.get("type", "value_error")),
        )
        for error in errors
    ]
