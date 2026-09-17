"""Canonical program/fingerprint adapter for decision orchestration."""

from __future__ import annotations

import logging

from andromeda.modules.decision.repository.ports import ProgramCandidateSnapshot, ProgramCandidateSource
from andromeda.modules.programs.repository.ports import ProgramReader
from andromeda.modules.proftest.contracts.public import ProgramFingerprint
from andromeda.modules.recommendations.contracts.public import ProgramFingerprintReader
from andromeda.shared.contracts.errors import ContractError, ErrorCode


logger = logging.getLogger("andromeda.infrastructure.repositories.decision_candidates")


class CatalogDecisionCandidateSource(ProgramCandidateSource):
    """Join canonical program rows with existing curriculum fingerprints.

    Programs without a curriculum fingerprint stay in the returned snapshot
    with ``fingerprint=None``.  That preserves the source gap for Decision
    without pretending that a missing curriculum is an ineligible program.
    """

    def __init__(self, programs: ProgramReader, fingerprints: ProgramFingerprintReader) -> None:
        self._programs = programs
        self._fingerprints = fingerprints

    def list_candidates(self) -> tuple[ProgramCandidateSnapshot, ...]:
        programs = tuple(sorted(self._programs.list(), key=lambda item: (item.code, item.id)))
        fingerprints = self._fingerprints.list_fingerprints()
        by_id: dict[str, ProgramFingerprint] = {}
        for fingerprint in fingerprints:
            if fingerprint.program_id in by_id:
                raise ContractError(ErrorCode.CONTRACT_ERROR, "Fingerprint source returned duplicate canonical program IDs")
            by_id[fingerprint.program_id] = fingerprint
        result = tuple(
            ProgramCandidateSnapshot(
                program=program,
                fingerprint=by_id.get(program.id),
            )
            for program in programs
        )
        logger.info(
            "decision_candidate_source_complete program_count=%d fingerprint_count=%d missing_fingerprint_count=%d",
            len(result),
            len(fingerprints),
            sum(item.fingerprint is None for item in result),
        )
        return result


__all__ = ["CatalogDecisionCandidateSource"]
