from __future__ import annotations

from decimal import Decimal

from proftest_spike.api_client.contracts import CurriculumResponse
from proftest_spike.explanations.builder import ExplanationBuilder
from proftest_spike.matching.scoring import ScoringService
from proftest_spike.program_fingerprints.builder import FingerprintBuilder
from proftest_spike.profiling.entities import Confidence, UserProfile
from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode

from .test_program_fingerprints import _curriculum


def _profile() -> UserProfile:
    return UserProfile(
        interests=(AreaCode.COMPUTER_SCIENCE_DATA,),
        activity_preferences=(ActivityCode.SOFTWARE_CREATION,),
        anti_interests=(),
        preferred_subject_weights={AreaCode.COMPUTER_SCIENCE_DATA: Decimal("1")},
        preferred_activity_weights={ActivityCode.SOFTWARE_CREATION: Decimal("1")},
        negative_weights={AreaCode.MATHEMATICS_STATISTICS: Decimal("0.8")},
        confidence=Confidence(value=Decimal("1"), answered_base=5, answered_adaptive=0),
    )


def test_reasons_use_actual_area_workload_and_source_names() -> None:
    curriculum: CurriculumResponse = _curriculum("explain")
    fingerprint = FingerprintBuilder().build_catalog((curriculum,))[0]
    profile = _profile()
    reasons = ExplanationBuilder().build(profile, fingerprint)

    assert reasons
    assert any(reason.kind == "positive" and reason.area is AreaCode.COMPUTER_SCIENCE_DATA for reason in reasons)
    assert any("Программирование" in reason.source_names for reason in reasons)
    assert all(reason.workload >= 0 for reason in reasons)
    assert all(reason.code.startswith(("subject:", "activity:", "anti:", "distinctive:", "neutral")) for reason in reasons)


def test_negative_reason_has_real_penalty_evidence() -> None:
    curriculum = _curriculum("negative")
    fingerprint = FingerprintBuilder().build_catalog((curriculum,))[0]
    profile = _profile()
    score = ScoringService().score(profile, fingerprint)
    reasons = ExplanationBuilder().build(profile, fingerprint)

    assert score.breakdown.anti_penalty >= 0
    negative = [reason for reason in reasons if reason.kind == "negative"]
    assert negative
    assert negative[0].impact <= 0
    assert negative[0].source_names
