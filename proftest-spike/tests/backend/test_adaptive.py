from __future__ import annotations

from decimal import Decimal

from proftest_spike.adaptive.entities import AdaptiveDimension, AdaptiveSelection
from proftest_spike.adaptive.question_factory import AdaptiveQuestionFactory
from proftest_spike.adaptive.selector import AdaptiveCandidate, AdaptiveQuestionSelector
from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode, ProgramFingerprint
from proftest_spike.profiling.profile_builder import UserProfileBuilder
from proftest_spike.questions.bank import BASE_QUESTIONS
from proftest_spike.questions.entities import AdaptiveAnswer, Answer, AnswerSet


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


def test_selector_uses_candidate_spread_not_static_question_order() -> None:
    candidates = (
        AdaptiveCandidate(
            _fingerprint(
                "a",
                {AreaCode.COMPUTER_SCIENCE_DATA: "0.80", AreaCode.PHYSICS_ASTRONOMY: "0.20"},
                {ActivityCode.SOFTWARE_CREATION: "0.80", ActivityCode.PHYSICAL_ENGINEERING: "0.20"},
            ),
            Decimal("90"),
        ),
        AdaptiveCandidate(
            _fingerprint(
                "b",
                {AreaCode.COMPUTER_SCIENCE_DATA: "0.10", AreaCode.PHYSICS_ASTRONOMY: "0.90"},
                {ActivityCode.SOFTWARE_CREATION: "0.10", ActivityCode.PHYSICAL_ENGINEERING: "0.90"},
            ),
            Decimal("80"),
        ),
    )
    selection = AdaptiveQuestionSelector().select(candidates)

    assert selection.status == "ready"
    assert len(selection.dimensions) == 2
    assert selection.dimensions[0].spread == max(item.spread for item in selection.dimensions)
    assert {item.kind for item in selection.dimensions} == {"area", "activity"}


def test_factory_creates_three_choices_from_selected_dimensions() -> None:
    selection = AdaptiveSelection(
        status="ready",
        candidate_count=2,
        top_candidate_count=2,
        dimensions=(
            AdaptiveDimension(code="area:computer_science_data", label="Компьютерные науки и данные", kind="area", spread=Decimal("0.8"), significance=Decimal("0.7")),
            AdaptiveDimension(code="activity:physical_engineering", label="Собирать и проверять физические решения", kind="activity", spread=Decimal("0.6"), significance=Decimal("0.5")),
        ),
    )
    question = AdaptiveQuestionFactory().create(selection)

    assert question is not None
    assert len(question.options) == 3
    assert question.options[0].id == "more_first"
    assert "program" not in question.prompt.lower()


def test_low_spread_candidates_are_skipped_explicitly() -> None:
    fingerprint = _fingerprint(
        "same",
        {AreaCode.COMPUTER_SCIENCE_DATA: "1"},
        {ActivityCode.SOFTWARE_CREATION: "1"},
    )
    selection = AdaptiveQuestionSelector().select((AdaptiveCandidate(fingerprint, Decimal("50")), AdaptiveCandidate(fingerprint, Decimal("49"))))

    assert selection.status == "skipped"
    assert selection.reason
    assert selection.question is None


def test_adaptive_choice_updates_only_declared_profile_dimensions() -> None:
    answers = tuple(
        Answer(question_id=question.id, option_id=question.options[0].id)
        for question in BASE_QUESTIONS
        if question.id != "anti_interest_areas"
    )
    profile = UserProfileBuilder(BASE_QUESTIONS).build(AnswerSet(answers=answers))
    answer = AdaptiveAnswer(
        question_id="adaptive:test",
        option_id="more_first",
        first_dimension="area:computer_science_data",
        second_dimension="activity:physical_engineering",
    )
    updated = UserProfileBuilder(BASE_QUESTIONS).apply_adaptive_answer(profile, answer)

    assert updated.preferred_subject_weights[AreaCode.COMPUTER_SCIENCE_DATA] > profile.preferred_subject_weights.get(AreaCode.COMPUTER_SCIENCE_DATA, Decimal("0"))
    assert updated.preferred_activity_weights == profile.preferred_activity_weights
    assert updated.confidence.answered_adaptive == 1


def test_identical_candidates_produce_identical_adaptive_selection() -> None:
    candidates = (
        AdaptiveCandidate(_fingerprint("a", {AreaCode.COMPUTER_SCIENCE_DATA: "0.5", AreaCode.PHYSICS_ASTRONOMY: "0.5"}, {ActivityCode.SOFTWARE_CREATION: "0.5", ActivityCode.PHYSICAL_ENGINEERING: "0.5"}), Decimal("50")),
        AdaptiveCandidate(_fingerprint("b", {AreaCode.COMPUTER_SCIENCE_DATA: "0.5", AreaCode.PHYSICS_ASTRONOMY: "0.5"}, {ActivityCode.SOFTWARE_CREATION: "0.5", ActivityCode.PHYSICAL_ENGINEERING: "0.5"}), Decimal("50")),
    )
    first = AdaptiveQuestionSelector().select(candidates)
    second = AdaptiveQuestionSelector().select(candidates)

    assert first == second
