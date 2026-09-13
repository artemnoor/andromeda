"""Questionnaire-level domain contract."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel

from .entities import Question


class Questionnaire(ContractModel):
    version: Literal[1] = 1
    questions: tuple[Question, ...] = Field(min_length=1)

    @classmethod
    def from_questions(cls, questions: tuple[Question, ...]) -> "Questionnaire":
        return cls(questions=questions)


__all__ = ["Questionnaire"]
