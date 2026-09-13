"""Application service for loading canonical catalog data through one port."""

from __future__ import annotations

import logging

from andromeda.shared.contracts.errors import ContractError, ErrorCode

from ..contracts.public import ProgramFingerprint
from ..repository.ports import ProftestCatalogReader
from .fingerprint import FingerprintBuilder


logger = logging.getLogger("andromeda.proftest.catalog")


class ProftestCatalogService:
    def __init__(self, reader: ProftestCatalogReader, builder: FingerprintBuilder | None = None) -> None:
        self._reader = reader
        self._builder = builder or FingerprintBuilder()

    def list_fingerprints(self) -> tuple[ProgramFingerprint, ...]:
        programs = self._reader.list_programs()
        logger.info("catalog_refresh_start program_count=%d", len(programs))
        fingerprints: list[ProgramFingerprint] = []
        for program in programs:
            curriculum = self._reader.get_curriculum(program.id)
            if curriculum is None:
                logger.warning("catalog_curriculum_missing program_id=%s", _safe_id(program.id))
                continue
            disciplines = {}
            for item in curriculum.items:
                discipline = self._reader.get_discipline(item.discipline_id)
                if discipline is None:
                    logger.error("catalog_discipline_missing program_id=%s discipline_id=%s", _safe_id(program.id), _safe_id(item.discipline_id))
                    raise ContractError(ErrorCode.CONTRACT_ERROR, "Curriculum item discipline is missing")
                disciplines[item.discipline_id] = discipline
            fingerprints.append(self._builder.build(program, curriculum, disciplines))
        result = self._builder.add_distinctive_subjects(fingerprints)
        if len(result) < 2:
            logger.warning("catalog_distinctiveness_insufficient fingerprint_count=%d", len(result))
        logger.info("catalog_refresh_complete program_count=%d fingerprint_count=%d", len(programs), len(result))
        return tuple(sorted(result, key=lambda fingerprint: fingerprint.program_code))


def _safe_id(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ")[:128]


__all__ = ["ProftestCatalogService"]
