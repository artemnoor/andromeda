"""Storage boundary consumed by the Admission Fit application service."""

from __future__ import annotations

from typing import Protocol

from andromeda.modules.admissions.contracts.public import ProgramAdmissions
from andromeda.modules.programs.contracts.public import Program
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import ProgramId


class AdmissionFitProgramData(ContractModel):
    """Validated public snapshot assembled by infrastructure composition."""

    program: Program
    admissions: ProgramAdmissions


class AdmissionFitDataReader(Protocol):
    """Read-only port; implementations may use any storage."""

    def read(self, program_id: ProgramId) -> AdmissionFitProgramData | None: ...


__all__ = ["AdmissionFitDataReader", "AdmissionFitProgramData"]
