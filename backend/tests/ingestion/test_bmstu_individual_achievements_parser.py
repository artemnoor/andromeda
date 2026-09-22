from __future__ import annotations

from datetime import UTC, datetime

from pydantic import HttpUrl

from andromeda.ingestion.contracts.raw import RawAdmissionBenefitDocument, SourceLocator
from andromeda.ingestion.universities.bmstu.parser.individual_achievements import (
    parse_individual_achievement_tables,
)


def _document(kind: str = "appendix_6") -> RawAdmissionBenefitDocument:
    url = "https://api.www.bmstu.ru/file/125465/download" if kind == "appendix_6" else "https://api.www.bmstu.ru/file/124926/download"
    return RawAdmissionBenefitDocument(
        document_kind=kind,
        document_title=f"Приложение {kind.removeprefix('appendix_')} 2026",
        admission_year=2026,
        source_url=HttpUrl(url),
        source_snapshot_hash="5" * 64,
        source_run_id="ingest:" + "6" * 32,
        captured_at=datetime(2026, 9, 22, tzinfo=UTC),
        locator=SourceLocator(source_url=HttpUrl(url)),
        parser_version="bmstu-admission-parser.v1",
    )


def test_appendix_6_rows_preserve_points_and_document_requirements() -> None:
    records, diagnostics = parse_individual_achievement_tables(
        _document(),
        (
            {
                "page": 1,
                "table": 1,
                "rows": [
                    ["№", "Вид индивидуального достижения", "Подтверждающий документ", "Баллы"],
                    ["1", "Аттестат о среднем общем образовании с отличием", "аттестат", "10"],
                    ["5", "Золотой знак ГТО", "удостоверение ГТО", "5"],
                ],
            },
        ),
    )

    assert len(records) == 2
    assert diagnostics == ()
    assert records[0].official_name_candidate == "Аттестат о среднем общем образовании с отличием"
    assert records[0].points_text == "10"
    assert records[1].required_document_text == "удостоверение ГТО"


def test_appendix_7_rows_are_marked_master_only() -> None:
    records, _ = parse_individual_achievement_tables(
        _document("appendix_7"),
        (
            {
                "page": 1,
                "table": 1,
                "rows": [["№", "Вид достижения", "Баллы"], ["1", "Научная публикация", "5"]],
            },
        ),
    )

    assert any(candidate.field == "education_level" and candidate.value == "master" for candidate in records[0].normalized_candidates)


def test_oversized_official_achievement_name_is_bounded_in_typed_projection() -> None:
    long_name = "Наличие " + ("документа о достижении, " * 60)
    records, diagnostics = parse_individual_achievement_tables(
        _document(),
        (
            {
                "page": 1,
                "table": 1,
                "rows": [
                    ["№", "Вид индивидуального достижения", "Баллы"],
                    ["1", long_name, "5"],
                ],
            },
        ),
    )

    assert diagnostics == ()
    assert records[0].official_name_candidate == f"{long_name[:509]}..."
    assert any(candidate.field == "official_name" and candidate.value == long_name.strip() for candidate in records[0].normalized_candidates)


def test_not_counted_for_special_rights_is_not_misclassified_as_non_combinable() -> None:
    records, diagnostics = parse_individual_achievement_tables(
        _document(),
        (
            {
                "page": 1,
                "table": 1,
                "rows": [
                    ["№", "Вид индивидуального достижения", "Условие", "Баллы"],
                    ["1", "Олимпиада", "результаты не учитывались при получении особых прав", "5"],
                ],
            },
        ),
    )

    assert diagnostics == ()
    assert records
    assert not any(candidate.field == "combination_policy" for candidate in records[0].normalized_candidates)
