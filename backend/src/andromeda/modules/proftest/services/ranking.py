"""Stable ranking over scored program fingerprints."""

from __future__ import annotations

from collections.abc import Iterable
import logging

from ..contracts.public import MatchScore, ProgramFingerprint, UserProfile
from .matching import MatchingService


logger = logging.getLogger("andromeda.proftest.matching")


class RankingService:
    def __init__(self, scorer: MatchingService | None = None) -> None:
        self._scorer = scorer or MatchingService()

    def rank(self, profile: UserProfile, fingerprints: Iterable[ProgramFingerprint], *, limit: int = 10) -> tuple[tuple[ProgramFingerprint, MatchScore], ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        scored = tuple((fingerprint, self._scorer.score(profile, fingerprint)) for fingerprint in fingerprints)
        ordered = tuple(sorted(scored, key=lambda item: (-item[1].content_fit, -item[1].breakdown.subject_fit, item[0].program_code))[:limit])
        if not ordered:
            logger.warning("ranking_empty")
        else:
            logger.info("ranking_complete catalog_size=%d result_count=%d top_fit=%d bottom_fit=%d", len(scored), len(ordered), ordered[0][1].content_fit, ordered[-1][1].content_fit)
        return ordered


__all__ = ["RankingService"]
