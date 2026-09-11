"""Infrastructure adapter for the Admission Fit reader port."""

from __future__ import annotations

import logging

from andromeda.modules.admission_fit.repository.ports import AdmissionFitDataReader, AdmissionFitProgramData
from andromeda.modules.admissions.repository.ports import AdmissionReader
from andromeda.modules.programs.repository.ports import ProgramReader
from andromeda.shared.contracts.ids import ProgramId


logger = logging.getLogger("andromeda.infrastructure.repositories.admission_fit")


class SqlAlchemyAdmissionFitReader(AdmissionFitDataReader):
    """Compose existing public program/admissions readers without leaking ORM."""

    def __init__(self, programs: ProgramReader, admissions: AdmissionReader) -> None:
        self._programs = programs
        self._admissions = admissions

    def read(self, program_id: ProgramId) -> AdmissionFitProgramData | None:
        program = self._programs.get(program_id)
        if program is None:
            logger.warning("admission_fit_program_missing program_id=%s", program_id)
            return None
        admissions = self._admissions.get_for_program(program_id)
        logger.debug(
            "admission_fit_public_snapshot_read program_id=%s offerings=%d",
            program_id,
            len(admissions.offerings),
        )
        return AdmissionFitProgramData(program=program, admissions=admissions)


__all__ = ["SqlAlchemyAdmissionFitReader"]
