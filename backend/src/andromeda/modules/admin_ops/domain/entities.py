from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import IngestRunId, ShortText, SourceHash


class IngestionRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionRunSummary(ContractModel):
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

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "IngestionRunSummary":
        if self.status is IngestionRunStatus.RUNNING and self.finished_at is not None:
            raise ValueError("running ingestion run cannot have finished_at")
        if self.status is not IngestionRunStatus.RUNNING and self.finished_at is None:
            raise ValueError("terminal ingestion run must have finished_at")
        if self.status is IngestionRunStatus.FAILED and self.error_code is None:
            raise ValueError("failed ingestion run must have error_code")
        if self.status is not IngestionRunStatus.FAILED and self.error_code is not None:
            raise ValueError("only failed ingestion run may have error_code")
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("ingestion run started_at must be timezone-aware")
        return self


class IngestionRunDetail(IngestionRunSummary):
    source_hashes: tuple[SourceHash, ...] = ()
    source_kinds: tuple[ShortText, ...] = ()


__all__ = ["IngestionRunDetail", "IngestionRunStatus", "IngestionRunSummary"]
