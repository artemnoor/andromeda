from __future__ import annotations

import logging

from sqlalchemy import Engine

from andromeda.ingestion.contracts.normalized import CanonicalSnapshot
from andromeda.ingestion.contracts.raw import RawTracerBundle as CanonicalRawTracerBundle
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository

from ..contracts.domain import NormalizedTracerSnapshot
from ..contracts.raw import RawTracerBundle

logger = logging.getLogger("tracer.ingest")


class TracerIngestService:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def ingest(self, raw: RawTracerBundle, normalized: NormalizedTracerSnapshot) -> str:
        logger.debug("ingest_service_enter programs=%d", len(normalized.programs))
        try:
            canonical_raw = CanonicalRawTracerBundle.model_validate(raw.model_dump())
            canonical = CanonicalSnapshot.model_validate(normalized.model_dump())
            run_id = SqlAlchemyIngestionRepository(self.engine).ingest(canonical_raw, canonical)
            logger.debug("ingest_service_exit run_id=%s", run_id)
            return run_id
        except Exception:
            logger.exception("ingest_transaction_rollback")
            raise
