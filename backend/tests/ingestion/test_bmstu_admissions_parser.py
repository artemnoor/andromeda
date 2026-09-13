from __future__ import annotations

from pathlib import Path

from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter


FIXTURES = Path(__file__).parents[1] / "fixtures" / "tracer" / "raw"


def test_bmstu_detail_admissions_are_emitted_as_canonical_program_contracts() -> None:
    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=FIXTURES)
    finally:
        adapter.close()

    assert len(raw.admissions) == 20
    assert {item.program_id for item in canonical.admissions} == {
        "program:09.03.01-02",
        "program:09.03.01-12",
    }
    first = canonical.admissions[0]
    current_budget = next(item for item in first.offerings if item.admission_year == 2026 and item.funding_type.value == "budget")
    current_paid = next(item for item in first.offerings if item.admission_year == 2026 and item.funding_type.value == "paid")
    assert current_budget.places == 318
    assert current_paid.places == 230
    assert {item.minimum_score for item in current_budget.exams} == {46}
    assert {item.amount for item in current_paid.tuition} == {529000, 264500}
    assert any(item.admission_year == 2024 and item.passing_scores for item in first.offerings)


def test_detail_admission_source_preserves_direction_scope_and_provenance() -> None:
    adapter = BmstuUniversityAdapter()
    try:
        _, canonical = adapter.parse_sources(fixture_dir=FIXTURES)
    finally:
        adapter.close()
    assert all(offering.scope.value == "direction" for item in canonical.admissions for offering in item.offerings)
    assert all(offering.provenance[0].source_kind == "bmstu_major_detail" for item in canonical.admissions for offering in item.offerings)
