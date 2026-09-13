"""Load Andromeda programs/curricula and build an ephemeral fingerprint catalog."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import time
from typing import Literal, Protocol

from proftest_spike.api_client.contracts import CurriculumResponse, ProgramListResponse
from proftest_spike.api_client.errors import ApiClientError
from proftest_spike.program_fingerprints.builder import FingerprintBuilder
from proftest_spike.program_fingerprints.entities import ProgramFingerprint

logger = logging.getLogger("proftest_spike.catalog")


class AndromedaReader(Protocol):
    async def get_programs_contract(self) -> ProgramListResponse:
        ...

    async def get_curriculum(self, program_id: str) -> CurriculumResponse:
        ...


@dataclass(frozen=True, slots=True)
class CatalogSnapshot:
    fingerprints: tuple[ProgramFingerprint, ...]
    requested_program_count: int
    failed_program_count: int
    curriculum_item_count: int
    loaded_at: float

    @property
    def status(self) -> Literal["ready", "partial", "empty"]:
        if not self.fingerprints:
            return "empty"
        if self.failed_program_count:
            return "partial"
        return "ready"


class CatalogService:
    """Stateless-at-rest catalog loader with a bounded in-memory TTL cache."""

    def __init__(self, reader: AndromedaReader, *, ttl_seconds: float = 300.0, concurrency: int = 8) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if concurrency < 1:
            raise ValueError("concurrency must be positive")
        self._reader = reader
        self._ttl_seconds = ttl_seconds
        self._semaphore = asyncio.Semaphore(concurrency)
        self._refresh_lock = asyncio.Lock()
        self._snapshot: CatalogSnapshot | None = None
        self._builder = FingerprintBuilder()

    async def get_catalog(self, *, force_refresh: bool = False) -> CatalogSnapshot:
        now = time.monotonic()
        if not force_refresh and self._snapshot is not None and now - self._snapshot.loaded_at < self._ttl_seconds:
            logger.debug("catalog_cache_hit age_seconds=%.2f program_count=%d", now - self._snapshot.loaded_at, len(self._snapshot.fingerprints))
            return self._snapshot
        logger.debug("catalog_cache_miss force_refresh=%s", force_refresh)
        async with self._refresh_lock:
            now = time.monotonic()
            if not force_refresh and self._snapshot is not None and now - self._snapshot.loaded_at < self._ttl_seconds:
                logger.debug("catalog_cache_hit_after_lock program_count=%d", len(self._snapshot.fingerprints))
                return self._snapshot
            snapshot = await self._refresh()
            self._snapshot = snapshot
            return snapshot

    async def get_fingerprint(self, program_id: str) -> ProgramFingerprint | None:
        snapshot = await self.get_catalog()
        return next((item for item in snapshot.fingerprints if item.program_id == program_id), None)

    async def _refresh(self) -> CatalogSnapshot:
        logger.info("catalog_refresh_start")
        programs = await self._reader.get_programs_contract()
        requested_count = len(programs.items)
        if requested_count == 0:
            logger.warning("catalog_empty")
            return CatalogSnapshot((), 0, 0, 0, time.monotonic())

        results = await asyncio.gather(
            *(self._load_curriculum(program.id) for program in programs.items),
            return_exceptions=True,
        )
        curricula: list[CurriculumResponse] = []
        failed_count = 0
        for result in results:
            if isinstance(result, CurriculumResponse):
                curricula.append(result)
                continue
            failed_count += 1
            if isinstance(result, ApiClientError):
                logger.error("catalog_curriculum_failed failed_count=%d error_type=%s", failed_count, type(result).__name__)
            else:
                logger.error("catalog_curriculum_failed failed_count=%d error_type=%s", failed_count, type(result).__name__)

        if not curricula:
            logger.warning("catalog_no_curricula requested_program_count=%d", requested_count)
            return CatalogSnapshot((), requested_count, failed_count, 0, time.monotonic())
        fingerprints = self._builder.build_catalog(curricula)
        item_count = sum(len(curriculum.items) for curriculum in curricula)
        if failed_count:
            logger.warning(
                "catalog_partial requested_program_count=%d loaded_program_count=%d failed_program_count=%d",
                requested_count,
                len(fingerprints),
                failed_count,
            )
        logger.info(
            "catalog_refresh_complete program_count=%d curriculum_item_count=%d failed_program_count=%d",
            len(fingerprints),
            item_count,
            failed_count,
        )
        return CatalogSnapshot(tuple(fingerprints), requested_count, failed_count, item_count, time.monotonic())

    async def _load_curriculum(self, program_id: str) -> CurriculumResponse:
        async with self._semaphore:
            logger.debug("catalog_curriculum_start program_id=%s", _safe_id(program_id))
            return await self._reader.get_curriculum(program_id)


def _safe_id(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ")[:128]


__all__ = ["AndromedaReader", "CatalogService", "CatalogSnapshot"]
