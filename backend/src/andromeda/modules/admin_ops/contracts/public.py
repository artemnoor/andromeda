from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel

from ..domain.entities import IngestionRunDetail, IngestionRunStatus, IngestionRunSummary


class IngestionRunFilters(ContractModel):
    status: IngestionRunStatus | None = None
    limit: int = Field(default=50, strict=True, ge=1, le=100)


class IngestionRetrySource(StrEnum):
    BMSTU_FIXTURE = "bmstu_fixture"
    BMSTU_LIVE = "bmstu_live"


class IngestionRetryRequest(ContractModel):
    source: IngestionRetrySource = IngestionRetrySource.BMSTU_FIXTURE


__all__ = [
    "IngestionRunDetail",
    "IngestionRunFilters",
    "IngestionRunStatus",
    "IngestionRunSummary",
    "IngestionRetryRequest",
    "IngestionRetrySource",
]
