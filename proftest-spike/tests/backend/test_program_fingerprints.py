from __future__ import annotations

import json
from decimal import Decimal

from proftest_spike.api_client.contracts import CurriculumResponse
from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.builder import FingerprintBuilder
from proftest_spike.program_fingerprints.entities import ActivityCode


def _program(code: str) -> dict[str, object]:
    return {
        "id": f"program:{code}",
        "directionId": f"direction:{code}",
        "code": code,
        "name": f"Программа {code}",
        "educationYear": 2025,
        "studyPlanUrl": "https://bmstu.example/plan",
        "sourceUrl": "https://bmstu.example/program",
    }


def _curriculum(code: str, *, hours: tuple[int, int] = (100, 50), credits: tuple[float, float] = (3, 2), zero_hours: bool = False) -> CurriculumResponse:
    first_hours = 0 if zero_hours else hours[0]
    second_hours = 0 if zero_hours else hours[1]
    payload = {
        "program": _program(code),
        "curriculumId": f"curriculum:{code}",
        "educationYear": 2025,
        "sourceUrl": "https://bmstu.example/curriculum",
        "capturedAt": "2026-09-10T10:00:00Z",
        "items": [
            {
                "id": f"item:{code}:math",
                "discipline": {
                    "id": "discipline:math",
                    "name": "Математика",
                    "normalizedName": "математика",
                    "areaWeights": [{"area": "mathematics_statistics", "weight": 1.0}],
                    "primaryArea": "mathematics_statistics",
                },
                "sourceName": "Математика",
                "semester": 1,
                "hours": first_hours,
                "credits": credits[0],
                "assessmentTypes": ["exam"],
                "subjectGroup": "Базовая часть",
                "sourcePosition": 1,
            },
            {
                "id": f"item:{code}:it",
                "discipline": {
                    "id": "discipline:it",
                    "name": "Программирование",
                    "normalizedName": "программирование",
                    "areaWeights": [
                        {"area": "computer_science_data", "weight": 0.7},
                        {"area": "mathematics_statistics", "weight": 0.3},
                    ],
                    "primaryArea": "computer_science_data",
                },
                "sourceName": "Программирование",
                "semester": None,
                "hours": second_hours,
                "credits": credits[1],
                "assessmentTypes": ["credit", "coursework"],
                "subjectGroup": None,
                "sourcePosition": 2,
            },
        ],
    }
    return CurriculumResponse.model_validate_json(json.dumps(payload))


def test_hours_weighted_fingerprint_preserves_groups_semesters_and_evidence() -> None:
    fingerprint = FingerprintBuilder().build(_curriculum("iu7"))

    assert fingerprint.basis == "hours"
    assert fingerprint.total_hours == 150
    assert fingerprint.total_credits == Decimal("5")
    assert fingerprint.total_workload == Decimal("150")
    assert fingerprint.area_share[AreaCode.MATHEMATICS_STATISTICS] == Decimal("0.7667")
    assert fingerprint.area_share[AreaCode.COMPUTER_SCIENCE_DATA] == Decimal("0.2333")
    assert sum(fingerprint.area_share.values(), Decimal("0")) == Decimal("1.0000")
    assert fingerprint.subject_group_hours["Базовая часть"] == Decimal("100")
    assert fingerprint.subject_group_hours["unassigned"] == Decimal("50")
    assert fingerprint.semester_distribution["1"] == Decimal("0.6667")
    assert fingerprint.semester_distribution["unassigned"] == Decimal("0.3333")
    assert fingerprint.evidence[1].source_name == "Программирование"
    assert ActivityCode.ANALYTICAL in fingerprint.activity_signals


def test_credits_are_used_only_when_all_hours_are_zero() -> None:
    fingerprint = FingerprintBuilder().build(_curriculum("zero", zero_hours=True))

    assert fingerprint.basis == "credits"
    assert fingerprint.total_hours == 0
    assert fingerprint.total_workload == Decimal("5")
    assert fingerprint.area_share[AreaCode.MATHEMATICS_STATISTICS] == Decimal("0.7200")


def test_activity_signals_are_reproducible_and_normalized() -> None:
    curriculum = _curriculum("iu7")
    first = FingerprintBuilder().build(curriculum)
    second = FingerprintBuilder().build(curriculum)

    assert first.activity_signals == second.activity_signals
    assert sum(first.activity_signals.values(), Decimal("0")) == Decimal("1.0000")


def test_distinctive_subjects_come_from_catalog_relative_evidence() -> None:
    builder = FingerprintBuilder()
    first = _curriculum("first")
    second = _curriculum("second", hours=(100, 0))
    fingerprints = builder.build_catalog((first, second))

    assert fingerprints[0].distinctive_subjects
    programming = next(subject for subject in fingerprints[0].distinctive_subjects if subject.source_name == "Программирование")
    assert programming.rarity == Decimal("0.5000")
