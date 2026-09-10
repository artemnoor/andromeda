"""Catalog-relative distinctive discipline calculation."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Iterable

from proftest_spike.api_client.contracts import CurriculumResponse
from proftest_spike.domain.values import ZERO, clamp, quantize_ratio

from .entities import CurriculumEvidence, DistinctiveSubject, ProgramFingerprint


def add_distinctive_subjects(
    fingerprints: Iterable[ProgramFingerprint],
    curricula: Iterable[CurriculumResponse],
    *,
    limit: int = 8,
) -> tuple[ProgramFingerprint, ...]:
    """Return fingerprints enriched with evidence-backed catalog-relative subjects."""

    fingerprint_list = tuple(fingerprints)
    curriculum_list = tuple(curricula)
    total_programs = len(fingerprint_list)
    if total_programs == 0:
        return ()

    program_presence: dict[str, set[str]] = defaultdict(set)
    for curriculum in curriculum_list:
        has_hours = sum(item.hours for item in curriculum.items) > 0
        for item in curriculum.items:
            item_workload = Decimal(item.hours) if has_hours else (item.credits or ZERO)
            if item_workload <= ZERO:
                continue
            program_presence[item.discipline.normalized_name].add(curriculum.program.id)

    enriched: list[ProgramFingerprint] = []
    for fingerprint in fingerprint_list:
        by_name: dict[str, list[CurriculumEvidence]] = defaultdict(list)
        for evidence in fingerprint.evidence:
            by_name[evidence.normalized_name].append(evidence)
        subjects: list[DistinctiveSubject] = []
        for normalized_name, evidence_rows in by_name.items():
            workload = sum((row.workload for row in evidence_rows), ZERO)
            if fingerprint.total_workload <= ZERO or workload <= ZERO:
                continue
            share = workload / fingerprint.total_workload
            frequency = len(program_presence.get(normalized_name, set()))
            rarity = Decimal(1) - (Decimal(frequency) / Decimal(total_programs))
            distinctiveness = clamp(share * rarity)
            if distinctiveness <= ZERO:
                continue
            representative = max(evidence_rows, key=lambda row: (row.workload, row.source_name))
            primary_area = max(representative.area_weights.items(), key=lambda entry: (entry[1], entry[0].value))[0]
            subjects.append(
                DistinctiveSubject(
                    source_name=representative.source_name,
                    normalized_name=normalized_name,
                    primary_area=primary_area,
                    workload=workload,
                    share=quantize_ratio(share),
                    rarity=quantize_ratio(rarity),
                    distinctiveness=quantize_ratio(distinctiveness),
                )
            )
        subjects.sort(key=lambda subject: (-subject.distinctiveness, -subject.share, subject.normalized_name))
        enriched.append(fingerprint.model_copy(update={"distinctive_subjects": tuple(subjects[:limit])}))
    return tuple(enriched)


__all__ = ["add_distinctive_subjects"]
