from __future__ import annotations

from decimal import Decimal

import pytest

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode
from andromeda.modules.proftest.contracts.public import Answer, AnswerSet
from andromeda.modules.proftest.services.profile_builder import UserProfileBuilder
from andromeda.modules.proftest.services.questionnaire import build_questionnaire


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
