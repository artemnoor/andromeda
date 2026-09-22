from __future__ import annotations

from andromeda.ingestion.contracts.admission_benefits import (
    AdmissionBenefitCoverage,
    AdmissionBenefitCoverageStatus,
    RawAdmissionBenefitRecord,
)


def build_coverage(
    *,
    documents_discovered: int,
    documents_captured: int,
    records: tuple[RawAdmissionBenefitRecord, ...],
    normalized_count: int,
    resolved_targets: int = 0,
    unresolved_targets: int = 0,
    conflicts: int = 0,
    review_required_rows: int = 0,
) -> AdmissionBenefitCoverage:
    status = AdmissionBenefitCoverageStatus.COMPLETE
    if conflicts or review_required_rows or unresolved_targets:
        status = AdmissionBenefitCoverageStatus.REVIEW_REQUIRED
    elif documents_captured < documents_discovered or normalized_count < len(records):
        status = AdmissionBenefitCoverageStatus.PARTIAL
    return AdmissionBenefitCoverage(
        status=status,
        documents_discovered=documents_discovered,
        documents_captured=documents_captured,
        documents_parsed=len({record.source_snapshot_hash for record in records}),
        records_normalized=normalized_count,
        targets_resolved=resolved_targets,
        unresolved_targets=unresolved_targets,
        conflicts=conflicts,
        review_required_rows=review_required_rows,
        source_hashes=tuple(dict.fromkeys(record.source_snapshot_hash for record in records)),
    )


__all__ = ["build_coverage"]
