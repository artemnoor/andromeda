"""Deterministic, cached entity resolvers shared by API and channels."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from andromeda.modules.analytics.domain.metric_registry import MetricRegistry
from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.programs.contracts.public import Program
from andromeda.modules.universities.contracts.public import Direction, University

from ..contracts.public import (
    CandidateMatchReason,
    EntityResolutionCandidate,
    EntityResolutionResult,
    ResolutionContext,
    ResolutionEntityType,
    ResolutionStatus,
)
from .normalization import (
    aliases_for,
    direction_university_id,
    normalize_text,
    program_university_id,
    tokens,
)


class CachedEntityCatalog:
    """TTL cache preventing a catalog SQL query on every conversational turn."""

    def __init__(self, reader: Any, *, ttl_seconds: float = 300.0, clock: Callable[[], float] = time.monotonic) -> None:
        if ttl_seconds <= 0:
            raise ValueError("catalog ttl must be positive")
        self._reader = reader
        self._ttl = ttl_seconds
        self._clock = clock
        self._loaded_at = 0.0
        self._universities: tuple[University, ...] | None = None
        self._directions: tuple[Direction, ...] | None = None
        self._programs: tuple[Program, ...] | None = None
        self._disciplines: tuple[Discipline, ...] | None = None

    def universities(self) -> tuple[University, ...]:
        self._refresh_if_needed()
        if self._universities is None:
            self._universities = tuple(self._reader.list_universities())
        return self._universities

    def directions(self) -> tuple[Direction, ...]:
        self._refresh_if_needed()
        if self._directions is None:
            self._directions = tuple(self._reader.list_directions())
        return self._directions

    def programs(self) -> tuple[Program, ...]:
        self._refresh_if_needed()
        if self._programs is None:
            self._programs = tuple(self._reader.list_programs())
        return self._programs

    def disciplines(self) -> tuple[Discipline, ...]:
        self._refresh_if_needed()
        if self._disciplines is None:
            self._disciplines = tuple(self._reader.list_disciplines())
        return self._disciplines

    def refresh(self) -> None:
        self._universities = tuple(self._reader.list_universities())
        self._directions = tuple(self._reader.list_directions())
        self._programs = tuple(self._reader.list_programs())
        self._disciplines = tuple(self._reader.list_disciplines())
        self._loaded_at = self._clock()

    def _refresh_if_needed(self) -> None:
        if self._loaded_at == 0.0 or self._clock() - self._loaded_at >= self._ttl:
            self.refresh()


@dataclass(frozen=True, slots=True)
class _Match:
    canonical_id: str
    label: str
    code: str | None
    reason: CandidateMatchReason
    score: Decimal
    university_id: str | None = None
    direction_id: str | None = None


class UniversityResolverService:
    def __init__(self, catalog: CachedEntityCatalog) -> None:
        self._catalog = catalog

    def resolve(self, query: str, *, limit: int = 10) -> EntityResolutionResult:
        matches = (
            _match_entity(
                query,
                entity_type=ResolutionEntityType.UNIVERSITY,
                canonical_id=item.id,
                label=item.name,
                code=None,
                aliases=aliases_for(entity_id=item.id, entity_name=item.name),
            )
            for item in self._catalog.universities()
        )
        return _result(ResolutionEntityType.UNIVERSITY, query, matches, limit)


class DirectionResolverService:
    def __init__(self, catalog: CachedEntityCatalog) -> None:
        self._catalog = catalog

    def resolve(self, query: str, *, context: ResolutionContext | None = None, limit: int = 10) -> EntityResolutionResult:
        items = self._catalog.directions()
        if context and context.university_id:
            items = tuple(item for item in items if item.university_id == context.university_id)
        matches = (
            _match_entity(
                query,
                entity_type=ResolutionEntityType.DIRECTION,
                canonical_id=item.id,
                label=item.name,
                code=item.code,
                aliases=aliases_for(entity_id=item.id, code=item.code, entity_name=item.name),
                university_id=item.university_id,
            )
            for item in items
        )
        return _result(ResolutionEntityType.DIRECTION, query, matches, limit)


class ProgramResolverService:
    def __init__(self, catalog: CachedEntityCatalog) -> None:
        self._catalog = catalog

    def resolve(self, query: str, *, context: ResolutionContext | None = None, limit: int = 10) -> EntityResolutionResult:
        items = self._catalog.programs()
        if context and context.direction_id:
            items = tuple(item for item in items if item.direction_id == context.direction_id)
        elif context and context.university_id:
            items = tuple(
                item for item in items if direction_university_id(item.direction_id) == context.university_id or program_university_id(item.id) == context.university_id
            )
        matches = (
            _match_entity(
                query,
                entity_type=ResolutionEntityType.PROGRAM,
                canonical_id=item.id,
                label=item.name,
                code=item.code,
                aliases=aliases_for(entity_id=item.id, code=item.code, entity_name=item.name),
                university_id=program_university_id(item.id) or direction_university_id(item.direction_id),
                direction_id=item.direction_id,
            )
            for item in items
        )
        return _result(ResolutionEntityType.PROGRAM, query, matches, limit)


class DisciplineResolverService:
    def __init__(self, catalog: CachedEntityCatalog) -> None:
        self._catalog = catalog

    def resolve(self, query: str, *, limit: int = 10) -> EntityResolutionResult:
        matches = (
            _match_entity(
                query,
                entity_type=ResolutionEntityType.DISCIPLINE,
                canonical_id=item.id,
                label=item.name,
                code=None,
                aliases=aliases_for(entity_id=item.id, entity_name=item.name),
            )
            for item in self._catalog.disciplines()
        )
        return _result(ResolutionEntityType.DISCIPLINE, query, matches, limit)


class MetricResolverService:
    def __init__(self, registry: MetricRegistry | None = None) -> None:
        self._registry = registry or MetricRegistry()

    def resolve(self, query: str, *, limit: int = 10) -> EntityResolutionResult:
        matches = (
            _match_entity(
                query,
                entity_type=ResolutionEntityType.METRIC,
                canonical_id=f"metric:{item.code}",
                label=item.name,
                code=item.code,
                aliases=aliases_for(entity_id=f"metric:{item.code}"),
            )
            for item in self._registry.all()
        )
        return _result(ResolutionEntityType.METRIC, query, matches, limit)


def _match_entity(
    query: str,
    *,
    entity_type: ResolutionEntityType,
    canonical_id: str,
    label: str,
    code: str | None,
    aliases: Iterable[str],
    university_id: str | None = None,
    direction_id: str | None = None,
) -> _Match | None:
    normalized_query = normalize_text(query)
    normalized_id = normalize_text(canonical_id)
    normalized_code = normalize_text(code) if code else None
    normalized_label = normalize_text(label)
    normalized_aliases = {normalize_text(alias) for alias in aliases}
    if normalized_query == normalized_id:
        reason, score = CandidateMatchReason.CANONICAL_ID, Decimal("1")
    elif normalized_code and normalized_query == normalized_code:
        reason, score = CandidateMatchReason.CODE, Decimal("1")
    elif normalized_query == normalized_label:
        reason, score = CandidateMatchReason.NAME, Decimal("0.95")
    elif normalized_query in normalized_aliases:
        reason, score = CandidateMatchReason.ALIAS, Decimal("0.90")
    else:
        query_tokens = tokens(normalized_query)
        candidate_tokens = tokens(f"{normalized_id} {normalized_code or ''} {normalized_label}")
        if not query_tokens or not query_tokens.issubset(candidate_tokens):
            return None
        reason, score = CandidateMatchReason.TOKEN_MATCH, Decimal("0.70")
    return _Match(canonical_id, label, code, reason, score, university_id, direction_id)


def _result(entity_type: ResolutionEntityType, query: str, matches: Iterable[_Match | None], limit: int) -> EntityResolutionResult:
    if limit < 1 or limit > 20:
        raise ValueError("resolution limit must be between 1 and 20")
    ranked = sorted((match for match in matches if match is not None), key=lambda item: (-item.score, item.canonical_id))
    candidates = tuple(
        EntityResolutionCandidate(
            entity_type=entity_type,
            canonical_id=item.canonical_id,
            label=item.label,
            match_reason=item.reason,
            score=item.score,
            confidence=item.score,
            university_id=item.university_id,
            direction_id=item.direction_id,
            code=item.code,
        )
        for item in ranked[:limit]
    )
    if not candidates:
        return EntityResolutionResult(entity_type=entity_type, query=query, status=ResolutionStatus.NOT_FOUND)
    plausible = tuple(candidate for candidate in candidates if candidate.score >= candidates[0].score - Decimal("0.05"))
    if len(plausible) > 1:
        return EntityResolutionResult(entity_type=entity_type, query=query, status=ResolutionStatus.AMBIGUOUS, candidates=candidates)
    status = ResolutionStatus.EXACT if candidates[0].match_reason is CandidateMatchReason.CANONICAL_ID else ResolutionStatus.RESOLVED
    return EntityResolutionResult(
        entity_type=entity_type,
        query=query,
        status=status,
        candidates=candidates,
        selected_id=candidates[0].canonical_id,
    )


__all__ = [
    "CachedEntityCatalog",
    "DisciplineResolverService",
    "DirectionResolverService",
    "MetricResolverService",
    "ProgramResolverService",
    "UniversityResolverService",
]
