from __future__ import annotations

from collections import defaultdict
from hashlib import sha256

from andromeda.ingestion.contracts.raw import RawIndividualAchievementRecord
from andromeda.shared.contracts.base import ContractModel
from pydantic import Field


class BenefitConflictGroup(ContractModel):
    conflict_id: str
    identity: str = Field(min_length=1, max_length=512)
    record_ids: tuple[str, ...] = Field(min_length=2)
    values: tuple[str, ...] = Field(min_length=2)


def detect_individual_achievement_conflicts(
    records: tuple[RawIndividualAchievementRecord, ...],
) -> tuple[BenefitConflictGroup, ...]:
    grouped: dict[str, list[RawIndividualAchievementRecord]] = defaultdict(list)
    for record in records:
        name = record.official_name_candidate or record.raw_text.split(" | ", 1)[0]
        grouped[name.casefold().strip()].append(record)
    conflicts: list[BenefitConflictGroup] = []
    for identity, group in grouped.items():
        values = tuple(dict.fromkeys(record.points_text or "unknown" for record in group))
        if len(values) < 2:
            continue
        conflict_id = "benefit-conflict:" + sha256(identity.encode("utf-8")).hexdigest()[:24]
        conflicts.append(
            BenefitConflictGroup(
                conflict_id=conflict_id,
                identity=identity,
                record_ids=tuple(record.record_id for record in group),
                values=values,
            )
        )
    return tuple(conflicts)


__all__ = ["BenefitConflictGroup", "detect_individual_achievement_conflicts"]
