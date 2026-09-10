"""Select adaptive dimensions from measurable candidate spread."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Iterable, Literal

from proftest_spike.domain.areas import AREA_LABELS, AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode, ProgramFingerprint

from .entities import AdaptiveDimension, AdaptiveSelection

logger = logging.getLogger("proftest_spike.adaptive")


@dataclass(frozen=True, slots=True)
class AdaptiveCandidate:
    fingerprint: ProgramFingerprint
    score: Decimal


class AdaptiveQuestionSelector:
    """Find the two most informative actual curriculum dimensions."""

    def __init__(self, *, top_limit: int = 10, min_spread: Decimal = Decimal("0.08")) -> None:
        self._top_limit = top_limit
        self._min_spread = min_spread

    def select(self, candidates: Iterable[AdaptiveCandidate]) -> AdaptiveSelection:
        candidate_list = sorted(
            tuple(candidates),
            key=lambda candidate: (-candidate.score, candidate.fingerprint.program_code),
        )
        top = candidate_list[: self._top_limit]
        logger.debug("adaptive_candidate_scan candidate_count=%d top_count=%d", len(candidate_list), len(top))
        if len(top) < 2:
            logger.warning("adaptive_skip_insufficient_candidates candidate_count=%d", len(top))
            return AdaptiveSelection(
                status="skipped",
                reason="Недостаточно программ для осмысленного уточнения.",
                candidate_count=len(candidate_list),
                top_candidate_count=len(top),
            )

        dimensions = _dimensions(tuple(top))
        scored_dimensions: list[AdaptiveDimension] = []
        for code, kind, label in dimensions:
            values = tuple(_dimension_value(candidate.fingerprint, code, kind) for candidate in top)
            spread = max(values) - min(values)
            average = sum(values, Decimal("0")) / Decimal(len(values))
            significance = min(Decimal("1"), spread * (Decimal("0.5") + average))
            if spread >= self._min_spread:
                scored_dimensions.append(
                    AdaptiveDimension(
                        code=code,
                        label=label,
                        kind=kind,
                        spread=spread,
                        significance=significance,
                    )
                )
        scored_dimensions.sort(key=lambda item: (-item.significance, -item.spread, item.code))
        logger.debug(
            "adaptive_dimensions_evaluated dimension_count=%d meaningful_count=%d",
            len(dimensions),
            len(scored_dimensions),
        )
        if len(scored_dimensions) < 2:
            logger.warning("adaptive_skip_insufficient_spread meaningful_count=%d", len(scored_dimensions))
            return AdaptiveSelection(
                status="skipped",
                reason="В текущем наборе программ нет двух достаточно различающихся направлений.",
                candidate_count=len(candidate_list),
                top_candidate_count=len(top),
                dimensions=tuple(scored_dimensions[:2]),
            )
        selected = tuple(scored_dimensions[:2])
        logger.info("adaptive_question_selected dimension_count=2 candidate_count=%d", len(top))
        return AdaptiveSelection(
            status="ready",
            candidate_count=len(candidate_list),
            top_candidate_count=len(top),
            dimensions=selected,
        )


def _dimensions(candidates: tuple[AdaptiveCandidate, ...]) -> tuple[tuple[str, Literal["area", "activity"], str], ...]:
    area_codes = sorted({area for candidate in candidates for area in candidate.fingerprint.area_share}, key=lambda value: value.value)
    activity_codes = sorted({activity for candidate in candidates for activity in candidate.fingerprint.activity_signals}, key=lambda value: value.value)
    return tuple(
        [(f"area:{area.value}", "area", AREA_LABELS[area]) for area in area_codes]
        + [(f"activity:{activity.value}", "activity", activity_label(activity)) for activity in activity_codes]
    )


def _dimension_value(fingerprint: ProgramFingerprint, code: str, kind: str) -> Decimal:
    prefix, value = code.split(":", maxsplit=1)
    if prefix != kind:
        return Decimal("0")
    if kind == "area":
        return fingerprint.area_share.get(AreaCode(value), Decimal("0"))
    return fingerprint.activity_signals.get(ActivityCode(value), Decimal("0"))


def activity_label(activity: ActivityCode) -> str:
    labels = {
        ActivityCode.ANALYTICAL: "Анализировать и находить закономерности",
        ActivityCode.SOFTWARE_CREATION: "Создавать цифровые инструменты",
        ActivityCode.SYSTEM_DESIGN: "Проектировать системы",
        ActivityCode.RESEARCH: "Исследовать и проверять гипотезы",
        ActivityCode.PHYSICAL_ENGINEERING: "Собирать и проверять физические решения",
        ActivityCode.COMMUNICATION: "Объяснять и работать с людьми",
        ActivityCode.CREATIVE: "Придумывать и визуализировать",
        ActivityCode.BUSINESS: "Организовывать и принимать решения",
        ActivityCode.DATA: "Работать с данными",
    }
    return labels[activity]


__all__ = ["AdaptiveCandidate", "AdaptiveQuestionSelector", "activity_label"]
