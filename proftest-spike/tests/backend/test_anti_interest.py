from __future__ import annotations

from decimal import Decimal

from proftest_spike.domain.areas import AreaCode
from proftest_spike.matching.scoring import ScoringService
from proftest_spike.program_fingerprints.entities import ActivityCode, ProgramFingerprint
from proftest_spike.profiling.entities import Confidence, UserProfile


def _program(code: str, physics_share: str) -> ProgramFingerprint:
    physics = Decimal(physics_share)
    computer = Decimal("1") - physics
    return ProgramFingerprint(
        program_id=f"program:{code}",
        program_code=code,
        program_name=code,
        basis="hours",
        total_hours=100,
        total_credits=Decimal("3"),
        total_workload=Decimal("100"),
        area_hours={AreaCode.COMPUTER_SCIENCE_DATA: computer * 100, AreaCode.PHYSICS_ASTRONOMY: physics * 100},
        area_share={AreaCode.COMPUTER_SCIENCE_DATA: computer, AreaCode.PHYSICS_ASTRONOMY: physics},
        subject_group_hours={"core": Decimal("100")},
        subject_group_share={"core": Decimal("1")},
        semester_distribution={"1": Decimal("1")},
        activity_signals={ActivityCode.SOFTWARE_CREATION: computer, ActivityCode.PHYSICAL_ENGINEERING: physics},
        evidence=(),
    )


def _profile(intensity: str) -> UserProfile:
    return UserProfile(
        interests=(AreaCode.COMPUTER_SCIENCE_DATA,),
        activity_preferences=(ActivityCode.SOFTWARE_CREATION,),
        anti_interests=(),
        preferred_subject_weights={AreaCode.COMPUTER_SCIENCE_DATA: Decimal("1")},
        preferred_activity_weights={ActivityCode.SOFTWARE_CREATION: Decimal("1")},
        negative_weights={AreaCode.PHYSICS_ASTRONOMY: Decimal(intensity)},
        confidence=Confidence(value=Decimal("1"), answered_base=5, answered_adaptive=0),
    )


def test_stronger_anti_interest_never_improves_high_area_program() -> None:
    program = _program("mixed", "0.60")
    low = ScoringService().score(_profile("0.20"), program)
    high = ScoringService().score(_profile("0.90"), program)

    assert high.content_fit <= low.content_fit
    assert high.breakdown.anti_penalty > low.breakdown.anti_penalty


def test_high_physics_program_is_penalized_relative_to_low_physics_program() -> None:
    profile = _profile("0.95")
    high_physics = ScoringService().score(profile, _program("physics-heavy", "0.80"))
    low_physics = ScoringService().score(profile, _program("it-heavy", "0.10"))

    assert high_physics.content_fit < low_physics.content_fit
