"""Short-lived opaque callback tokens for Telegram inline keyboards."""

from __future__ import annotations

from dataclasses import dataclass
import secrets
import time
from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class CallbackPayload:
    action: str
    program_ids: tuple[str, ...] = ()
    revision: int | None = None
    question_id: str | None = None
    option_id: str | None = None


@dataclass(frozen=True, slots=True)
class _StoredCallback:
    owner_key: str
    payload: CallbackPayload
    expires_at: float


class CallbackStore:
    def __init__(self, *, ttl_seconds: float = 900.0, max_items: int = 2048, clock: Callable[[], float] = time.monotonic) -> None:
        if ttl_seconds <= 0 or max_items < 1:
            raise ValueError("callback store bounds must be positive")
        self._ttl = ttl_seconds
        self._max_items = max_items
        self._clock = clock
        self._values: dict[str, _StoredCallback] = {}

    def issue(self, owner_key: str, payload: CallbackPayload) -> str:
        self._purge()
        token = secrets.token_urlsafe(18)
        self._values[token] = _StoredCallback(owner_key, payload, self._clock() + self._ttl)
        while len(self._values) > self._max_items:
            self._values.pop(next(iter(self._values)))
        return f"cb:{token}"

    def consume(self, owner_key: str, data: str) -> CallbackPayload | None:
        self._purge()
        token = data.removeprefix("cb:")
        stored = self._values.get(token)
        if stored is None or stored.owner_key != owner_key:
            return None
        self._values.pop(token, None)
        return stored.payload

    def _purge(self) -> None:
        now = self._clock()
        for token, stored in tuple(self._values.items()):
            if stored.expires_at <= now:
                self._values.pop(token, None)


__all__ = ["CallbackPayload", "CallbackStore"]
