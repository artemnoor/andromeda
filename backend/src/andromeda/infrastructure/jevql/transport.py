"""Provider-neutral jevQL transport implementations."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
import subprocess
from typing import Protocol, cast

from andromeda.modules.analytics.contracts.semantic_predicate import SemanticPredicateRequest

from .config import JevQLConfig


class JevQLTransportError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class JevQLTransport(Protocol):
    def available(self) -> bool: ...

    def evaluate(self, request: SemanticPredicateRequest) -> object: ...


class EmbeddedClient(Protocol):
    def evaluate(self, request: SemanticPredicateRequest) -> object: ...


class EmbeddedTransport:
    """Lazy official SDK adapter; the SDK is imported only on first use."""

    def __init__(self, client_factory: Callable[[], EmbeddedClient] | None = None) -> None:
        self._client_factory = client_factory or _official_embedded_client
        self._client: EmbeddedClient | None = None
        self._capability_error: str | None = None

    def available(self) -> bool:
        if self._client is not None:
            return True
        try:
            self._client = self._client_factory()
        except Exception as exc:
            self._capability_error = type(exc).__name__
            return False
        return True

    def evaluate(self, request: SemanticPredicateRequest) -> object:
        if not self.available() or self._client is None:
            raise JevQLTransportError("capability_unavailable", self._capability_error or "embedded SDK unavailable")
        return self._client.evaluate(request)


class PrivateProcessTransport:
    """Bounded JSON process protocol; command is configured, never user-selected."""

    def __init__(self, command: tuple[str, ...], *, timeout_seconds: float) -> None:
        self._command = command
        self._timeout_seconds = timeout_seconds

    def available(self) -> bool:
        return bool(self._command)

    def evaluate(self, request: SemanticPredicateRequest) -> object:
        if not self._command:
            raise JevQLTransportError("capability_unavailable", "private process command is not configured")
        try:
            completed = subprocess.run(
                self._command,
                input=request.model_dump_json(),
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise JevQLTransportError("transport", "private process timed out") from exc
        if completed.returncode != 0:
            raise JevQLTransportError("internal", "private process returned a failure")
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise JevQLTransportError("internal", "private process returned malformed JSON") from exc


class SharedServiceTransport:
    def __init__(
        self,
        config: JevQLConfig,
        *,
        requester: Callable[[SemanticPredicateRequest], object] | None = None,
    ) -> None:
        if config.shared_endpoint is None:
            raise ValueError("shared jevQL endpoint is not configured")
        self._config = config
        self._requester = requester

    def available(self) -> bool:
        return self._requester is not None or self._config.shared_endpoint is not None

    def evaluate(self, request: SemanticPredicateRequest) -> object:
        if self._requester is not None:
            return self._requester(request)
        try:
            import httpx

            headers = {}
            if self._config.shared_bearer_token:
                headers["Authorization"] = f"Bearer {self._config.shared_bearer_token}"
            response = httpx.post(
                self._config.shared_endpoint or "",
                json=request.model_dump(mode="json"),
                headers=headers,
                timeout=self._config.timeout_seconds,
            )
            if response.status_code in {401, 403}:
                raise JevQLTransportError("auth", "shared jevQL authorization failed")
            if response.status_code == 429:
                raise JevQLTransportError("api", "shared jevQL rate limit")
            response.raise_for_status()
            return response.json()
        except JevQLTransportError:
            raise
        except Exception as exc:
            raise JevQLTransportError("transport", "shared jevQL request failed") from exc


def _official_embedded_client() -> EmbeddedClient:
    try:
        import importlib

        module = importlib.import_module("jevql")
        factory = getattr(module, "EmbeddedClient", None)
        if not callable(factory):
            raise ImportError("jevQL SDK does not expose EmbeddedClient")
        return cast(EmbeddedClient, factory())
    except Exception as exc:
        raise RuntimeError("official jevQL Python SDK embedded engine is unavailable") from exc


__all__ = [
    "EmbeddedTransport",
    "JevQLTransport",
    "JevQLTransportError",
    "PrivateProcessTransport",
    "SharedServiceTransport",
]
