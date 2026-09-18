"""Resolve human program references against the live backend catalog."""

from __future__ import annotations

from dataclasses import dataclass
import re
import time
from collections.abc import Callable

from ..clients.backend import BackendHttpClient
from ..clients.models import Program


@dataclass(frozen=True, slots=True)
class ResolveResult:
    query: str
    matches: tuple[Program, ...]
    exact: bool
    session_cookie: str | None = None

    @property
    def found(self) -> bool:
        return bool(self.matches)


class ProgramResolver:
    def __init__(self, backend: BackendHttpClient, *, ttl_seconds: float = 300.0, clock: Callable[[], float] = time.monotonic) -> None:
        if ttl_seconds <= 0:
            raise ValueError("catalog ttl must be positive")
        self._backend = backend
        self._ttl = ttl_seconds
        self._clock = clock
        self._catalog: tuple[Program, ...] = ()
        self._loaded_at = 0.0

    async def refresh(self, *, session_cookie: str | None = None) -> str | None:
        result = await self._backend.list_programs(session_cookie=session_cookie)
        self._catalog = tuple(result.value.items)
        self._loaded_at = self._clock()
        return result.session_cookie

    async def resolve(self, query: str, *, session_cookie: str | None = None, force_refresh: bool = False) -> ResolveResult:
        rotated_cookie: str | None = None
        if force_refresh or not self._catalog or self._clock() - self._loaded_at >= self._ttl:
            rotated_cookie = await self.refresh(session_cookie=session_cookie)
        normalized = normalize_program_query(query)
        if not normalized:
            return ResolveResult(query=query, matches=(), exact=False, session_cookie=rotated_cookie)

        exact_matches = tuple(item for item in self._catalog if normalized in {normalize_program_query(item.id), normalize_program_query(item.code), normalize_program_query(item.name)})
        if len(exact_matches) == 1:
            return ResolveResult(query=query, matches=exact_matches, exact=True, session_cookie=rotated_cookie)
        candidates = tuple(item for item in self._catalog if _tokens_match(normalized, normalize_program_query(item.name)) or _tokens_match(normalized, normalize_program_query(item.code)))
        return ResolveResult(query=query, matches=_stable(candidates), exact=False, session_cookie=rotated_cookie)

    async def resolve_many(self, query: str, *, session_cookie: str | None = None) -> tuple[ResolveResult, ...]:
        parts = split_program_references(query)
        results: list[ResolveResult] = []
        current_cookie = session_cookie
        for part in parts:
            result = await self.resolve(part, session_cookie=current_cookie)
            results.append(result)
            if result.session_cookie:
                current_cookie = result.session_cookie
        return tuple(results)


def split_program_references(value: str) -> tuple[str, ...]:
    cleaned = re.sub(r"^\s*(?:сравни|сопоставь|compare)\s+", "", value, flags=re.IGNORECASE)
    parts = tuple(part.strip() for part in re.split(r"\s+(?:и|vs|versus)\s+|[,;]\s*", cleaned, flags=re.IGNORECASE) if part.strip())
    return parts or (cleaned.strip(),)


def normalize_program_query(value: str) -> str:
    value = value.replace("ё", "е").replace("Ё", "Е").casefold()
    value = re.sub(r"[^\w:.-]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _tokens_match(query: str, candidate: str) -> bool:
    query_tokens = query.split()
    candidate_tokens = candidate.split()
    return bool(query_tokens) and all(token in candidate_tokens for token in query_tokens)


def _stable(values: tuple[Program, ...]) -> tuple[Program, ...]:
    return tuple(sorted(values, key=lambda item: (item.code, item.id)))


__all__ = ["ProgramResolver", "ResolveResult", "normalize_program_query", "split_program_references"]
