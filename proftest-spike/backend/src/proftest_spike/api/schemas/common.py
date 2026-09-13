"""Shared public schemas for the Spike API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from proftest_spike.api_client.contracts import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
        strict=True,
    )


class HealthResponse(ApiModel):
    status: Literal["ok"]
    service: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=32)
    data_source: Literal["andromeda_http_api"]


class BootstrapResponse(ApiModel):
    status: Literal["ready"]
    service: str = Field(min_length=1, max_length=128)
    test_version: str = Field(min_length=1, max_length=32)
    catalog_status: Literal["not_loaded"]
    data_source: Literal["andromeda_http_api"]


class ErrorResponse(ApiModel):
    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=512)
    details: dict[str, str] | None = None


__all__ = ["ApiModel", "BootstrapResponse", "ErrorResponse", "HealthResponse"]
