from decimal import Decimal

from andromeda.modules.admission_benefits.contracts.applicant import ApplicantExamScore, ApplicantInternalExamScore
from andromeda.modules.admission_benefits.contracts.public import ConfirmationExamKind, ConfirmationRequirement, ConfirmationSubjectRule
from andromeda.modules.admission_benefits.contracts.results import EligibilityStatus
from andromeda.modules.admission_benefits.services.confirmation import evaluate_confirmation


def _subject(name: str = "информатика", minimum: str | None = "75", kind: ConfirmationExamKind = ConfirmationExamKind.EGE) -> ConfirmationSubjectRule:
    return ConfirmationSubjectRule(
        subject=name,
        minimum_score=Decimal(minimum) if minimum is not None else None,
        exam_kind=kind,
        source_text="Правила приема 2026",
    )


def test_ege_threshold_is_source_backed_and_boundary_is_inclusive() -> None:
    subjects = (_subject(),)
    passed = evaluate_confirmation(
        ConfirmationRequirement.REQUIRED,
        subjects,
        ege_scores=(ApplicantExamScore(subject="Информатика", score=Decimal("75")),),
    )
    failed = evaluate_confirmation(
        ConfirmationRequirement.REQUIRED,
        subjects,
        ege_scores=(ApplicantExamScore(subject="Информатика", score=Decimal("74")),),
    )
    assert passed.status is EligibilityStatus.ELIGIBLE
    assert failed.status is EligibilityStatus.NOT_ELIGIBLE


def test_any_allowed_subject_can_confirm_the_result() -> None:
    result = evaluate_confirmation(
        ConfirmationRequirement.REQUIRED,
        (_subject("информатика"), _subject("физика")),
        ege_scores=(ApplicantExamScore(subject="физика", score=Decimal("80")),),
    )
    assert result.status is EligibilityStatus.ELIGIBLE
    assert result.matched_subject == "физика"


def test_internal_exam_is_not_mixed_with_ege() -> None:
    result = evaluate_confirmation(
        ConfirmationRequirement.REQUIRED,
        (_subject(kind=ConfirmationExamKind.INTERNAL_EXAM),),
        ege_scores=(ApplicantExamScore(subject="информатика", score=Decimal("100")),),
        internal_exam_scores=(ApplicantInternalExamScore(subject="информатика", score=Decimal("75")),),
    )
    assert result.status is EligibilityStatus.ELIGIBLE
    assert result.exam_kind is ConfirmationExamKind.INTERNAL_EXAM


def test_unknown_threshold_and_exam_kind_fail_closed() -> None:
    unknown_threshold = evaluate_confirmation(
        ConfirmationRequirement.REQUIRED,
        (_subject(minimum=None),),
    )
    unknown_kind = evaluate_confirmation(
        ConfirmationRequirement.REQUIRED,
        (_subject(kind=ConfirmationExamKind.UNKNOWN),),
        ege_scores=(ApplicantExamScore(subject="информатика", score=Decimal("100")),),
    )
    assert unknown_threshold.status is EligibilityStatus.REVIEW_REQUIRED
    assert unknown_kind.status is EligibilityStatus.REVIEW_REQUIRED
