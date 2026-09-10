from __future__ import annotations

from decimal import Decimal

import pytest

from proftest_spike.domain.areas import AreaCode
from proftest_spike.profiling.profile_builder import ProfileValidationError, UserProfileBuilder
from proftest_spike.questions.bank import BASE_QUESTIONS
from proftest_spike.questions.entities import Answer, AnswerSet


def _complete_answers(*, strong_physics_anti: bool = False) -> AnswerSet:
    answers: list[Answer] = []
    for question in BASE_QUESTIONS:
        if question.id == "anti_interest_areas":
            if strong_physics_anti:
                answers.append(Answer(question_id=question.id, option_id="anti_physics", intensity=Decimal("0.95")))
            continue
        answers.append(Answer(question_id=question.id, option_id=question.options[0].id))
    return AnswerSet(answers=tuple(answers))


def test_answers_become_normalized_profile_with_separate_axes() -> None:
    profile = UserProfileBuilder(BASE_QUESTIONS).build(_complete_answers())

    assert profile.preferred_subject_weights
    assert profile.preferred_activity_weights
    assert sum(profile.preferred_subject_weights.values(), Decimal("0")) == Decimal("1.0000")
    assert sum(profile.preferred_activity_weights.values(), Decimal("0")) == Decimal("1.0000")
    assert profile.negative_weights == {}
    assert profile.confidence.answered_base == 5


def test_strong_anti_interest_is_an_explicit_negative_weight() -> None:
    profile = UserProfileBuilder(BASE_QUESTIONS).build(_complete_answers(strong_physics_anti=True))

    assert profile.anti_interests[0].area is AreaCode.PHYSICS_ASTRONOMY
    assert profile.negative_weights[AreaCode.PHYSICS_ASTRONOMY] == Decimal("0.9500")


def test_empty_profile_is_neutral_and_serializable() -> None:
    profile = UserProfileBuilder(BASE_QUESTIONS).build(AnswerSet())

    assert profile.preferred_subject_weights == {}
    assert profile.preferred_activity_weights == {}
    assert profile.model_dump_json() == UserProfileBuilder(BASE_QUESTIONS).build(AnswerSet()).model_dump_json()


@pytest.mark.parametrize(
    "answers",
    [
        (Answer(question_id="unknown", option_id="x"),),
        (Answer(question_id="interest_scenario_1", option_id="unknown"),),
        (Answer(question_id="anti_interest_areas", option_id="anti_physics"),),
        (Answer(question_id="interest_scenario_1", option_id="prototype_logic"), Answer(question_id="interest_scenario_1", option_id="find_patterns")),
    ],
)
def test_invalid_answer_sets_are_rejected(answers: tuple[Answer, ...]) -> None:
    with pytest.raises(ProfileValidationError):
        UserProfileBuilder(BASE_QUESTIONS).build(AnswerSet(answers=answers))


def test_same_answers_produce_identical_profiles() -> None:
    first = UserProfileBuilder(BASE_QUESTIONS).build(_complete_answers())
    second = UserProfileBuilder(BASE_QUESTIONS).build(_complete_answers())

    assert first == second
    assert first.model_dump_json() == second.model_dump_json()
