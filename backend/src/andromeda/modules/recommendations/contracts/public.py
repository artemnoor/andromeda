"""Stable public surface of the recommendation module."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

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

from ..domain.entities import RankedFingerprint
from .requests import RecommendationRequest
from .results import RecommendationResult


class ProgramFingerprintReader(Protocol):
    """Read canonical, curriculum-backed fingerprints without storage details."""

    def list_fingerprints(self) -> tuple[ProgramFingerprint, ...]: ...


RecommendationCatalogReader = ProgramFingerprintReader


class RecommendationServicePort(Protocol):
    """Application boundary used by consumers of recommendation orchestration."""

    def rank_fingerprints(
        self,
        profile: UserProfile,
        fingerprints: Iterable[ProgramFingerprint],
        *,
        limit: int | None = None,
    ) -> tuple[RankedFingerprint, ...]: ...

    def recommend_from_fingerprints(
        self,
        request: RecommendationRequest,
        fingerprints: Iterable[ProgramFingerprint],
    ) -> RecommendationResult: ...


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
    "ProgramFingerprintReader",
    "RecommendationCatalogReader",
    "RecommendationServicePort",
    "RankedFingerprint",
    "ScoreBreakdown",
    "UserProfile",
]
