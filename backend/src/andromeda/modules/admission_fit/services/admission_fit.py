"""Application service for the Admission Fit vertical slice."""

from __future__ import annotations

import logging

from andromeda.shared.contracts.errors import ContractError, ErrorCode, NotFoundError
from andromeda.shared.contracts.ids import ProgramId

from ..contracts.public import AdmissionFitRequest, AdmissionFitResult
from ..repository.ports import AdmissionFitDataReader
from .scoring import AdmissionFitScoringService


logger = logging.getLogger("andromeda.admission_fit")


class AdmissionFitService:
    """Coordinate public program/admissions readers and the pure scorer."""

    def __init__(
        self,
        reader: AdmissionFitDataReader,
        scorer: AdmissionFitScoringService | None = None,
    ) -> None:
        self._reader = reader
        self._scorer = scorer or AdmissionFitScoringService()

    def evaluate(self, program_id: ProgramId, request: AdmissionFitRequest) -> AdmissionFitResult:
        logger.debug(
            "admission_fit_evaluation_started program_id=%s offering_id=%s subject_count=%d",
            program_id,
            request.offering_id,
            len(request.applicant.scores),
        )
        try:
            snapshot = self._reader.read(program_id)
        except Exception:
            logger.exception("admission_fit_reader_failed program_id=%s", program_id)
            raise
        if snapshot is None:
            raise NotFoundError(f"Program not found: {program_id}")
        if snapshot.program.id != program_id or snapshot.admissions.program_id != program_id:
            logger.error("admission_fit_reader_contract_mismatch program_id=%s", program_id)
            raise ContractError(ErrorCode.CONTRACT_ERROR, "Admission Fit reader returned an incompatible program contract")
        offering = next((item for item in snapshot.admissions.offerings if item.id == request.offering_id), None)
        if offering is None:
            raise NotFoundError(f"Admission offering not found: {request.offering_id}")
        result = self._scorer.score(program_id, offering, request.applicant)
        logger.debug(
            "admission_fit_evaluation_finished program_id=%s offering_id=%s data_quality=%s",
            program_id,
            request.offering_id,
            result.data_quality.value,
        )
        return result


__all__ = ["AdmissionFitService"]
