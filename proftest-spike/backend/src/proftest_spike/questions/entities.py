"""Typed question and answer contracts used before profile construction."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode


class QuestionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)


class QuestionBlock(StrEnum):
    INTERESTS = "interests"
    ACTIVITY = "activity"
    ANTI_INTERESTS = "anti_interests"
    TRADEOFF = "tradeoff"
    ADAPTIVE = "adaptive"


class QuestionKind(StrEnum):
    SINGLE = "single"
    MULTI_INTENSITY = "multi_intensity"


class AnswerOption(QuestionModel):
    id: str = Field(min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=512)
    description: str = Field(min_length=1, max_length=512)
    subject_weights: dict[AreaCode, Decimal] = Field(default_factory=dict)
    activity_weights: dict[ActivityCode, Decimal] = Field(default_factory=dict)
    anti_area: AreaCode | None = None
    requires_intensity: bool = False


class Question(QuestionModel):
    id: str = Field(min_length=1, max_length=128)
    block: QuestionBlock
    kind: QuestionKind
    title: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1, max_length=1_000)
    helper_text: str = Field(min_length=1, max_length=512)
    required: bool = True
    options: tuple[AnswerOption, ...] = Field(min_length=2)
    min_selections: int = Field(strict=True, ge=0, le=22)
    max_selections: int = Field(strict=True, ge=1, le=22)

    @model_validator(mode="after")
    def validate_selection_bounds(self) -> Self:
        if self.kind is QuestionKind.SINGLE and self.min_selections < 1:
            raise ValueError("single questions require at least one selection")
        if self.min_selections > self.max_selections:
            raise ValueError("min_selections must not exceed max_selections")
        if self.max_selections > len(self.options):
            raise ValueError("max_selections must not exceed option count")
        return self


class Answer(QuestionModel):
    question_id: str = Field(min_length=1, max_length=128)
    option_id: str = Field(min_length=1, max_length=128)
    intensity: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("1"), max_digits=5, decimal_places=4)


class AdaptiveAnswer(QuestionModel):
    question_id: str = Field(min_length=1, max_length=256)
    option_id: str = Field(min_length=1, max_length=128)
    first_dimension: str = Field(min_length=3, max_length=128)
    second_dimension: str = Field(min_length=3, max_length=128)


class AnswerSet(QuestionModel):
    answers: tuple[Answer, ...] = ()
    adaptive_answers: tuple[AdaptiveAnswer, ...] = ()


__all__ = [
    "AdaptiveAnswer",
    "Answer",
    "AnswerOption",
    "AnswerSet",
    "Question",
    "QuestionBlock",
    "QuestionKind",
]
