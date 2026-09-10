from __future__ import annotations

from typing import Protocol

from ....shared.contracts.ids import DisciplineId
from ..contracts.public import Discipline
from ..contracts.resolution import IdentityResolution


class DisciplineReader(Protocol):
    def get(self, discipline_id: DisciplineId) -> Discipline | None: ...

    def list(self) -> tuple[Discipline, ...]: ...


class DisciplineWriter(Protocol):
    def save(self, discipline: Discipline) -> None: ...


class DisciplineRepository(DisciplineReader, DisciplineWriter, Protocol):
    """Storage port for canonical disciplines."""


class DisciplineIdentityResolver(Protocol):
    """Identity-resolution port; ambiguity policy is owned by the service."""

    def resolve(self, source_name: str, candidates: tuple[Discipline, ...] = ()) -> IdentityResolution: ...


__all__ = ["DisciplineIdentityResolver", "DisciplineReader", "DisciplineRepository", "DisciplineWriter"]
