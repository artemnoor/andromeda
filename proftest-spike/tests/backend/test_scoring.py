from __future__ import annotations

from decimal import Decimal

from proftest_spike.domain.areas import AreaCode
from proftest_spike.matching.ranking import RankingService
from proftest_spike.matching.scoring import ScoringService
from proftest_spike.program_fingerprints.entities import ActivityCode, ProgramFingerprint
from proftest_spike.profiling.entities import Confidence, UserProfile


def _fingerprint(code: str, areas: dict[AreaCode, str], activities: dict[ActivityCode, str]) -> ProgramFingerprint:
    return ProgramFingerprint(
        program_id=f"program:{code}",
        program_code=code,
        program_name=f"Program {code}",
        basis="hours",
        total_hours=100,
        total_credits=Decimal("3"),
        total_workload=Decimal("100"),
        area_hours={area: Decimal(value) * Decimal("100") for area, value in areas.items()},
        area_share={area: Decimal(value) for area, value in areas.items()},
        subject_group_hours={"core": Decimal("100")},
        subject_group_share={"core": Decimal("1")},
        semester_distribution={"1": Decimal("1")},
        activity_signals={activity: Decimal(value) for activity, value in activities.items()},
        evidence=(),
    )


def _profile(
    subjects: dict[AreaCode, str],
    activities: dict[ActivityCode, str],
    negative: dict[AreaCode, str] | None = None,
) -> UserProfile:
    return UserProfile(
        interests=tuple(subjects),
        activity_preferences=tuple(activities),
        anti_interests=(),
        preferred_subject_weights={area: Decimal(value) for area, value in subjects.items()},
        preferred_activity_weights={activity: Decimal(value) for activity, value in activities.items()},
        negative_weights={area: Decimal(value) for area, value in (negative or {}).items()},
        confidence=Confidence(value=Decimal("1"), answered_base=5, answered_adaptive=0),
    )


def test_fixed_formula_is_explicit_and_rounded_to_integer() -> None:
    fingerprint = _fingerprint(
        "iu7",
        {AreaCode.COMPUTER_SCIENCE_DATA: "0.7", AreaCode.PHYSICS_ASTRONOMY: "0.3"},
        {ActivityCode.SOFTWARE_CREATION: "0.8", ActivityCode.PHYSICAL_ENGINEERING: "0.2"},
    )
    profile = _profile(
        {AreaCode.COMPUTER_SCIENCE_DATA: "1"},
        {ActivityCode.SOFTWARE_CREATION: "1"},
        {AreaCode.PHYSICS_ASTRONOMY: "0.5"},
    )

    score = ScoringService().score(profile, fingerprint)

    assert score.breakdown.subject_fit == Decimal("70")
    assert score.breakdown.activity_fit == Decimal("80")
    assert score.breakdown.distinctive_fit == Decimal("50")
    assert score.breakdown.anti_penalty == Decimal("15")
    assert score.breakdown.raw_content_fit == Decimal("59.5")
    assert score.content_fit == 60


def test_neutral_profile_has_neutral_content_fit() -> None:
    fingerprint = _fingerprint("neutral", {AreaCode.COMPUTER_SCIENCE_DATA: "1"}, {ActivityCode.SOFTWARE_CREATION: "1"})
    profile = _profile({}, {})

    score = ScoringService().score(profile, fingerprint)

    assert score.content_fit == 50
    assert score.breakdown.subject_fit == Decimal("50")
    assert score.breakdown.activity_fit == Decimal("50")


def test_ranking_has_stable_code_tie_break() -> None:
    first = _fingerprint("aa", {AreaCode.COMPUTER_SCIENCE_DATA: "1"}, {ActivityCode.SOFTWARE_CREATION: "1"})
    second = _fingerprint("bb", {AreaCode.COMPUTER_SCIENCE_DATA: "1"}, {ActivityCode.SOFTWARE_CREATION: "1"})
    profile = _profile({AreaCode.COMPUTER_SCIENCE_DATA: "1"}, {ActivityCode.SOFTWARE_CREATION: "1"})

    ranked = RankingService().rank(profile, (second, first))

    assert [item[0].program_code for item in ranked] == ["aa", "bb"]


def test_content_fit_is_always_bounded() -> None:
    fingerprint = _fingerprint("bounded", {AreaCode.COMPUTER_SCIENCE_DATA: "1"}, {ActivityCode.SOFTWARE_CREATION: "1"})
    profile = _profile({}, {}, {AreaCode.COMPUTER_SCIENCE_DATA: "1"})

    score = ScoringService().score(profile, fingerprint)

    assert 0 <= score.content_fit <= 100
