"""Canonical admission-benefit snapshot independent from ingestion adapters."""

from __future__ import annotations

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.provenance import SourceAttribution, SourceGapReference

from .coverage import AdmissionBenefitCoverage
from .public import (
    AdmissionBenefitRule,
    IndividualAchievementPolicy,
    Olympiad,
    OlympiadProfile,
)


class AdmissionBenefitsSnapshot(ContractModel):
    """Versioned canonical projection for one university and admission year."""

    admission_year: int = Field(strict=True, ge=2000, le=2100)
    sources: tuple[SourceAttribution, ...] = Field(min_length=1)
    olympiads: tuple[Olympiad, ...] = ()
    olympiad_profiles: tuple[OlympiadProfile, ...] = ()
    benefit_rules: tuple[AdmissionBenefitRule, ...] = ()
    individual_achievement_policy: IndividualAchievementPolicy | None = None
    coverage: AdmissionBenefitCoverage
    source_gaps: tuple[SourceGapReference, ...] = ()


__all__ = ["AdmissionBenefitsSnapshot"]
