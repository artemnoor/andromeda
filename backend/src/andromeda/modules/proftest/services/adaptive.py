"""Select and materialize adaptive questions from candidate spread."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Literal

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode, area_definition

from ..contracts.public import ActivityCode, AdaptiveDimension, AdaptiveSelection, AdaptiveStatus, Question, QuestionBlock, QuestionOption
from ..domain.entities import ProgramFingerprint
from ..domain.values import quantize_ratio


logger = logging.getLogger("andromeda.proftest.adaptive")


@dataclass(frozen=True, slots=True)
class AdaptiveCandidate:
    fingerprint: ProgramFingerprint
    score: Decimal


class AdaptiveQuestionSelector:
    def __init__(self, *, top_limit: int = 10, min_spread: Decimal = Decimal("0.08")) -> None:
        self._top_limit = top_limit
        self._min_spread = min_spread

    def select(self, candidates: tuple[AdaptiveCandidate, ...]) -> AdaptiveSelection:
        ranked = tuple(sorted(candidates, key=lambda candidate: (-candidate.score, candidate.fingerprint.program_code)))
        top = ranked[: self._top_limit]
        if len(top) < 2:
            logger.warning("adaptive_skip_insufficient_candidates candidate_count=%d", len(top))
            return AdaptiveSelection(status=AdaptiveStatus.SKIPPED, reason="Недостаточно программ для осмысленного уточнения.", candidate_count=len(ranked), top_candidate_count=len(top))
        dimensions = _dimensions(top)
        scored: list[AdaptiveDimension] = []
        for code, kind, label in dimensions:
            values = tuple(_dimension_value(candidate.fingerprint, code, kind) for candidate in top)
            spread = max(values) - min(values)
            average = sum(values, Decimal("0")) / Decimal(len(values))
            significance = min(Decimal("1"), spread * (Decimal("0.5") + average))
            if spread >= self._min_spread:
                scored.append(AdaptiveDimension(code=code, label=label, kind=kind, spread=quantize_ratio(spread), significance=quantize_ratio(significance)))
        scored.sort(key=lambda dimension: (-dimension.significance, -dimension.spread, dimension.code))
        if len(scored) < 2:
            logger.warning("adaptive_skip_insufficient_spread meaningful_count=%d", len(scored))
            return AdaptiveSelection(status=AdaptiveStatus.SKIPPED, reason="В текущем наборе программ нет двух достаточно различающихся направлений.", candidate_count=len(ranked), top_candidate_count=len(top), dimensions=tuple(scored[:2]))
        logger.info("adaptive_question_selected dimension_count=2 candidate_count=%d", len(top))
        return AdaptiveSelection(status=AdaptiveStatus.READY, candidate_count=len(ranked), top_candidate_count=len(top), dimensions=tuple(scored[:2]))


class AdaptiveQuestionFactory:
    def create(self, selection: AdaptiveSelection) -> Question | None:
        if selection.status is not AdaptiveStatus.READY or len(selection.dimensions) < 2:
            return None
        first, second = selection.dimensions
        first_subjects, first_activities = _dimension_weights(first)
        second_subjects, second_activities = _dimension_weights(second)
        return Question(
            id=f"adaptive_{first.code.replace(':', '_')}_{second.code.replace(':', '_')}",
            block=QuestionBlock.ADAPTIVE,
            prompt=f"Что тебе ближе: {first.label.lower()} или {second.label.lower()}?",
            adaptive=True,
            options=(
                QuestionOption(id="prefer_first", label=first.label, subject_weights=first_subjects, activity_weights=first_activities),
                QuestionOption(id="prefer_second", label=second.label, subject_weights=second_subjects, activity_weights=second_activities),
                QuestionOption(id="balanced", label="Сочетать оба направления", subject_weights={**first_subjects, **second_subjects}, activity_weights={**first_activities, **second_activities}),
            ),
        )


def _dimensions(candidates: tuple[AdaptiveCandidate, ...]) -> tuple[tuple[str, Literal["area", "activity"], str], ...]:
    areas = sorted({area for candidate in candidates for area in candidate.fingerprint.area_share}, key=lambda area: area.value)
    activities = sorted({activity for candidate in candidates for activity in candidate.fingerprint.activity_signals}, key=lambda activity: activity.value)
    return tuple([(f"area:{area.value}", "area", area_definition(area).name) for area in areas] + [(f"activity:{activity.value}", "activity", _activity_label(activity)) for activity in activities])


def _dimension_value(fingerprint: ProgramFingerprint, code: str, kind: Literal["area", "activity"]) -> Decimal:
    _, value = code.split(":", maxsplit=1)
    if kind == "area":
        return fingerprint.area_share.get(DisciplineAreaCode(value), Decimal("0"))
    return fingerprint.activity_signals.get(ActivityCode(value), Decimal("0"))


def _dimension_weights(dimension: AdaptiveDimension) -> tuple[dict[DisciplineAreaCode, Decimal], dict[ActivityCode, Decimal]]:
    _, value = dimension.code.split(":", maxsplit=1)
    if dimension.kind == "area":
        return {DisciplineAreaCode(value): Decimal("1")}, {}
    return {}, {ActivityCode(value): Decimal("1")}


def _activity_label(activity: ActivityCode) -> str:
    return {
        ActivityCode.ANALYTICAL: "Анализировать и находить закономерности",
        ActivityCode.SOFTWARE_CREATION: "Создавать цифровые инструменты",
        ActivityCode.SYSTEM_DESIGN: "Проектировать системы",
        ActivityCode.RESEARCH: "Исследовать и проверять гипотезы",
        ActivityCode.PHYSICAL_ENGINEERING: "Собирать и проверять физические решения",
        ActivityCode.COMMUNICATION: "Объяснять и работать с людьми",
        ActivityCode.CREATIVE: "Придумывать и визуализировать",
        ActivityCode.BUSINESS: "Организовывать и принимать решения",
        ActivityCode.DATA: "Работать с данными",
    }[activity]


__all__ = ["AdaptiveCandidate", "AdaptiveQuestionFactory", "AdaptiveQuestionSelector"]
