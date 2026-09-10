"""Serializable UserProfile contracts."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode
from proftest_spike.questions.entities import AdaptiveAnswer


class ProfileModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)


class PreferenceDistribution(ProfileModel):
    axis: Literal["subject", "activity"]
    weights: dict[AreaCode | ActivityCode, Decimal]


class AntiInterest(ProfileModel):
    area: AreaCode
    intensity: Decimal = Field(strict=True, ge=Decimal("0"), le=Decimal("1"), max_digits=5, decimal_places=4)


class Confidence(ProfileModel):
    value: Decimal = Field(strict=True, ge=Decimal("0"), le=Decimal("1"), max_digits=5, decimal_places=4)
    answered_base: int = Field(strict=True, ge=0)
    answered_adaptive: int = Field(strict=True, ge=0)


class UserProfile(ProfileModel):
    interests: tuple[AreaCode, ...]
    activity_preferences: tuple[ActivityCode, ...]
    anti_interests: tuple[AntiInterest, ...]
    preferred_subject_weights: dict[AreaCode, Decimal]
    preferred_activity_weights: dict[ActivityCode, Decimal]
    negative_weights: dict[AreaCode, Decimal]
    confidence: Confidence
    adaptive_answers: tuple[AdaptiveAnswer, ...] = ()

    @model_validator(mode="after")
    def validate_distributions(self) -> Self:
        for name, weights in (
            ("preferred_subject_weights", self.preferred_subject_weights),
            ("preferred_activity_weights", self.preferred_activity_weights),
        ):
            if weights and abs(sum(weights.values(), Decimal("0")) - Decimal("1")) > Decimal("0.001"):
                raise ValueError(f"{name} must sum to one")
        return self


__all__ = ["AntiInterest", "Confidence", "PreferenceDistribution", "UserProfile"]
