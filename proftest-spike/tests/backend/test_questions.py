from __future__ import annotations

from proftest_spike.questions.bank import BASE_QUESTIONS
from proftest_spike.questions.entities import QuestionBlock, QuestionKind
from proftest_spike.questions.service import QuestionService


def test_base_bank_has_five_logical_blocks_and_scenario_options() -> None:
    blocks = {question.block for question in BASE_QUESTIONS}
    assert blocks == {QuestionBlock.INTERESTS, QuestionBlock.ACTIVITY, QuestionBlock.ANTI_INTERESTS, QuestionBlock.TRADEOFF}
    assert sum(question.kind is QuestionKind.MULTI_INTENSITY for question in BASE_QUESTIONS) == 1
    assert all("program:" not in option.label.lower() for question in BASE_QUESTIONS for option in question.options)
    assert all("data scientist" not in option.label.lower() for question in BASE_QUESTIONS for option in question.options)
    assert QuestionService().required_ids


def test_question_ids_and_option_ids_are_deterministic() -> None:
    first = [(question.id, tuple(option.id for option in question.options)) for question in BASE_QUESTIONS]
    second = [(question.id, tuple(option.id for option in question.options)) for question in QuestionService().list_base()]
    assert first == second
