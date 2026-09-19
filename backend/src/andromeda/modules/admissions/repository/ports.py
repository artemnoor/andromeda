"""Storage ports exposed by the admissions module."""

from __future__ import annotations

from typing import Protocol

from andromeda.shared.contracts.ids import ProgramId

from ..contracts.public import ProgramAdmissions


class AdmissionReader(Protocol):
    def get_for_program(self, program_id: ProgramId) -> ProgramAdmissions: ...


class BatchAdmissionReader(AdmissionReader, Protocol):
    """Optimized read boundary for candidate projections."""

    def get_for_programs(self, program_ids: tuple[ProgramId, ...]) -> tuple[ProgramAdmissions, ...]: ...


class AdmissionWriter(Protocol):
    def save(self, admissions: ProgramAdmissions) -> None: ...


class AdmissionRepository(AdmissionReader, AdmissionWriter, Protocol):
    """Combined port used only by composition and ingestion infrastructure."""


__all__ = ["AdmissionReader", "AdmissionRepository", "AdmissionWriter", "BatchAdmissionReader"]
