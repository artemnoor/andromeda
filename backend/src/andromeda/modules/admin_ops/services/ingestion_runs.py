from __future__ import annotations

import logging

from andromeda.shared.contracts.errors import NotFoundError
from andromeda.shared.contracts.ids import IngestRunId

from ..contracts.public import IngestionRunFilters
from ..contracts.results import IngestionRunDetailResult, IngestionRunListResult
from ..repository.ports import IngestionRunReader


logger = logging.getLogger("andromeda.admin_ops")


class IngestionRunService:
    """Read-only application service for bounded ingestion audit views."""

    def __init__(self, reader: IngestionRunReader) -> None:
        self._reader = reader

    def list(self, filters: IngestionRunFilters) -> IngestionRunListResult:
        logger.debug("ingestion_runs_use_case_start status=%s limit=%d", filters.status, filters.limit)
        result = self._reader.list(filters)
        logger.info("ingestion_runs_use_case_complete result_count=%d total=%d", len(result.items), result.total)
        return result

    def get(self, run_id: IngestRunId) -> IngestionRunDetailResult:
        logger.debug("ingestion_run_detail_use_case_start run_id=%s", run_id)
        result = self._reader.get(run_id)
        if result is None:
            logger.warning("ingestion_run_detail_not_found run_id=%s", run_id)
            raise NotFoundError("Ingestion run was not found")
        logger.info("ingestion_run_detail_use_case_complete run_id=%s", run_id)
        return result


__all__ = ["IngestionRunService"]
