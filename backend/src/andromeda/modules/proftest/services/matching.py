"""Deterministic Content Fit scoring over public proftest contracts."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import logging

from ..contracts.public import ActivityCode, MatchScore, ProgramFingerprint, ScoreBreakdown, UserProfile
from ..domain.signals import ACTIVITY_SIGNAL_WEIGHTS
from ..domain.values import ZERO


logger = logging.getLogger("andromeda.proftest.matching")


class MatchingService:
    """Calculate a bounded, explainable score from a profile and fingerprint."""

    def score(self, profile: UserProfile, fingerprint: ProgramFingerprint) -> MatchScore:
        subject_fit = self._subject_fit(profile, fingerprint)
        activity_fit = self._activity_fit(profile, fingerprint)
        distinctive_fit = self._distinctive_fit(profile, fingerprint)
        anti_penalty = self._anti_penalty(profile, fingerprint)
        raw = Decimal("0.55") * subject_fit + Decimal("0.25") * activity_fit + Decimal("0.20") * distinctive_fit - Decimal("0.60") * anti_penalty
        result = MatchScore(
            program_id=fingerprint.program_id,
            program_code=fingerprint.program_code,
            content_fit=_round_clamp(raw),
            breakdown=ScoreBreakdown(
                subject_fit=subject_fit,
                activity_fit=activity_fit,
                distinctive_fit=distinctive_fit,
                anti_penalty=anti_penalty,
                raw_content_fit=raw,
            ),
        )
        logger.debug("score_calculated program_id=%s content_fit=%d anti_penalty=%.2f", _safe_id(fingerprint.program_id), result.content_fit, anti_penalty)
        return result

    @staticmethod
    def _subject_fit(profile: UserProfile, fingerprint: ProgramFingerprint) -> Decimal:
        if not profile.preferred_subject_weights:
            return Decimal("50")
        return Decimal("100") * sum((fingerprint.area_share.get(area, ZERO) * weight for area, weight in profile.preferred_subject_weights.items()), ZERO)

    @staticmethod
    def _activity_fit(profile: UserProfile, fingerprint: ProgramFingerprint) -> Decimal:
        if not profile.preferred_activity_weights:
            return Decimal("50")
        return Decimal("100") * sum((fingerprint.activity_signals.get(activity, ZERO) * weight for activity, weight in profile.preferred_activity_weights.items()), ZERO)

    @staticmethod
    def _distinctive_fit(profile: UserProfile, fingerprint: ProgramFingerprint) -> Decimal:
        if not fingerprint.distinctive_subjects or (not profile.preferred_subject_weights and not profile.preferred_activity_weights):
            return Decimal("50")
        total_weight = sum((subject.distinctiveness for subject in fingerprint.distinctive_subjects), ZERO)
        if total_weight <= ZERO:
            return Decimal("50")
        overlap = ZERO
        for subject in fingerprint.distinctive_subjects:
            subject_affinity = profile.preferred_subject_weights.get(subject.primary_area, ZERO)
            activity_affinity = sum(
                (profile.preferred_activity_weights.get(activity, ZERO) * weight for activity, weight in ACTIVITY_SIGNAL_WEIGHTS[subject.primary_area].items()),
                ZERO,
            )
            overlap += subject.distinctiveness * (Decimal("0.70") * subject_affinity + Decimal("0.30") * activity_affinity)
        return Decimal("100") * overlap / total_weight

    @staticmethod
    def _anti_penalty(profile: UserProfile, fingerprint: ProgramFingerprint) -> Decimal:
        if not profile.negative_weights:
            return ZERO
        return Decimal("100") * sum((fingerprint.area_share.get(area, ZERO) * weight for area, weight in profile.negative_weights.items()), ZERO)


def _round_clamp(value: Decimal) -> int:
    rounded = int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(0, min(100, rounded))


def _safe_id(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ")[:128]


__all__ = ["MatchingService"]
