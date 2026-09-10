"""Typed failures at the Andromeda HTTP boundary."""

from __future__ import annotations


class ApiClientError(RuntimeError):
    """Base error that can be mapped to a safe Spike API response."""

    endpoint: str

    def __init__(self, message: str, *, endpoint: str) -> None:
        super().__init__(message)
        self.endpoint = endpoint


class ApiUnavailable(ApiClientError):
    """The upstream API did not respond or returned a transient failure."""


class ApiNotFound(ApiClientError):
    """The requested upstream resource does not exist."""


class ApiContractError(ApiClientError):
    """The upstream payload violated the strict read contract."""

    error_path: str | None

    def __init__(self, message: str, *, endpoint: str, error_path: str | None = None) -> None:
        super().__init__(message, endpoint=endpoint)
        self.error_path = error_path


__all__ = ["ApiClientError", "ApiContractError", "ApiNotFound", "ApiUnavailable"]
