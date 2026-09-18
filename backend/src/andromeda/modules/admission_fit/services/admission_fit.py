"""Application service for the Admission Fit vertical slice."""

from __future__ import annotations

import logging

from andromeda.shared.contracts.errors import ContractError, ErrorCode, NotFoundError
from andromeda.shared.contracts.ids import ProgramId, canonical_program_id

from ..contracts.public import (
    AdmissionFitReason,
    AdmissionFitReasonKind,
    AdmissionFitRequest,
    AdmissionFitResult,
    AdmissionFitStatus,
    BatchAdmissionFitOutcome,
    BatchAdmissionFitRequest,
    BatchAdmissionFitResult,
)
from ...admissions.contracts.public import AdmissionOffering
from ..repository.ports import AdmissionFitDataReader, AdmissionFitProgramData
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
        resolved_program_id = canonical_program_id(program_id)
        logger.debug(
            "admission_fit_evaluation_started program_id=%s offering_id=%s subject_count=%d",
            program_id,
            request.offering_id,
            len(request.applicant.scores),
        )
        try:
            snapshot = self._reader.read(resolved_program_id)
            if snapshot is None and resolved_program_id != program_id:
                # One-cycle compatibility for in-memory/legacy consumers. The
                # canonical repositories write only university-scoped IDs.
                snapshot = self._reader.read(program_id)
        except Exception:
            logger.exception("admission_fit_reader_failed program_id=%s", program_id)
            raise
        if snapshot is None:
            raise NotFoundError(f"Program not found: {program_id}")
        if snapshot.program.id not in {resolved_program_id, program_id} or snapshot.admissions.program_id not in {resolved_program_id, program_id}:
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

    def evaluate_batch(self, request: BatchAdmissionFitRequest) -> BatchAdmissionFitResult:
        """Evaluate each candidate independently, preserving source gaps."""

        logger.debug(
            "admission_fit_batch_started candidate_count=%d admission_year=%s study_form=%s funding_type=%s",
            len(request.program_ids),
            request.admission_year,
            request.study_form.value if request.study_form is not None else "unknown",
            request.funding_type.value if request.funding_type is not None else "unknown",
        )
        outcomes: dict[ProgramId, BatchAdmissionFitOutcome] = {}
        for program_id in request.program_ids:
            resolved_program_id = canonical_program_id(program_id)
            snapshot = self._read_snapshot(resolved_program_id, legacy_program_id=program_id)
            if snapshot is None:
                outcomes[program_id] = _missing_outcome(program_id, "Для программы нет source-backed данных поступления")
                continue
            public_program_id = program_id
            offering, gap = _select_offering(snapshot.admissions.offerings, request)
            if offering is None:
                outcomes[public_program_id] = _missing_outcome(public_program_id, gap)
                continue
            result = self._scorer.score(public_program_id, offering, request.applicant)
            outcomes[public_program_id] = BatchAdmissionFitOutcome(
                program_id=public_program_id,
                status=result.status,
                result=result,
                data_gaps=result.data_gaps,
            )
        response = BatchAdmissionFitResult(by_program_id=outcomes)
        logger.info(
            "admission_fit_batch_complete candidate_count=%d result_count=%d insufficient_count=%d",
            len(request.program_ids),
            len(response.by_program_id),
            sum(item.status is AdmissionFitStatus.INSUFFICIENT_DATA for item in response.by_program_id.values()),
        )
        return response

    def _read_snapshot(self, program_id: ProgramId, *, legacy_program_id: ProgramId | None = None) -> AdmissionFitProgramData | None:
        try:
            snapshot = self._reader.read(program_id)
        except Exception:
            logger.exception("admission_fit_batch_reader_failed program_id=%s", program_id)
            raise
        if snapshot is None and legacy_program_id is not None and legacy_program_id != program_id:
            snapshot = self._reader.read(legacy_program_id)
        accepted_ids = {program_id, legacy_program_id} - {None}
        if snapshot is not None and (snapshot.program.id not in accepted_ids or snapshot.admissions.program_id not in accepted_ids):
            logger.error("admission_fit_batch_reader_contract_mismatch program_id=%s", program_id)
            raise ContractError(ErrorCode.CONTRACT_ERROR, "Admission Fit reader returned an incompatible program contract")
        return snapshot


def _select_offering(
    offerings: tuple[AdmissionOffering, ...],
    request: BatchAdmissionFitRequest,
) -> tuple[AdmissionOffering | None, str]:
    matching = tuple(
        offering
        for offering in offerings
        if (request.admission_year is None or offering.admission_year == request.admission_year)
        and (request.study_form is None or offering.study_form is request.study_form)
        and (request.funding_type is None or offering.funding_type is request.funding_type)
    )
    if len(matching) == 1:
        return matching[0], ""
    if not matching:
        return None, "Для заданных года, формы или типа финансирования нет опубликованного набора"
    return None, "Для заданных ограничений опубликовано несколько наборов; offering нельзя выбрать однозначно"


def _missing_outcome(program_id: ProgramId, message: str) -> BatchAdmissionFitOutcome:
    return BatchAdmissionFitOutcome(
        program_id=program_id,
        status=AdmissionFitStatus.INSUFFICIENT_DATA,
        data_gaps=(AdmissionFitReason(kind=AdmissionFitReasonKind.DATA_GAP, message=message),),
    )


__all__ = ["AdmissionFitService"]
