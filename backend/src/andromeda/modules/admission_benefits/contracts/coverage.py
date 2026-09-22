"""Coverage metadata shared by ingestion and admission-benefit consumers."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import SourceHash


class AdmissionBenefitCoverageStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    REVIEW_REQUIRED = "review_required"
    UNAVAILABLE = "unavailable"


class AdmissionBenefitCoverage(ContractModel):
    status: AdmissionBenefitCoverageStatus = AdmissionBenefitCoverageStatus.PARTIAL
    documents_discovered: int = Field(default=0, strict=True, ge=0)
    documents_captured: int = Field(default=0, strict=True, ge=0)
    documents_parsed: int = Field(default=0, strict=True, ge=0)
    records_normalized: int = Field(default=0, strict=True, ge=0)
    targets_resolved: int = Field(default=0, strict=True, ge=0)
    unresolved_targets: int = Field(default=0, strict=True, ge=0)
    conflicts: int = Field(default=0, strict=True, ge=0)
    review_required_rows: int = Field(default=0, strict=True, ge=0)
    source_hashes: tuple[SourceHash, ...] = ()


__all__ = ["AdmissionBenefitCoverage", "AdmissionBenefitCoverageStatus"]
