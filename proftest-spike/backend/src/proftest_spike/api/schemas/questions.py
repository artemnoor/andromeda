"""Frontend-safe question schemas without scoring metadata."""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from proftest_spike.questions.entities import AdaptiveAnswer, Answer, AnswerSet, Question

from .common import ApiModel


class AnswerOptionResponse(ApiModel):
    id: str = Field(min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=512)
    description: str = Field(min_length=1, max_length=512)
    requires_intensity: bool


class QuestionResponse(ApiModel):
    id: str = Field(min_length=1, max_length=128)
    block: str = Field(min_length=1, max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1, max_length=1_000)
    helper_text: str = Field(min_length=1, max_length=512)
    required: bool
    options: tuple[AnswerOptionResponse, ...]
    min_selections: int = Field(strict=True, ge=0, le=22)
    max_selections: int = Field(strict=True, ge=1, le=22)


class AnswerPayload(ApiModel):
    question_id: str = Field(min_length=1, max_length=128)
    option_id: str = Field(min_length=1, max_length=128)
    intensity: Decimal | None = Field(default=None, strict=False, ge=0, le=1, max_digits=5, decimal_places=4)


class AdaptiveAnswerPayload(ApiModel):
    question_id: str = Field(min_length=1, max_length=256)
    option_id: str = Field(min_length=1, max_length=128)
    first_dimension: str = Field(min_length=3, max_length=128)
    second_dimension: str = Field(min_length=3, max_length=128)


class TestAnswersRequest(ApiModel):
    answers: list[AnswerPayload]
    adaptive_answers: list[AdaptiveAnswerPayload] = Field(default_factory=list)


def question_response(question: Question) -> QuestionResponse:
    return QuestionResponse(
        id=question.id,
        block=question.block.value,
        kind=question.kind.value,
        title=question.title,
        prompt=question.prompt,
        helper_text=question.helper_text,
        required=question.required,
        options=tuple(
            AnswerOptionResponse(
                id=option.id,
                label=option.label,
                description=option.description,
                requires_intensity=option.requires_intensity,
            )
            for option in question.options
        ),
        min_selections=question.min_selections,
        max_selections=question.max_selections,
    )


def to_answer_set(payload: TestAnswersRequest) -> AnswerSet:
    return AnswerSet(
        answers=tuple(Answer.model_validate(item.model_dump()) for item in payload.answers),
        adaptive_answers=tuple(AdaptiveAnswer.model_validate(item.model_dump()) for item in payload.adaptive_answers),
    )


__all__ = ["AdaptiveAnswerPayload", "AnswerOptionResponse", "AnswerPayload", "QuestionResponse", "TestAnswersRequest", "question_response", "to_answer_set"]
