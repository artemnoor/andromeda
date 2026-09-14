from __future__ import annotations

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel

from ..domain.entities import IngestionRunDetail, IngestionRunStatus, IngestionRunSummary


class IngestionRunFilters(ContractModel):
    status: IngestionRunStatus | None = None
    limit: int = Field(default=50, strict=True, ge=1, le=100)


__all__ = [
    "IngestionRunDetail",
    "IngestionRunFilters",
    "IngestionRunStatus",
    "IngestionRunSummary",
]
