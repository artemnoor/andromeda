"""Stable ranking over scored fingerprints."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from proftest_spike.program_fingerprints.entities import ProgramFingerprint
from proftest_spike.profiling.entities import UserProfile

from .entities import MatchScore
from .scoring import ScoringService

logger = logging.getLogger("proftest_spike.matching")


class RankingService:
    def __init__(self, scorer: ScoringService | None = None) -> None:
        self._scorer = scorer or ScoringService()

    def rank(self, profile: UserProfile, fingerprints: Iterable[ProgramFingerprint], *, limit: int = 10) -> tuple[tuple[ProgramFingerprint, MatchScore], ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        scored = tuple((fingerprint, self._scorer.score(profile, fingerprint)) for fingerprint in fingerprints)
        ordered = tuple(
            sorted(
                scored,
                key=lambda item: (-item[1].content_fit, -item[1].breakdown.subject_fit, item[0].program_code),
            )[:limit]
        )
        if not ordered:
            logger.warning("ranking_empty")
        else:
            logger.info(
                "ranking_complete catalog_size=%d result_count=%d top_fit=%d bottom_fit=%d",
                len(scored),
                len(ordered),
                ordered[0][1].content_fit,
                ordered[-1][1].content_fit,
            )
        return ordered


__all__ = ["RankingService"]
