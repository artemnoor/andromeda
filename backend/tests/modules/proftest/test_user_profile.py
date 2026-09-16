from __future__ import annotations

from decimal import Decimal

import pytest

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode
from andromeda.modules.proftest.contracts.public import Answer, AnswerSet, AnswerStatus
from andromeda.modules.proftest.services.profile_builder import UserProfileBuilder
from andromeda.modules.proftest.services.questionnaire import build_questionnaire, build_session_questionnaire


def test_answers_become_normalized_profile_with_separate_anti_interest() -> None:
    answer_set = AnswerSet(
        answers=(
            Answer(question_id="interest_free_day", option_ids=("software_tool",)),
            Answer(question_id="activity_build", option_ids=("system_scheme",)),
            Answer(question_id="anti_subjects", option_ids=("avoid_physics",), intensity=Decimal("0.9")),
        )
    )

    profile = UserProfileBuilder().build(answer_set, build_questionnaire().questions)

    assert profile.preferred_subject_weights[DisciplineAreaCode.COMPUTER_SCIENCE_DATA] == Decimal("1.0000")
    assert profile.preferred_activity_weights
    assert profile.negative_weights[DisciplineAreaCode.PHYSICS_ASTRONOMY] == Decimal("0.9")
    assert profile.anti_interests[0].intensity == Decimal("0.9")
    assert profile.confidence.answered_base == 3


def test_unknown_question_is_rejected_before_matching() -> None:
    with pytest.raises(ValueError, match="Unknown question"):
        UserProfileBuilder().build(AnswerSet(answers=(Answer(question_id="missing", option_ids=("option",)),)), build_questionnaire().questions)


def test_session_answers_keep_context_format_and_confidence_separate() -> None:
    questionnaire = build_session_questionnaire()
    answers = AnswerSet(
        answers=(
            Answer(question_id="context_goal", option_ids=("find_field",)),
            Answer(question_id="work_alone_team", option_ids=("solve_together",)),
            Answer(question_id="work_pace", option_ids=("fast_iterations",)),
            Answer(question_id="context_experience", status=AnswerStatus.UNCERTAIN),
            Answer(question_id="anti_load", option_ids=("high_load",)),
        )
    )

    profile = UserProfileBuilder().build(answers, questionnaire.questions)

    assert "exploration" in profile.decision_context
    assert "teamwork" in profile.format_preferences
    assert "iterative" in profile.format_preferences
    assert profile.load_tolerance == Decimal("0.9000")
    assert profile.confidence_by_dimension["context"] == Decimal("0.6250")
    assert profile.confidence_by_dimension["format"] == Decimal("1.0000")
