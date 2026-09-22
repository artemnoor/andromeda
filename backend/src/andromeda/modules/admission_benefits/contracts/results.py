"""Explainable deterministic benefit-evaluation results."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import (
    AdmissionBenefitRuleId,
    EducationYear,
    IndividualAchievementRuleId,
    NonEmptyText,
    ProgramId,
    ShortText,
)

from .provenance import BenefitProvenance
from .public import (
    AchievementCombinationPolicy,
    AdmissionRoute,
    BenefitType,
    OlympiadResultType,
)


class EligibilityStatus(StrEnum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    INSUFFICIENT_DATA = "insufficient_data"
    REVIEW_REQUIRED = "review_required"


class AdmissionBenefitEvidence(ContractModel):
    rule_id: AdmissionBenefitRuleId | IndividualAchievementRuleId
    provenance: BenefitProvenance
    excerpt: ShortText | None = None


class AdmissionBenefitEvaluation(ContractModel):
    rule_id: AdmissionBenefitRuleId
    benefit_type: BenefitType
    route: AdmissionRoute | None = None
    status: EligibilityStatus
    result_type: OlympiadResultType | None = None
    matched_applicant_fact: ShortText | None = None
    rejection_reason: ShortText | None = None
    effective_score_change: Decimal | None = None
    points_contribution: Decimal | None = None
    evidence: tuple[AdmissionBenefitEvidence, ...] = Field(min_length=1)


class IndividualAchievementStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVIEW_REQUIRED = "review_required"
    DEDUPLICATED = "deduplicated"
    CAPPED = "capped"
    EXCLUDED = "excluded"


class IndividualAchievementEvaluation(ContractModel):
    rule_id: IndividualAchievementRuleId | None = None
    achievement_code: NonEmptyText
    status: IndividualAchievementStatus
    applicant_year: EducationYear | None = None
    rule_points: Decimal | None = Field(default=None, strict=True, ge=Decimal(0), le=Decimal(100), max_digits=5, decimal_places=2)
    awarded_points: Decimal = Field(strict=True, ge=Decimal(0), le=Decimal(100), max_digits=5, decimal_places=2)
    combination_policy: AchievementCombinationPolicy | None = None
    reason: ShortText
    evidence: tuple[AdmissionBenefitEvidence, ...] = ()


class IndividualAchievementBreakdown(ContractModel):
    status: EligibilityStatus
    total_points: Decimal = Field(strict=True, ge=Decimal(0), le=Decimal(100), max_digits=6, decimal_places=2)
    uncapped_points: Decimal = Field(strict=True, ge=Decimal(0), le=Decimal(100), max_digits=6, decimal_places=2)
    global_cap: Decimal | None = Field(default=None, strict=True, ge=Decimal(0), le=Decimal(100), max_digits=5, decimal_places=2)
    evaluations: tuple[IndividualAchievementEvaluation, ...] = ()
    source_gaps: tuple[ShortText, ...] = ()


class AdmissionEligibilityResult(ContractModel):
    program_id: ProgramId
    admission_year: EducationYear
    status: EligibilityStatus
    route: AdmissionRoute | None = None
    evaluations: tuple[AdmissionBenefitEvaluation, ...] = ()
    base_competitive_score: Decimal | None = None
    individual_achievement_points: Decimal | None = None
    effective_competitive_score: Decimal | None = None
    source_gaps: tuple[ShortText, ...] = ()


class AdmissionDecisionResult(ContractModel):
    """Legal eligibility plus optional individual-achievement score composition."""

    program_id: ProgramId
    admission_year: EducationYear
    status: EligibilityStatus
    route: AdmissionRoute | None = None
    eligibility: AdmissionEligibilityResult | None = None
    individual_achievements: IndividualAchievementBreakdown | None = None
    base_competitive_score: Decimal | None = None
    individual_achievement_points: Decimal | None = None
    effective_competitive_score: Decimal | None = None
    source_gaps: tuple[ShortText, ...] = ()


__all__ = [
    "AdmissionBenefitEvaluation",
    "AdmissionBenefitEvidence",
    "AdmissionDecisionResult",
    "AdmissionEligibilityResult",
    "EligibilityStatus",
    "IndividualAchievementBreakdown",
    "IndividualAchievementEvaluation",
    "IndividualAchievementStatus",
]
