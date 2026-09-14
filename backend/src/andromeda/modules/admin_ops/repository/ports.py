from __future__ import annotations

from typing import Protocol

from andromeda.shared.contracts.ids import IngestRunId

from ..contracts.public import IngestionRunFilters
from ..contracts.results import IngestionRunDetailResult, IngestionRunListResult


class IngestionRunReader(Protocol):
    def list(self, filters: IngestionRunFilters) -> IngestionRunListResult: ...

    def get(self, run_id: IngestRunId) -> IngestionRunDetailResult | None: ...


__all__ = ["IngestionRunReader"]
