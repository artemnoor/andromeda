"""Build fingerprints from Andromeda curriculum read DTOs."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import logging
from typing import Iterable, Literal, TypeVar

from proftest_spike.api_client.contracts import CurriculumResponse
from proftest_spike.domain.areas import AreaCode
from proftest_spike.domain.values import ZERO, quantize_ratio

from .distinctive import add_distinctive_subjects
from .entities import ActivityCode, CurriculumEvidence, ProgramFingerprint
from .signals import ACTIVITY_SIGNAL_WEIGHTS

logger = logging.getLogger("proftest_spike.fingerprint")
KeyT = TypeVar("KeyT", str, AreaCode)


class FingerprintBuilder:
    """Pure deterministic fingerprint builder; no storage or network access."""

    def build(self, curriculum: CurriculumResponse) -> ProgramFingerprint:
        logger.debug("fingerprint_start program_id=%s item_count=%d", _safe_id(curriculum.program.id), len(curriculum.items))
        total_hours = sum(item.hours for item in curriculum.items)
        total_credits = sum((item.credits or ZERO for item in curriculum.items), ZERO)
        basis: Literal["hours", "credits"] = "hours" if total_hours > 0 else "credits"
        total_workload = Decimal(total_hours) if basis == "hours" else total_credits
        if total_workload <= ZERO:
            logger.warning("fingerprint_zero_workload program_id=%s", _safe_id(curriculum.program.id))

        area_workload: dict[AreaCode, Decimal] = defaultdict(lambda: ZERO)
        group_workload: dict[str, Decimal] = defaultdict(lambda: ZERO)
        semester_workload: dict[str, Decimal] = defaultdict(lambda: ZERO)
        evidence: list[CurriculumEvidence] = []
        for item in curriculum.items:
            item_workload = Decimal(item.hours) if basis == "hours" else (item.credits or ZERO)
            area_weight_sum = sum((weight.weight for weight in item.discipline.area_weights), ZERO)
            if area_weight_sum != Decimal("1"):
                logger.error("fingerprint_invalid_area_vector program_id=%s field=area_weights", _safe_id(curriculum.program.id))
                raise ValueError(f"discipline area weights must sum to one: {item.discipline.id}")
            item_area_weights = {weight.area: weight.weight for weight in item.discipline.area_weights}
            for area, weight in item_area_weights.items():
                area_workload[area] += item_workload * weight
            group_key = item.subject_group or "unassigned"
            group_workload[group_key] += item_workload
            semester_key = str(item.semester) if item.semester is not None else "unassigned"
            semester_workload[semester_key] += item_workload
            evidence.append(
                CurriculumEvidence(
                    source_name=item.source_name,
                    normalized_name=item.discipline.normalized_name,
                    hours=item.hours,
                    credits=item.credits,
                    semester=item.semester,
                    subject_group=group_key,
                    assessment_types=item.assessment_types,
                    workload=item_workload,
                    area_weights=item_area_weights,
                )
            )

        area_share = _shares(area_workload, total_workload)
        group_share = _shares(group_workload, total_workload)
        semester_share = _shares(semester_workload, total_workload)
        activity_signals = _activity_signals(area_share)
        fingerprint = ProgramFingerprint(
            program_id=curriculum.program.id,
            program_code=curriculum.program.code,
            program_name=curriculum.program.name,
            basis=basis,
            total_hours=total_hours,
            total_credits=total_credits,
            total_workload=total_workload,
            area_hours=dict(sorted(area_workload.items(), key=lambda entry: entry[0].value)),
            area_share=dict(sorted(area_share.items(), key=lambda entry: entry[0].value)),
            subject_group_hours=dict(sorted(group_workload.items())),
            subject_group_share=dict(sorted(group_share.items())),
            semester_distribution=dict(sorted(semester_share.items())),
            activity_signals=dict(sorted(activity_signals.items(), key=lambda entry: entry[0].value)),
            evidence=tuple(evidence),
        )
        logger.debug(
            "fingerprint_buckets program_id=%s basis=%s areas=%d groups=%d semesters=%d signals=%d",
            _safe_id(fingerprint.program_id),
            fingerprint.basis,
            len(fingerprint.area_share),
            len(fingerprint.subject_group_share),
            len(fingerprint.semester_distribution),
            len(fingerprint.activity_signals),
        )
        logger.info(
            "fingerprint_complete program_id=%s basis=%s total_hours=%d total_credits=%s area_count=%d distinctive_count=%d",
            _safe_id(fingerprint.program_id),
            fingerprint.basis,
            fingerprint.total_hours,
            fingerprint.total_credits,
            len(fingerprint.area_share),
            len(fingerprint.distinctive_subjects),
        )
        return fingerprint

    def build_catalog(self, curricula: Iterable[CurriculumResponse]) -> tuple[ProgramFingerprint, ...]:
        curriculum_list = tuple(curricula)
        fingerprints = tuple(self.build(curriculum) for curriculum in curriculum_list)
        if len(fingerprints) < 2:
            logger.warning("fingerprint_distinctiveness_insufficient_catalog program_count=%d", len(fingerprints))
        return add_distinctive_subjects(fingerprints, curriculum_list)


def _shares(values: dict[KeyT, Decimal], total: Decimal) -> dict[KeyT, Decimal]:
    if total <= ZERO:
        return {}
    ordered_values: list[tuple[KeyT, Decimal]] = sorted(
        ((key, value) for key, value in values.items() if value > ZERO),
        key=lambda entry: str(entry[0]),
    )
    if not ordered_values:
        return {}
    shares = {key: quantize_ratio(value / total) for key, value in ordered_values}
    last_key = ordered_values[-1][0]
    shares[last_key] += Decimal("1") - sum(shares.values(), ZERO)
    return shares


def _activity_signals(area_share: dict[AreaCode, Decimal]) -> dict[ActivityCode, Decimal]:
    if not area_share:
        return {}
    signals: dict[ActivityCode, Decimal] = defaultdict(lambda: ZERO)
    for area, area_ratio in area_share.items():
        for signal, weight in ACTIVITY_SIGNAL_WEIGHTS[area].items():
            signals[signal] += area_ratio * weight
    total = sum(signals.values(), ZERO)
    if total <= ZERO:
        return {}
    ordered_signals = sorted(((signal, value) for signal, value in signals.items() if value > ZERO), key=lambda entry: entry[0].value)
    normalized = {signal: quantize_ratio(value / total) for signal, value in ordered_signals}
    last_signal = ordered_signals[-1][0]
    normalized[last_signal] += Decimal("1") - sum(normalized.values(), ZERO)
    return normalized


def _safe_id(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ")[:128]


__all__ = ["FingerprintBuilder"]
