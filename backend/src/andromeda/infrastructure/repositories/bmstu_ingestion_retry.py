from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter
from andromeda.modules.admin_ops.contracts.public import IngestionRetryRequest, IngestionRetrySource
from andromeda.modules.admin_ops.contracts.results import IngestionRetryOutcome
from andromeda.shared.contracts.errors import ContractError, ErrorCode

from .ingestion import SqlAlchemyIngestionRepository


logger = logging.getLogger("andromeda.infrastructure.repositories.bmstu_ingestion_retry")


class SqlAlchemyBmstuIngestionRetryExecutor:
    """Runs the repository-owned BMSTU catalog discovery ingestion."""

    def __init__(self, engine: Any, environment: str) -> None:
        self._engine = engine
        self._environment = environment

    def execute(self, request: IngestionRetryRequest) -> IngestionRetryOutcome:
        if request.source is IngestionRetrySource.BMSTU_LIVE and self._environment != "staging":
            raise ContractError(ErrorCode.CONTRACT_ERROR, "Live ingestion is available only in staging")

        run_id = f"ingest:{uuid4().hex}"
        repository = SqlAlchemyIngestionRepository(self._engine)
        repository.start_run(run_id)
        adapter = BmstuUniversityAdapter()
        mode = "fixture" if request.source is IngestionRetrySource.BMSTU_FIXTURE else "live"
        try:
            captured = adapter.capture(mode=mode)
            repository.record_captured_metadata(run_id, captured)
            raw, canonical = adapter.parse(captured)
            repository.record_source_metadata(run_id, raw)
            repository.ingest(raw, canonical, run_id=run_id)
        except Exception as exc:
            repository.mark_failed(run_id, exc)
            logger.warning("admin_ops_retry_failed run_id=%s source=%s error_code=%s", run_id, request.source.value, type(exc).__name__)
        finally:
            adapter.close()
        logger.info("admin_ops_retry_complete run_id=%s source=%s", run_id, request.source.value)
        return IngestionRetryOutcome(run_id=run_id, source=request.source)


__all__ = ["SqlAlchemyBmstuIngestionRetryExecutor"]
