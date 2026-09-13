"""Question bank access service."""

from __future__ import annotations

from collections.abc import Iterable

from .bank import BASE_QUESTIONS
from .entities import Question


class QuestionService:
    def __init__(self, questions: Iterable[Question] = BASE_QUESTIONS) -> None:
        self._questions = tuple(questions)
        self._by_id = {question.id: question for question in self._questions}
        if len(self._by_id) != len(self._questions):
            raise ValueError("question ids must be unique")

    def list_base(self) -> tuple[Question, ...]:
        return self._questions

    def get(self, question_id: str) -> Question | None:
        return self._by_id.get(question_id)

    @property
    def required_ids(self) -> frozenset[str]:
        return frozenset(question.id for question in self._questions if question.required)


__all__ = ["QuestionService"]
