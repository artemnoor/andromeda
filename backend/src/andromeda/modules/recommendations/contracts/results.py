"""Output contracts for recommendation use cases."""

from __future__ import annotations

from pydantic import Field

from andromeda.modules.proftest.contracts.public import Recommendation, UserProfile
from andromeda.shared.contracts.base import ContractModel


class RecommendationResult(ContractModel):
    """Stable result envelope returned by the recommendation application service."""

    profile: UserProfile
    recommendations: tuple[Recommendation, ...] = Field(default_factory=tuple)


__all__ = ["RecommendationResult"]
