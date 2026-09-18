"""Bounded TTL cache for identical render requests."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import time
from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class CacheEntry:
    value: bytes
    expires_at: float


class RenderCache:
    def __init__(self, *, max_items: int = 128, ttl_seconds: float = 300.0, clock: Callable[[], float] = time.monotonic) -> None:
        if max_items < 1 or ttl_seconds <= 0:
            raise ValueError("render cache bounds must be positive")
        self._max_items = max_items
        self._ttl = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> bytes | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at <= self._clock():
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return entry.value

    def put(self, key: str, value: bytes) -> None:
        self._entries[key] = CacheEntry(value=value, expires_at=self._clock() + self._ttl)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_items:
            self._entries.popitem(last=False)


__all__ = ["RenderCache"]
