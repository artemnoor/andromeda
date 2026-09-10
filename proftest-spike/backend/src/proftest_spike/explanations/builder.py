"""Build only claims supported by fingerprint and profile values."""

from __future__ import annotations

from decimal import Decimal

from proftest_spike.domain.areas import AREA_LABELS, AreaCode
from proftest_spike.domain.values import ZERO, quantize_ratio
from proftest_spike.program_fingerprints.entities import ActivityCode, ProgramFingerprint
from proftest_spike.profiling.entities import UserProfile

from .entities import Reason


class ExplanationBuilder:
    def build(self, profile: UserProfile, fingerprint: ProgramFingerprint) -> tuple[Reason, ...]:
        reasons: list[Reason] = []
        reasons.extend(self._positive_area_reasons(profile, fingerprint))
        reasons.extend(self._positive_activity_reasons(profile, fingerprint))
        reasons.extend(self._negative_reasons(profile, fingerprint))
        reasons.extend(self._distinctive_reasons(profile, fingerprint))
        if not reasons:
            reasons.append(
                Reason(
                    kind="neutral",
                    code="neutral_profile",
                    title="Профиль пока нейтральный",
                    detail="Результат основан на доступной структуре учебного плана; после дополнительных ответов fit станет точнее.",
                    workload=fingerprint.total_workload,
                    share=Decimal("1") if fingerprint.total_workload > ZERO else ZERO,
                    impact=ZERO,
                )
            )
        return tuple(reasons[:8])

    def _positive_area_reasons(self, profile: UserProfile, fingerprint: ProgramFingerprint) -> list[Reason]:
        rows: list[Reason] = []
        for area, preference in sorted(profile.preferred_subject_weights.items(), key=lambda entry: (-entry[1], entry[0].value)):
            share = fingerprint.area_share.get(area, ZERO)
            if share <= ZERO:
                continue
            workload = fingerprint.area_hours.get(area, ZERO)
            impact = Decimal("100") * share * preference
            rows.append(
                Reason(
                    kind="positive",
                    code=f"subject:{area.value}",
                    title=f"Совпадает интерес к области «{AREA_LABELS[area]}»",
                    detail=f"В учебном плане {format_workload(workload, fingerprint)} ({format_percent(share)}); это поддерживает выбранное направление.",
                    area=area,
                    workload=workload,
                    share=quantize_ratio(share),
                    impact=quantize_ratio(impact),
                    source_names=_source_names_for_area(fingerprint, area),
                )
            )
        return rows[:3]

    def _positive_activity_reasons(self, profile: UserProfile, fingerprint: ProgramFingerprint) -> list[Reason]:
        rows: list[Reason] = []
        for activity, preference in sorted(profile.preferred_activity_weights.items(), key=lambda entry: (-entry[1], entry[0].value)):
            share = fingerprint.activity_signals.get(activity, ZERO)
            if share <= ZERO:
                continue
            workload = fingerprint.total_workload * share
            impact = Decimal("100") * share * preference
            rows.append(
                Reason(
                    kind="positive",
                    code=f"activity:{activity.value}",
                    title=f"Способ работы «{activity_label(activity)}» встречается в fingerprint",
                    detail=f"Сигнал занимает около {format_percent(share)} учебной нагрузки ({format_workload(workload, fingerprint)}).",
                    activity=activity,
                    workload=workload,
                    share=quantize_ratio(share),
                    impact=quantize_ratio(impact),
                )
            )
        return rows[:2]

    def _negative_reasons(self, profile: UserProfile, fingerprint: ProgramFingerprint) -> list[Reason]:
        rows: list[Reason] = []
        for area, intensity in sorted(profile.negative_weights.items(), key=lambda entry: (-entry[1], entry[0].value)):
            share = fingerprint.area_share.get(area, ZERO)
            if share <= ZERO:
                continue
            workload = fingerprint.area_hours.get(area, ZERO)
            impact = -Decimal("100") * share * intensity
            rows.append(
                Reason(
                    kind="negative",
                    code=f"anti:{area.value}",
                    title=f"Может не понравиться: «{AREA_LABELS[area]}»",
                    detail=f"Антиинтерес умножает penalty: {format_percent(share)} учебного плана ({format_workload(workload, fingerprint)}) с интенсивностью {format_percent(intensity)}.",
                    area=area,
                    workload=workload,
                    share=quantize_ratio(share),
                    impact=quantize_ratio(impact),
                    source_names=_source_names_for_area(fingerprint, area),
                )
            )
        return rows[:3]

    def _distinctive_reasons(self, profile: UserProfile, fingerprint: ProgramFingerprint) -> list[Reason]:
        rows: list[Reason] = []
        for subject in fingerprint.distinctive_subjects:
            preference = profile.preferred_subject_weights.get(subject.primary_area, ZERO)
            if preference <= ZERO:
                continue
            rows.append(
                Reason(
                    kind="distinctive",
                    code=f"distinctive:{subject.normalized_name}",
                    title=f"Отличительная дисциплина: {subject.source_name}",
                    detail=f"Дисциплина занимает {format_percent(subject.share)} нагрузки и редко встречается в загруженном каталоге.",
                    area=subject.primary_area,
                    workload=subject.workload,
                    share=subject.share,
                    impact=quantize_ratio(Decimal("100") * subject.distinctiveness * preference),
                    source_names=(subject.source_name,),
                )
            )
        return rows[:2]


def _source_names_for_area(fingerprint: ProgramFingerprint, area: AreaCode) -> tuple[str, ...]:
    names = [
        evidence.source_name
        for evidence in fingerprint.evidence
        if area in evidence.area_weights
    ]
    return tuple(dict.fromkeys(names))[:3]


def format_workload(workload: Decimal, fingerprint: ProgramFingerprint) -> str:
    unit = "часов" if fingerprint.basis == "hours" else "ЗЕТ"
    return f"{_decimal_text(workload)} {unit}"


def format_percent(value: Decimal) -> str:
    return f"{_decimal_text(value * Decimal('100'))}%"


def _decimal_text(value: Decimal) -> str:
    normalized = value.quantize(Decimal("0.1"))
    return str(normalized).rstrip("0").rstrip(".")


def activity_label(activity: ActivityCode) -> str:
    return {
        ActivityCode.ANALYTICAL: "анализировать и находить закономерности",
        ActivityCode.SOFTWARE_CREATION: "создавать цифровые инструменты",
        ActivityCode.SYSTEM_DESIGN: "проектировать системы",
        ActivityCode.RESEARCH: "исследовать и проверять гипотезы",
        ActivityCode.PHYSICAL_ENGINEERING: "собирать физические решения",
        ActivityCode.COMMUNICATION: "объяснять и работать с людьми",
        ActivityCode.CREATIVE: "придумывать и визуализировать",
        ActivityCode.BUSINESS: "организовывать и принимать решения",
        ActivityCode.DATA: "работать с данными",
    }[activity]


__all__ = ["ExplanationBuilder", "activity_label", "format_percent", "format_workload"]
