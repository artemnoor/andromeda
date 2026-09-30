"""Typed admission-planning profile collected by the initial questionnaire."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, Self

from pydantic import Field, model_validator

from andromeda.modules.admission_benefits.contracts.public import OlympiadResultType
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import EducationYear, NonEmptyText, OlympiadId, OlympiadProfileId


class ApplicantExamPlan(ContractModel):
    subject: NonEmptyText
    score: Decimal | None = Field(default=None, strict=True, ge=Decimal("0"), le=Decimal("100"), max_digits=5, decimal_places=2)
    score_certainty: Literal["known", "estimated"] | None = None

    @model_validator(mode="after")
    def validate_score_certainty(self) -> Self:
        if (self.score is None) != (self.score_certainty is None):
            raise ValueError("score and certainty must be supplied together")
        return self


class ApplicantOlympiadResult(ContractModel):
    olympiad_id: OlympiadId
    olympiad_profile_id: OlympiadProfileId | None = None
    result_type: OlympiadResultType | None = None
    result_year: EducationYear | None = None
    grade_or_class: NonEmptyText | None = None


class ApplicantOnboardingProfile(ContractModel):
    """User-reported intake facts; no claim of official verification is made."""

    version: Literal[1] = 1
    grade: Literal[8, 9, 10, 11]
    planned_ege_subjects: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=12)
    exam_scores: tuple[ApplicantExamPlan, ...] = Field(default=(), max_length=12)
    olympiad_results: tuple[ApplicantOlympiadResult, ...] = Field(default=(), max_length=30)
    individual_achievements: tuple[NonEmptyText, ...] = Field(default=(), max_length=12)
    quota_preference: Literal["special", "separate", "unsure", "none"]

    @model_validator(mode="after")
    def validate_profile(self) -> Self:
        normalized_subjects = tuple(item.casefold() for item in self.planned_ege_subjects)
        if len(normalized_subjects) != len(set(normalized_subjects)):
            raise ValueError("planned EGE subjects must be unique")
        if "русский язык" not in normalized_subjects:
            raise ValueError("Russian language must be included in planned EGE subjects")
        score_subjects = tuple(item.subject.casefold() for item in self.exam_scores)
        if len(score_subjects) != len(set(score_subjects)) or not set(score_subjects).issubset(set(normalized_subjects)):
            raise ValueError("exam scores must refer to unique planned subjects")
        olympiad_keys = tuple((item.olympiad_id, item.olympiad_profile_id, item.result_year, item.result_type) for item in self.olympiad_results)
        if len(olympiad_keys) != len(set(olympiad_keys)):
            raise ValueError("olympiad results must be unique")
        return self


__all__ = ["ApplicantExamPlan", "ApplicantOnboardingProfile", "ApplicantOlympiadResult"]
