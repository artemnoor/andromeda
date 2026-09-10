from __future__ import annotations

from andromeda.modules.proftest.domain.entities import QuestionBlock
from andromeda.modules.proftest.services.questionnaire import build_questionnaire


def test_questionnaire_contains_separate_interest_activity_and_anti_interest_blocks() -> None:
    questionnaire = build_questionnaire()
    blocks = {question.block for question in questionnaire.questions}
    assert {QuestionBlock.INTERESTS, QuestionBlock.ACTIVITIES, QuestionBlock.ANTI_INTERESTS} <= blocks
    assert all("program:" not in option.id for question in questionnaire.questions for option in question.options)
    anti = next(question for question in questionnaire.questions if question.id == "anti_subjects")
    assert anti.multi_select is True
    assert anti.max_selected == 3
