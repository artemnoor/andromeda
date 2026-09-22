from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from andromeda.ingestion.contracts.raw import (
    AdmissionBenefitParserDiagnostic,
    RawAdmissionBenefitCandidate,
    RawAdmissionBenefitDocument,
    RawIndividualAchievementRecord,
    SourceLocator,
)

_NUMBER_RE = re.compile(r"(?<!\d)(\d{1,3})(?!\d)")
_DIRECTION_RE = re.compile(r"\b\d{2}\.\d{2}\.\d{2}\b")


def parse_individual_achievement_tables(
    document: RawAdmissionBenefitDocument,
    tables: Iterable[Mapping[str, Any]],
) -> tuple[tuple[RawIndividualAchievementRecord, ...], tuple[AdmissionBenefitParserDiagnostic, ...]]:
    """Extract Appendix 6/7 rows without deciding their legal combination policy."""

    records: list[RawIndividualAchievementRecord] = []
    diagnostics: list[AdmissionBenefitParserDiagnostic] = []
    for table_index, table in enumerate(tables, start=1):
        page = _positive_int(table.get("page")) or 1
        table_number = _positive_int(table.get("table")) or _positive_int(table.get("index")) or table_index
        rows = [_values(row) for row in (table.get("rows") or table.get("raw_rows") or ()) if _values(row)]
        source_row_numbers = table.get("row_numbers") or ()
        source_pages = table.get("row_pages") or ()
        if not rows:
            continue
        header = rows[0]
        start = 1 if _looks_like_header(header) else 0
        for row_number, row in enumerate(rows[start:], start=start + 1):
            text = _join(row)
            if not text:
                continue
            source_row = (
                source_row_numbers[row_number - start - 1]
                if row_number - start - 1 < len(source_row_numbers)
                and isinstance(source_row_numbers[row_number - start - 1], int)
                else row_number
            )
            source_page = (
                source_pages[row_number - start - 1]
                if row_number - start - 1 < len(source_pages)
                and isinstance(source_pages[row_number - start - 1], int)
                else page
            )
            locator = SourceLocator(source_url=document.source_url, page=source_page, row=source_row, field=f"table:{table_number}")
            name = _name_candidate(row, header)
            points = _points_candidate(row)
            candidates: list[RawAdmissionBenefitCandidate] = []
            if name:
                candidates.append(RawAdmissionBenefitCandidate(field="official_name", value=name))
            category = _category_candidate(row, header)
            if category:
                candidates.append(RawAdmissionBenefitCandidate(field="category", value=category))
            if points:
                candidates.append(RawAdmissionBenefitCandidate(field="points", value=points))
            document_text = _document_candidate(row, header)
            if document_text:
                candidates.append(RawAdmissionBenefitCandidate(field="required_document", value=document_text))
            if document.document_kind == "appendix_7":
                candidates.append(RawAdmissionBenefitCandidate(field="education_level", value="master"))
            elif document.document_kind == "appendix_6":
                candidates.append(RawAdmissionBenefitCandidate(field="education_level", value="bachelor_or_specialist"))
            policy_text = _policy_text(row)
            if policy_text:
                candidates.append(RawAdmissionBenefitCandidate(field="combination_text", value=policy_text))
                if "не сумм" in policy_text.casefold():
                    candidates.append(RawAdmissionBenefitCandidate(field="combination_policy", value="not_combinable"))
            cap_match = re.search(r"(?:не более|максимум|итого)[^\d]{0,20}(\d{1,3})\s*(?:балл|б\.?)", text, re.IGNORECASE)
            if cap_match:
                candidates.append(RawAdmissionBenefitCandidate(field="global_max_points", value=cap_match.group(1)))
            if not name or not points:
                diagnostics.append(
                    AdmissionBenefitParserDiagnostic(
                        code="individual_achievement_row_review_required",
                        stage="individual_achievements",
                        message="achievement name or points could not be extracted safely",
                        severity="ambiguous",
                        locator=locator,
                    )
                )
            records.append(
                RawIndividualAchievementRecord(
                    record_id=f"raw-individual-achievement:{document.source_snapshot_hash[:16]}:{page}:{table_number}:{row_number}",
                    document_kind=document.document_kind,
                    document_title=document.document_title,
                    admission_year=document.admission_year,
                    source_url=document.source_url,
                    source_snapshot_hash=document.source_snapshot_hash,
                    source_run_id=document.source_run_id,
                    captured_at=document.captured_at,
                    locator=locator,
                    raw_text=text,
                    normalized_candidates=tuple(candidates),
                    diagnostics=tuple(diagnostic for diagnostic in diagnostics if diagnostic.locator == locator),
                    parser_version=document.parser_version,
                    achievement_code_candidate=None,
                    official_name_candidate=_bounded_candidate(name, 512),
                    points_text=points,
                    required_document_text=document_text,
                    combination_text=policy_text,
                )
            )
    return tuple(records), tuple(diagnostics)


def _name_candidate(row: list[str], header: list[str]) -> str | None:
    for index, value in enumerate(row):
        if not value or index == 0 or _looks_like_number(value):
            continue
        header_text = header[index] if index < len(header) else ""
        if any(token in _normalize(header_text) for token in ("документ", "балл", "подтверж")):
            continue
        return value
    return None


def _category_candidate(row: list[str], header: list[str]) -> str | None:
    for index, header_value in enumerate(header):
        if index < len(row) and any(token in _normalize(header_value) for token in ("категор", "вид достиж")) and row[index]:
            return row[index]
    return None


def _points_candidate(row: list[str]) -> str | None:
    for value in reversed(row):
        matches = _NUMBER_RE.findall(value)
        if matches:
            candidate = matches[-1]
            if int(candidate) <= 100:
                return str(candidate)
    return None


def _document_candidate(row: list[str], header: list[str]) -> str | None:
    values = [
        row[index]
        for index, header_value in enumerate(header)
        if index < len(row) and any(token in _normalize(header_value) for token in ("документ", "подтверж", "основан")) and row[index]
    ]
    return " | ".join(values) if values else None


def _policy_text(row: list[str]) -> str | None:
    values = [value for value in row if any(token in _normalize(value) for token in ("сумм", "учитыва", "максимум", "не более", "одноврем"))]
    return " | ".join(values) if values else None


def _looks_like_header(row: list[str]) -> bool:
    return any(token in _normalize(_join(row)) for token in ("достиж", "балл", "документ", "подтверж"))


def _looks_like_number(value: str) -> bool:
    return bool(re.fullmatch(r"\d{1,4}", value.strip()))


def _values(row: Any) -> list[str]:
    if isinstance(row, Mapping):
        return [str(value).strip() for value in row.values() if value is not None and str(value).strip()]
    if isinstance(row, (list, tuple)):
        return [str(value or "").strip() for value in row]
    return []


def _join(values: list[str]) -> str:
    return " | ".join(value for value in values if value)


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def _positive_int(value: object) -> int | None:
    return value if isinstance(value, int) and value >= 1 else None


def _bounded_candidate(value: str | None, limit: int) -> str | None:
    """Project an extracted value into a bounded typed candidate field."""
    if value is None or len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


__all__ = ["parse_individual_achievement_tables"]
