"""Strict HTTP schemas for the standalone recommendation use case."""

from __future__ import annotations

from pydantic import Field

from andromeda.modules.recommendations.contracts.public import AdaptiveAnswer, AntiInterest, Confidence, RecommendationRequest as RecommendationRequestContract
from andromeda.modules.recommendations.contracts.public import RecommendationResult, UserProfile

from .common import ApiModel
from .proftest import RecommendationResponse, UserProfileResponse, profile_response, recommendation_response


class RecommendationRequest(ApiModel):
    profile: UserProfileResponse
    limit: int = Field(default=10, strict=True, ge=1, le=20)

    def to_contract(self) -> RecommendationRequestContract:
        return RecommendationRequestContract(
            profile=UserProfile(
                version=self.profile.version,
                interests=tuple(self.profile.interests),
                activity_preferences=tuple(self.profile.activity_preferences),
                anti_interests=tuple(AntiInterest(area=item.area, intensity=item.intensity) for item in self.profile.anti_interests),
                preferred_subject_weights=self.profile.preferred_subject_weights,
                preferred_activity_weights=self.profile.preferred_activity_weights,
                negative_weights=self.profile.negative_weights,
                confidence=Confidence(**self.profile.confidence.model_dump()),
                adaptive_answers=tuple(AdaptiveAnswer(**answer.model_dump()) for answer in self.profile.adaptive_answers),
            ),
            limit=self.limit,
        )


class RecommendationsResponse(ApiModel):
    profile: UserProfileResponse
    recommendations: tuple[RecommendationResponse, ...]


def recommendations_response(result: RecommendationResult) -> RecommendationsResponse:
    return RecommendationsResponse(profile=profile_response(result.profile), recommendations=tuple(recommendation_response(item) for item in result.recommendations))


__all__ = ["RecommendationRequest", "RecommendationsResponse", "recommendations_response"]
