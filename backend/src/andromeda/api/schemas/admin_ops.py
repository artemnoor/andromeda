from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from andromeda.modules.admin_ops.contracts.public import IngestionRunStatus
from andromeda.modules.admin_ops.contracts.results import IngestionRunDetailResult, IngestionRunListResult
from andromeda.modules.admin_ops.domain.entities import IngestionRunDetail, IngestionRunSummary
from andromeda.shared.contracts.ids import IngestRunId, SourceHash

from .common import ApiModel


class IngestionRunSummaryResponse(ApiModel):
    id: IngestRunId
    status: IngestionRunStatus
    started_at: datetime
    finished_at: datetime | None = None
    source_count: int = Field(strict=True, ge=0)
    program_count: int = Field(strict=True, ge=0)
    curriculum_item_count: int = Field(strict=True, ge=0)
    event_count: int = Field(strict=True, ge=0)
    campus_point_count: int = Field(strict=True, ge=0)
    inserted_count: int = Field(strict=True, ge=0)
    updated_count: int = Field(strict=True, ge=0)
    unchanged_count: int = Field(strict=True, ge=0)
    removed_count: int = Field(strict=True, ge=0)
    error_code: str | None = Field(default=None, min_length=1, max_length=64)
    error_message: str | None = Field(default=None, min_length=1, max_length=512)


class IngestionRunDetailResponse(IngestionRunSummaryResponse):
    source_hashes: tuple[SourceHash, ...] = ()
    source_kinds: tuple[str, ...] = ()


class IngestionRunListResponse(ApiModel):
    items: tuple[IngestionRunSummaryResponse, ...] = ()
    total: int = Field(strict=True, ge=0)


class IngestionRunDetailEnvelope(ApiModel):
    run: IngestionRunDetailResponse


class IngestionRetryRequestBody(ApiModel):
    source: Literal["bmstu_fixture", "bmstu_live"] = "bmstu_fixture"


def ingestion_run_summary_response(run: IngestionRunSummary) -> IngestionRunSummaryResponse:
    return IngestionRunSummaryResponse.model_validate(run.model_dump(mode="python"))


def ingestion_run_list_response(result: IngestionRunListResult) -> IngestionRunListResponse:
    return IngestionRunListResponse(
        items=tuple(ingestion_run_summary_response(item) for item in result.items),
        total=result.total,
    )


def ingestion_run_detail_response(result: IngestionRunDetailResult) -> IngestionRunDetailEnvelope:
    run: IngestionRunDetail = result.run
    return IngestionRunDetailEnvelope(run=IngestionRunDetailResponse.model_validate(run.model_dump(mode="python")))


__all__ = [
    "IngestionRunDetailEnvelope",
    "IngestionRunDetailResponse",
    "IngestionRunListResponse",
    "IngestionRunSummaryResponse",
    "IngestionRetryRequestBody",
    "ingestion_run_detail_response",
    "ingestion_run_list_response",
]
