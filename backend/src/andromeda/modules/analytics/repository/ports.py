"""Repository ports for materialized analytical projections."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from andromeda.shared.contracts.ids import ProgramId

from ..contracts.public import ProgramProjection, ProjectionBuild


class ProgramProjectionStore(Protocol):
    def save(self, builds: Iterable[ProjectionBuild]) -> None: ...


class ProgramProjectionReader(Protocol):
    def get(self, program_id: ProgramId) -> ProgramProjection | None: ...

    def list(self, *, program_ids: tuple[ProgramId, ...] = ()) -> tuple[ProgramProjection, ...]: ...


__all__ = ["ProgramProjectionReader", "ProgramProjectionStore"]
