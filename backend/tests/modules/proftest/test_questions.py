from __future__ import annotations

from andromeda.modules.proftest.domain.entities import QuestionBlock
from andromeda.modules.proftest.contracts.public import QuestionComponentType
from andromeda.modules.proftest.services.questionnaire import build_questionnaire, build_session_questionnaire


def test_questionnaire_contains_separate_interest_activity_and_anti_interest_blocks() -> None:
    questionnaire = build_questionnaire()
    blocks = {question.block for question in questionnaire.questions}
    assert {QuestionBlock.INTERESTS, QuestionBlock.ACTIVITIES, QuestionBlock.ANTI_INTERESTS} <= blocks
    assert all("program:" not in option.id for question in questionnaire.questions for option in question.options)
    anti = next(question for question in questionnaire.questions if question.id == "anti_subjects")
    assert anti.multi_select is True
    assert anti.max_selected == 3


def test_session_questionnaire_is_versioned_deterministic_and_has_mechanics_budget() -> None:
    first = build_session_questionnaire()
    second = build_session_questionnaire()

    assert first == second
    assert first.question_set_version == "proftest-v2"
    assert len(first.questions) == 24
    assert {question.component_type for question in first.questions} >= {
        QuestionComponentType.CHIP_SELECT,
        QuestionComponentType.PAIR_CHOICE,
        QuestionComponentType.SCENARIO_CHOICE,
        QuestionComponentType.ANCHORED_SCALE,
        QuestionComponentType.MULTI_CHOICE,
    }
    scales = 0
    for question in first.questions:
        if question.component_type is QuestionComponentType.ANCHORED_SCALE:
            scales += 1
            assert scales <= 3
        else:
            scales = 0
        assert question.order >= 1
        assert question.declared_dimensions
