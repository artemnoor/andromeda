from __future__ import annotations

from decimal import Decimal

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode
from andromeda.modules.proftest.contracts.public import ActivityCode, AdaptiveStatus, ProgramFingerprint
from andromeda.modules.proftest.services.adaptive import AdaptiveCandidate, AdaptiveQuestionFactory, AdaptiveQuestionSelector


def _fingerprint(code: str, math_share: str, computer_share: str) -> ProgramFingerprint:
    return ProgramFingerprint(
        program_id=f"program:09.03.01-{code}",
        program_code=f"09.03.01-{code}",
        program_name=code,
        basis="hours",
        total_hours=100,
        total_credits=Decimal("10"),
        total_workload=Decimal("100"),
        area_hours={DisciplineAreaCode.MATHEMATICS_STATISTICS: Decimal(math_share) * 100, DisciplineAreaCode.COMPUTER_SCIENCE_DATA: Decimal(computer_share) * 100},
        area_share={DisciplineAreaCode.MATHEMATICS_STATISTICS: Decimal(math_share), DisciplineAreaCode.COMPUTER_SCIENCE_DATA: Decimal(computer_share)},
        subject_group_hours={"base": Decimal("100")},
        subject_group_share={"base": Decimal("1")},
        semester_distribution={"1": Decimal("1")},
        activity_signals={ActivityCode.ANALYTICAL: Decimal("0.5"), ActivityCode.SOFTWARE_CREATION: Decimal("0.5")},
    )


def test_adaptive_selector_uses_largest_candidate_spread() -> None:
    candidates = (
        AdaptiveCandidate(_fingerprint("02", "0.8", "0.2"), Decimal("80")),
        AdaptiveCandidate(_fingerprint("12", "0.2", "0.8"), Decimal("79")),
    )

    selection = AdaptiveQuestionSelector().select(candidates)

    assert selection.status is AdaptiveStatus.READY
    assert tuple(dimension.code for dimension in selection.dimensions) == (
        "area:computer_science_data",
        "area:mathematics_statistics",
    )
    question = AdaptiveQuestionFactory().create(selection)
    assert question is not None
    assert question.adaptive is True
    assert len(question.options) == 3


def test_adaptive_selector_skips_when_catalog_has_no_meaningful_spread() -> None:
    fingerprint = _fingerprint("02", "0.5", "0.5")
    selection = AdaptiveQuestionSelector().select((AdaptiveCandidate(fingerprint, Decimal("70")), AdaptiveCandidate(fingerprint, Decimal("70"))))

    assert selection.status is AdaptiveStatus.SKIPPED
    assert selection.reason
    assert AdaptiveQuestionFactory().create(selection) is None
