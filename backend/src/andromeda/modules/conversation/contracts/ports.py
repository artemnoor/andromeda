"""Owner-bound persistence port for generic query sessions."""

from __future__ import annotations

from typing import Protocol

from andromeda.modules.proftest.contracts.public import ProfileScope

from .public import QuerySession, QuerySessionId


class QuerySessionRepository(Protocol):
    def get(self, session_id: QuerySessionId, *, owner_scope: ProfileScope) -> QuerySession | None: ...

    def save(self, session: QuerySession, *, expected_revision: int | None = None) -> QuerySession: ...


__all__ = ["QuerySessionRepository"]
