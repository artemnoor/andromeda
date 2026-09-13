"""Stable public surface of the recommendation module."""

from andromeda.modules.proftest.contracts.public import (
    ActivityCode,
    AdaptiveAnswer,
    AntiInterest,
    Confidence,
    MatchReason,
    MatchScore,
    ProgramFingerprint,
    Recommendation,
    ReasonKind,
    ScoreBreakdown,
    UserProfile,
)

from .requests import RecommendationRequest
from .results import RecommendationResult

__all__ = [
    "ActivityCode",
    "AdaptiveAnswer",
    "AntiInterest",
    "Confidence",
    "MatchReason",
    "MatchScore",
    "ProgramFingerprint",
    "Recommendation",
    "ReasonKind",
    "RecommendationRequest",
    "RecommendationResult",
    "ScoreBreakdown",
    "UserProfile",
]
