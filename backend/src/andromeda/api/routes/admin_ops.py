from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query

from andromeda.api.dependencies import get_ingestion_run_service, require_ops_access
from andromeda.api.schemas.admin_ops import IngestionRetryRequestBody, IngestionRunDetailEnvelope, IngestionRunListResponse, ingestion_run_detail_response, ingestion_run_list_response
from andromeda.modules.admin_ops.contracts.public import IngestionRetryRequest, IngestionRetrySource, IngestionRunFilters, IngestionRunStatus
from andromeda.modules.admin_ops.contracts.results import IngestionRunDetailResult
from andromeda.modules.admin_ops.services.ingestion_runs import IngestionRunService
from andromeda.shared.contracts.ids import IngestRunId


logger = logging.getLogger("andromeda.api.admin_ops")
router = APIRouter(prefix="/ops/ingestion", tags=["admin-ops"])


@router.post("/runs/retry", response_model=IngestionRunDetailEnvelope, operation_id="retry_ingestion_run", dependencies=[Depends(require_ops_access)])
def retry_ingestion_run(
    body: IngestionRetryRequestBody,
    service: IngestionRunService = Depends(get_ingestion_run_service),
) -> IngestionRunDetailEnvelope:
    result = service.retry(IngestionRetryRequest(source=IngestionRetrySource(body.source)))
    response = ingestion_run_detail_response(IngestionRunDetailResult(run=result.run))
    logger.info("admin_ops_ingestion_retry_complete run_id=%s source=%s", result.run.id, body.source)
    return response


@router.get("/runs", response_model=IngestionRunListResponse, operation_id="list_ingestion_runs", dependencies=[Depends(require_ops_access)])
def list_ingestion_runs(
    status: IngestionRunStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    service: IngestionRunService = Depends(get_ingestion_run_service),
) -> IngestionRunListResponse:
    result = service.list(IngestionRunFilters(status=status, limit=limit))
    response = ingestion_run_list_response(result)
    logger.info("admin_ops_ingestion_runs_complete result_count=%d total=%d", len(response.items), response.total)
    return response


@router.get("/runs/{id}", response_model=IngestionRunDetailEnvelope, operation_id="get_ingestion_run", dependencies=[Depends(require_ops_access)])
def get_ingestion_run(
    id: IngestRunId,
    service: IngestionRunService = Depends(get_ingestion_run_service),
) -> IngestionRunDetailEnvelope:
    result = service.get(id)
    response = ingestion_run_detail_response(result)
    logger.info("admin_ops_ingestion_run_detail_complete run_id=%s", id)
    return response


__all__ = ["router"]
