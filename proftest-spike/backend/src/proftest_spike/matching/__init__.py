"""Deterministic, explainable program matching."""

from .entities import MatchScore, Metric, Recommendation, ScoreBreakdown
from .ranking import RankingService
from .scoring import ScoringService

__all__ = ["MatchScore", "Metric", "Recommendation", "RankingService", "ScoreBreakdown", "ScoringService"]
