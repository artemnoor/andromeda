from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode
from andromeda.modules.proftest.contracts.public import ActivityCode, AdaptiveAnswer, AdaptiveStatus, AnswerSet, MatchScore, ProgramFingerprint, ProftestAnswerSession, ScoreBreakdown, UserProfile
from andromeda.modules.proftest.services.adaptive import AdaptiveCandidate, AdaptiveQuestionFactory, AdaptiveQuestionSelector
from andromeda.modules.proftest.services.questionnaire import build_session_questionnaire
from andromeda.modules.proftest.services.session import ProftestSessionService
from andromeda.modules.recommendations.domain.entities import RankedFingerprint


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


def test_session_rebuilds_ranking_with_adaptive_answers() -> None:
    candidates = (
        AdaptiveCandidate(_fingerprint("02", "0.8", "0.2"), Decimal("80")),
        AdaptiveCandidate(_fingerprint("12", "0.2", "0.8"), Decimal("79")),
    )
    initial_selection = AdaptiveQuestionSelector().select(candidates)
    adaptive_question = AdaptiveQuestionFactory().create(initial_selection)
    assert adaptive_question is not None

    class Catalog:
        def list_fingerprints(self) -> tuple[ProgramFingerprint, ...]:
            return tuple(item.fingerprint for item in candidates)

    class Recommendations:
        def __init__(self) -> None:
            self.profiles: list[UserProfile] = []

        def rank_fingerprints(self, profile: UserProfile, fingerprints: tuple[ProgramFingerprint, ...], *, limit: int | None = None) -> tuple[RankedFingerprint, ...]:
            self.profiles.append(profile)
            return tuple(
                RankedFingerprint(
                    fingerprint=fingerprint,
                    score=MatchScore(
                        program_id=fingerprint.program_id,
                        program_code=fingerprint.program_code,
                        content_fit=80,
                        breakdown=ScoreBreakdown(subject_fit=Decimal("80"), activity_fit=Decimal("80"), distinctive_fit=Decimal("80"), anti_penalty=Decimal("0"), raw_content_fit=Decimal("80")),
                    ),
                )
                for fingerprint in fingerprints
            )[:limit]

    recommendations = Recommendations()
    service = ProftestSessionService(Catalog(), recommendations, object())
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    session = ProftestAnswerSession(
        session_id="proftest-session:" + "a" * 32,
        question_set_version="proftest-v2",
        answer_set=AnswerSet(
            adaptive_answers=(AdaptiveAnswer(question_id=adaptive_question.id, option_id=adaptive_question.options[0].id, dimension=adaptive_question.declared_dimensions[0]),),
        ),
        adaptive_questions=(adaptive_question,),
        cursor=24,
        interaction_count=25,
        current_question_id=adaptive_question.id,
        revision=1,
        created_at=now,
        updated_at=now,
        expires_at=now,
    )

    selection = service._selection(session, build_session_questionnaire().questions)

    assert recommendations.profiles
    assert recommendations.profiles[-1].confidence_by_dimension[adaptive_question.declared_dimensions[0]] == Decimal("1")
    assert selection.status is AdaptiveStatus.SKIPPED
