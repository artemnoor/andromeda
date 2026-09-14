from __future__ import annotations

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel

from ..domain.entities import IngestionRunDetail, IngestionRunSummary


class IngestionRunListResult(ContractModel):
    items: tuple[IngestionRunSummary, ...] = ()
    total: int = Field(strict=True, ge=0)


class IngestionRunDetailResult(ContractModel):
    run: IngestionRunDetail


__all__ = ["IngestionRunDetailResult", "IngestionRunListResult"]
