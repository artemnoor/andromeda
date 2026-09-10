"""Ports consumed by proftest application services."""

from __future__ import annotations

from typing import Protocol

from andromeda.modules.curricula.contracts.public import Curriculum
from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.programs.contracts.public import Program
from andromeda.shared.contracts.ids import DisciplineId, ProgramId


class ProftestCatalogReader(Protocol):
    """Read canonical content without exposing storage or transport details."""

    def list_programs(self) -> tuple[Program, ...]: ...

    def get_curriculum(self, program_id: ProgramId) -> Curriculum | None: ...

    def get_discipline(self, discipline_id: DisciplineId) -> Discipline | None: ...


__all__ = ["ProftestCatalogReader"]
