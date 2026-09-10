from __future__ import annotations

from decimal import Decimal

from proftest_spike.domain.areas import AreaCode
from proftest_spike.matching.ranking import RankingService
from proftest_spike.program_fingerprints.entities import ActivityCode, ProgramFingerprint
from proftest_spike.profiling.entities import Confidence, UserProfile


def _program(code: str, area: AreaCode, activity: ActivityCode) -> ProgramFingerprint:
    return ProgramFingerprint(
        program_id=f"program:{code}",
        program_code=code,
        program_name=code,
        basis="hours",
        total_hours=100,
        total_credits=Decimal("3"),
        total_workload=Decimal("100"),
        area_hours={area: Decimal("100")},
        area_share={area: Decimal("1")},
        subject_group_hours={"core": Decimal("100")},
        subject_group_share={"core": Decimal("1")},
        semester_distribution={"1": Decimal("1")},
        activity_signals={activity: Decimal("1")},
        evidence=(),
    )


def _profile(area: AreaCode, activity: ActivityCode, *, anti: dict[AreaCode, str] | None = None) -> UserProfile:
    return UserProfile(
        interests=(area,),
        activity_preferences=(activity,),
        anti_interests=(),
        preferred_subject_weights={area: Decimal("1")},
        preferred_activity_weights={activity: Decimal("1")},
        negative_weights={key: Decimal(value) for key, value in (anti or {}).items()},
        confidence=Confidence(value=Decimal("1"), answered_base=5, answered_adaptive=0),
    )


PROGRAMS = (
    _program("it", AreaCode.COMPUTER_SCIENCE_DATA, ActivityCode.SOFTWARE_CREATION),
    _program("engineering", AreaCode.ENGINEERING_TECHNOLOGY, ActivityCode.PHYSICAL_ENGINEERING),
    _program("economics", AreaCode.ECONOMICS_FINANCE, ActivityCode.BUSINESS),
    _program("data", AreaCode.MATHEMATICS_STATISTICS, ActivityCode.DATA),
)


def test_five_synthetic_personas_have_logical_relative_rankings() -> None:
    personas = (
        _profile(AreaCode.COMPUTER_SCIENCE_DATA, ActivityCode.SOFTWARE_CREATION),
        _profile(AreaCode.ENGINEERING_TECHNOLOGY, ActivityCode.PHYSICAL_ENGINEERING),
        _profile(AreaCode.ECONOMICS_FINANCE, ActivityCode.BUSINESS, anti={AreaCode.PHYSICS_ASTRONOMY: "0.9"}),
        _profile(AreaCode.MATHEMATICS_STATISTICS, ActivityCode.DATA),
        _profile(AreaCode.COMPUTER_SCIENCE_DATA, ActivityCode.SOFTWARE_CREATION, anti={AreaCode.ENGINEERING_TECHNOLOGY: "0.95"}),
    )
    expected_areas = (
        AreaCode.COMPUTER_SCIENCE_DATA,
        AreaCode.ENGINEERING_TECHNOLOGY,
        AreaCode.ECONOMICS_FINANCE,
        AreaCode.MATHEMATICS_STATISTICS,
        AreaCode.COMPUTER_SCIENCE_DATA,
    )

    for profile, expected_area in zip(personas, expected_areas):
        ranked = RankingService().rank(profile, PROGRAMS)
        assert ranked
        top = ranked[0][0]
        assert top.area_share.get(expected_area, Decimal("0")) == max(item[0].area_share.get(expected_area, Decimal("0")) for item in ranked)


def test_same_profile_is_deterministic() -> None:
    profile = _profile(AreaCode.COMPUTER_SCIENCE_DATA, ActivityCode.SOFTWARE_CREATION)
    first = RankingService().rank(profile, PROGRAMS)
    second = RankingService().rank(profile, PROGRAMS)

    assert [(item[0].program_code, item[1].content_fit) for item in first] == [(item[0].program_code, item[1].content_fit) for item in second]
