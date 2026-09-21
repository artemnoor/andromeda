"""Ports implemented by backend adapters, never by transport clients."""

from __future__ import annotations

from typing import Protocol

from .public import EntityResolutionResult, ResolutionContext, ResolutionEntityType


class UniversityResolver(Protocol):
    def resolve(self, query: str, *, limit: int = 10) -> EntityResolutionResult: ...


class DirectionResolver(Protocol):
    def resolve(
        self,
        query: str,
        *,
        context: ResolutionContext | None = None,
        limit: int = 10,
    ) -> EntityResolutionResult: ...


class ProgramResolver(Protocol):
    def resolve(
        self,
        query: str,
        *,
        context: ResolutionContext | None = None,
        limit: int = 10,
    ) -> EntityResolutionResult: ...


class DisciplineResolver(Protocol):
    def resolve(self, query: str, *, limit: int = 10) -> EntityResolutionResult: ...


class MetricResolver(Protocol):
    def resolve(self, query: str, *, limit: int = 10) -> EntityResolutionResult: ...


class EntityResolverGateway(Protocol):
    """One transport-independent entry point for typed entity resolution."""

    def resolve(
        self,
        entity_type: ResolutionEntityType,
        query: str,
        *,
        context: ResolutionContext | None = None,
        limit: int = 10,
    ) -> EntityResolutionResult: ...


__all__ = [
    "DirectionResolver",
    "DisciplineResolver",
    "EntityResolverGateway",
    "MetricResolver",
    "ProgramResolver",
    "UniversityResolver",
]
