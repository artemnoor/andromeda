"""Pure EGE/internal-exam confirmation evaluation."""

from __future__ import annotations

import logging
import re
from decimal import Decimal

from pydantic import Field

from andromeda.modules.admission_benefits.contracts.applicant import (
    ApplicantExamScore,
    ApplicantInternalExamScore,
)
from andromeda.modules.admission_benefits.contracts.public import (
    ConfirmationExamKind,
    ConfirmationRequirement,
    ConfirmationSubjectRule,
)
from andromeda.modules.admission_benefits.contracts.results import EligibilityStatus
from andromeda.shared.contracts.base import ContractModel

logger = logging.getLogger("andromeda.modules.admission_benefits.confirmation")


class ConfirmationEvaluation(ContractModel):
    status: EligibilityStatus
    reason: str = Field(min_length=1, max_length=256)
    matched_subject: str | None = None
    required_score: Decimal | None = None
    provided_score: Decimal | None = None
    exam_kind: ConfirmationExamKind | None = None


def evaluate_confirmation(
    requirement: ConfirmationRequirement,
    subjects: tuple[ConfirmationSubjectRule, ...],
    *,
    ege_scores: tuple[ApplicantExamScore, ...] = (),
    internal_exam_scores: tuple[ApplicantInternalExamScore, ...] = (),
) -> ConfirmationEvaluation:
    if requirement is ConfirmationRequirement.NOT_REQUIRED:
        return _result(EligibilityStatus.ELIGIBLE, "Source rule does not require confirmation")
    if requirement is ConfirmationRequirement.UNKNOWN:
        return _result(EligibilityStatus.REVIEW_REQUIRED, "Source confirmation requirement is unknown")
    if not subjects:
        return _result(EligibilityStatus.REVIEW_REQUIRED, "Confirmation subject or threshold is missing")

    insufficient = False
    below_threshold = False
    for subject_rule in subjects:
        if subject_rule.minimum_score is None:
            return _result(EligibilityStatus.REVIEW_REQUIRED, "Confirmation threshold is unknown")
        scores: tuple[ApplicantExamScore, ...] | tuple[ApplicantInternalExamScore, ...]
        if subject_rule.exam_kind is ConfirmationExamKind.INTERNAL_EXAM:
            scores = internal_exam_scores
        elif subject_rule.exam_kind is ConfirmationExamKind.EGE:
            scores = ege_scores
        else:
            return _result(EligibilityStatus.REVIEW_REQUIRED, "Confirmation exam kind is unknown")
        score = next((item.score for item in scores if _same_subject(item.subject, subject_rule.subject)), None)
        if score is None:
            insufficient = True
            continue
        if score >= subject_rule.minimum_score:
            return ConfirmationEvaluation(
                status=EligibilityStatus.ELIGIBLE,
                reason="Applicant result satisfies the source confirmation threshold",
                matched_subject=subject_rule.subject,
                required_score=subject_rule.minimum_score,
                provided_score=score,
                exam_kind=subject_rule.exam_kind,
            )
        below_threshold = True
    if insufficient:
        return _result(EligibilityStatus.INSUFFICIENT_DATA, "Applicant confirmation subject is missing")
    if below_threshold:
        return _result(EligibilityStatus.NOT_ELIGIBLE, "Applicant result is below the source confirmation threshold")
    return _result(
        EligibilityStatus.NOT_ELIGIBLE,
        "Applicant confirmation does not satisfy any allowed subject",
    )


def _same_subject(left: str, right: str) -> bool:
    return _normalize_subject(left) == _normalize_subject(right)


def _normalize_subject(value: str) -> str:
    return re.sub(r"[^\w]+", " ", value.casefold().replace("ё", "е")).strip()


def _result(status: EligibilityStatus, reason: str) -> ConfirmationEvaluation:
    logger.info("admission_benefit_confirmation_evaluated status=%s reason=%s", status, reason)
    return ConfirmationEvaluation(status=status, reason=reason)


__all__ = ["ConfirmationEvaluation", "evaluate_confirmation"]
