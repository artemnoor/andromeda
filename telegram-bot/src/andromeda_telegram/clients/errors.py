"""Safe, transport-level errors exposed to handlers."""

from __future__ import annotations


class BackendError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class BackendTransportError(BackendError):
    def __init__(self, message: str = "backend is unavailable") -> None:
        super().__init__(0, message)


class RenderError(RuntimeError):
    pass


__all__ = ["BackendError", "BackendTransportError", "RenderError"]
