"""Pure proftest entities and typed value objects."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode, DisciplineAreaWeight
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.enums import AssessmentType
from andromeda.shared.contracts.ids import Credits, HourCount, NonEmptyText, ProgramCode, ProgramId, Semester, ShortText

from .values import ONE, ZERO


class ActivityCode(StrEnum):
    """Activity dimensions used by deterministic profile matching."""

    ANALYTICAL = "analytical"
    SOFTWARE_CREATION = "software_creation"
    SYSTEM_DESIGN = "system_design"
    RESEARCH = "research"
    PHYSICAL_ENGINEERING = "physical_engineering"
    COMMUNICATION = "communication"
    CREATIVE = "creative"
    BUSINESS = "business"
    DATA = "data"


class QuestionBlock(StrEnum):
    INTERESTS = "interests"
    ACTIVITIES = "activities"
    ANTI_INTERESTS = "anti_interests"
    ADAPTIVE = "adaptive"


class QuestionOption(ContractModel):
    id: ShortText
    label: NonEmptyText
    subject_weights: dict[DisciplineAreaCode, Decimal] = Field(default_factory=dict)
    activity_weights: dict[ActivityCode, Decimal] = Field(default_factory=dict)
    anti_interest_weights: dict[DisciplineAreaCode, Decimal] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_weights(self) -> Self:
        for name, weights in (
            ("subject_weights", self.subject_weights),
            ("activity_weights", self.activity_weights),
            ("anti_interest_weights", self.anti_interest_weights),
        ):
            if any(weight < ZERO or weight > ONE for weight in weights.values()):
                raise ValueError(f"{name} values must be between zero and one")
        return self


class Question(ContractModel):
    id: ShortText
    block: QuestionBlock
    prompt: NonEmptyText
    options: tuple[QuestionOption, ...] = Field(min_length=2, max_length=6)
    required: bool = True
    adaptive: bool = False
    multi_select: bool = False
    max_selected: int = Field(default=1, strict=True, ge=1, le=6)

    @model_validator(mode="after")
    def validate_options(self) -> Self:
        option_ids = tuple(option.id for option in self.options)
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("question options must have unique ids")
        if self.adaptive and self.block is not QuestionBlock.ADAPTIVE:
            raise ValueError("adaptive questions must use the adaptive block")
        if not self.multi_select and self.max_selected != 1:
            raise ValueError("single-select questions must allow one option")
        return self


class Answer(ContractModel):
    question_id: ShortText
    option_ids: tuple[ShortText, ...] = Field(min_length=1, max_length=6)
    intensity: Decimal | None = Field(default=None, strict=True, ge=ZERO, le=ONE, max_digits=5, decimal_places=4)

    @model_validator(mode="after")
    def validate_option_ids(self) -> Self:
        if len(self.option_ids) != len(set(self.option_ids)):
            raise ValueError("answer option ids must be unique")
        return self


class AdaptiveAnswer(ContractModel):
    question_id: ShortText
    option_id: ShortText
    dimension: ShortText


class AnswerSet(ContractModel):
    answers: tuple[Answer, ...] = ()
    adaptive_answers: tuple[AdaptiveAnswer, ...] = ()

    @model_validator(mode="after")
    def validate_questions(self) -> Self:
        question_ids = tuple(answer.question_id for answer in self.answers)
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("answer set cannot contain duplicate questions")
        adaptive_ids = tuple(answer.question_id for answer in self.adaptive_answers)
        if len(adaptive_ids) != len(set(adaptive_ids)):
            raise ValueError("answer set cannot contain duplicate adaptive questions")
        return self


class AntiInterest(ContractModel):
    area: DisciplineAreaCode
    intensity: Decimal = Field(strict=True, ge=ZERO, le=ONE, max_digits=5, decimal_places=4)


class Confidence(ContractModel):
    value: Decimal = Field(strict=True, ge=ZERO, le=ONE, max_digits=5, decimal_places=4)
    answered_base: int = Field(strict=True, ge=0)
    answered_adaptive: int = Field(strict=True, ge=0)


class UserProfile(ContractModel):
    """Stable public representation of a user's educational-content preferences."""

    version: Literal[1] = 1
    interests: tuple[DisciplineAreaCode, ...] = ()
    activity_preferences: tuple[ActivityCode, ...] = ()
    anti_interests: tuple[AntiInterest, ...] = ()
    preferred_subject_weights: dict[DisciplineAreaCode, Decimal] = Field(default_factory=dict)
    preferred_activity_weights: dict[ActivityCode, Decimal] = Field(default_factory=dict)
    negative_weights: dict[DisciplineAreaCode, Decimal] = Field(default_factory=dict)
    confidence: Confidence = Confidence(value=ZERO, answered_base=0, answered_adaptive=0)
    adaptive_answers: tuple[AdaptiveAnswer, ...] = ()

    @model_validator(mode="after")
    def validate_distributions(self) -> Self:
        for name, weights in (
            ("preferred_subject_weights", self.preferred_subject_weights),
            ("preferred_activity_weights", self.preferred_activity_weights),
            ("negative_weights", self.negative_weights),
        ):
            if any(weight < ZERO or weight > ONE for weight in weights.values()):
                raise ValueError(f"{name} values must be between zero and one")
        for name, weights in (
            ("preferred_subject_weights", self.preferred_subject_weights),
            ("preferred_activity_weights", self.preferred_activity_weights),
        ):
            if weights and abs(sum(weights.values(), ZERO) - ONE) > Decimal("0.001"):
                raise ValueError(f"{name} must sum to one")
        areas = tuple(item.area for item in self.anti_interests)
        if len(areas) != len(set(areas)):
            raise ValueError("anti_interests must contain unique areas")
        return self


