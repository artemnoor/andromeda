from __future__ import annotations

import logging

from sqlalchemy import Engine

from ..contracts.domain import NormalizedTracerSnapshot
from ..contracts.raw import RawTracerBundle
from ..db.repositories import ingest_snapshot
from ..db.session import session_scope

logger = logging.getLogger("tracer.ingest")


class TracerIngestService:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def ingest(self, raw: RawTracerBundle, normalized: NormalizedTracerSnapshot) -> str:
        logger.debug("ingest_service_enter programs=%d", len(normalized.programs))
        try:
            with session_scope(self.engine) as session:
                with session.begin():
                    run_id = ingest_snapshot(session, raw, normalized)
            logger.debug("ingest_service_exit run_id=%s", run_id)
            return run_id
        except Exception:
            logger.exception("ingest_transaction_rollback")
            raise