class CurriculumEvidence(ContractModel):
    source_name: NonEmptyText
    normalized_name: ShortText
    hours: HourCount
    credits: Credits | None = None
    semester: Semester | None = None
    subject_group: ShortText
    assessment_types: tuple[AssessmentType, ...] | None = None
    workload: Decimal = Field(strict=True, ge=ZERO)
    area_weights: tuple[DisciplineAreaWeight, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_area_weights(self) -> Self:
        if sum((weight.weight for weight in self.area_weights), ZERO) != ONE:
            raise ValueError("evidence area weights must sum to one")
        return self


class DistinctiveSubject(ContractModel):
    source_name: NonEmptyText
    normalized_name: ShortText
    primary_area: DisciplineAreaCode
    workload: Decimal = Field(strict=True, ge=ZERO)
    share: Decimal = Field(strict=True, ge=ZERO, le=ONE, max_digits=7, decimal_places=4)
    rarity: Decimal = Field(strict=True, ge=ZERO, le=ONE, max_digits=7, decimal_places=4)
    distinctiveness: Decimal = Field(strict=True, ge=ZERO, le=ONE, max_digits=7, decimal_places=4)


class ProgramFingerprint(ContractModel):
    program_id: ProgramId
    program_code: ProgramCode
    program_name: NonEmptyText
    basis: Literal["hours", "credits"]
    total_hours: int = Field(strict=True, ge=0)
    total_credits: Decimal = Field(strict=True, ge=ZERO)
    total_workload: Decimal = Field(strict=True, ge=ZERO)
    area_hours: dict[DisciplineAreaCode, Decimal] = Field(default_factory=dict)
    area_share: dict[DisciplineAreaCode, Decimal] = Field(default_factory=dict)
    subject_group_hours: dict[ShortText, Decimal] = Field(default_factory=dict)
    subject_group_share: dict[ShortText, Decimal] = Field(default_factory=dict)
    semester_distribution: dict[str, Decimal] = Field(default_factory=dict)
    activity_signals: dict[ActivityCode, Decimal] = Field(default_factory=dict)
    evidence: tuple[CurriculumEvidence, ...] = ()
    distinctive_subjects: tuple[DistinctiveSubject, ...] = ()

    @model_validator(mode="after")
    def validate_vectors(self) -> Self:
        if self.total_workload > ZERO:
            for name, vector in (
                ("area_share", self.area_share),
                ("subject_group_share", self.subject_group_share),
                ("semester_distribution", self.semester_distribution),
                ("activity_signals", self.activity_signals),
            ):
                if not vector or abs(sum(vector.values(), ZERO) - ONE) > Decimal("0.001"):
                    raise ValueError(f"{name} must sum to one for a non-empty fingerprint")
        if self.basis == "hours" and self.total_workload != Decimal(self.total_hours):
            raise ValueError("hours basis must use total_hours as total_workload")
        if self.basis == "credits" and self.total_workload != self.total_credits:
            raise ValueError("credits basis must use total_credits as total_workload")
        return self


__all__ = [
    "ActivityCode",
    "AdaptiveAnswer",
    "Answer",
    "AnswerSet",
    "AntiInterest",
    "Confidence",
    "CurriculumEvidence",
    "DistinctiveSubject",
    "ONE",
    "ProgramFingerprint",
    "Question",
    "QuestionBlock",
    "QuestionOption",
    "UserProfile",
    "ZERO",
]
