from __future__ import annotations

"""Priority parser for the official 2026 BMSTU admission-plan PDF.

The PDF is an exported spreadsheet.  The parsing model is based on the
reference ``pdfplumber`` parser in :mod:`bmstu_parser.admission_pdf`: it
reads table geometry, restores merged cells and keeps page/table/row
provenance.  No OCR is used.  Admission places are emitted once per actual
program block; links to several departments are preserved separately instead
of multiplying the same places across departments.
"""

import re
from datetime import datetime, timezone
from hashlib import sha1, sha256
from pathlib import Path
from typing import Any

from .admission_pdf import build_model, iter_raw_rows
from .models import ExtractionResult, SourceDefinition
from .pdf import extract_pdf_text, pdf_metadata


PRIORITY_SOURCE_ID = "P01_BS_PDF"
ADMISSION_PLAN_HEADERS = [
    "direction_name",
    "direction_code",
    "education_level",
    "department_code",
    "department_name",
    "program_name",
    "duration",
    "budget_places",
    "paid_places",
    "budget_special_quota_places",
    "paid_special_quota_places",
]

_EDUCATION_CODE_RE = re.compile(r"(?<!\d)\d{1,2}\.\d{2}\.\d{2}(?:[-/]\d+)?(?!\d)")
def priority_source_definition(path: Path) -> SourceDefinition:
    resolved = path.expanduser().resolve()
    return SourceDefinition(
        id=PRIORITY_SOURCE_ID,
        name="БС.pdf — план приёма 2026 (приоритетный источник)",
        url=resolved.as_uri(),
        officiality="официальный документ МГТУ",
        scope="head_university_and_branches",
        format="PDF",
        availability="локальный файл",
        method="pdfplumber table geometry + merged-cell state",
        data_description="План приёма на 1-й курс: направление, кафедра, образовательная программа, срок и распределение мест",
        refresh="по замене файла",
        note=(
            "Имеет приоритет над сайтами для мест и связанных с ними полей "
            "поступления; несколько кафедр внутри одного блока не дублируют места."
        ),
    )


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def _number(value: Any) -> int | None:
    text = _clean(value).replace(" ", "")
    if not text:
        return None
    match = re.search(r"(?<!\d)\d{1,3}(?!\d)", text)
    return int(match.group(0)) if match else None


def _education_code(value: Any) -> str | None:
    match = _EDUCATION_CODE_RE.search(_clean(value).replace("–", "-").replace("—", "-"))
    return match.group(0) if match else None


def _infer_level(code: str | None, value: Any) -> str | None:
    text = _clean(value).casefold()
    if "бакалавр" in text:
        return "бакалавриат"
    if "магистр" in text:
        return "магистратура"
    if "специал" in text:
        return "специалитет"
    if code and ".03." in code:
        return "бакалавриат"
    if code and ".04." in code:
        return "магистратура"
    if code and ".05." in code:
        return "специалитет"
    return text or None


def _record_id(payload: dict[str, Any]) -> str:
    stable = "|".join(str(payload.get(key) or "") for key in (
        "direction_code", "program_name", "campus", "pdf_program_id", "pdf_page", "pdf_row",
    ))
    return f"{PRIORITY_SOURCE_ID}:Admission:{sha1(stable.encode('utf-8')).hexdigest()[:16]}"


def parse_priority_pdf(path: Path, captured_at: str | None = None) -> ExtractionResult:
    """Parse the admission-place table from ``БС.pdf``."""
    try:
        import pdfplumber  # noqa: F401  # imported for a clear dependency error
    except ImportError as exc:  # pragma: no cover - declared project dependencies
        raise RuntimeError("Для приоритетного PDF нужен pdfplumber") from exc

    source = priority_source_definition(path)
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Приоритетный PDF не найден: {resolved}")
    captured_at = captured_at or datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    warnings: list[str] = []
    raw_text = resolved.read_bytes()
    metadata = pdf_metadata(raw_text)
    extracted_text = extract_pdf_text(raw_text)
    raw_rows = iter_raw_rows(resolved)
    model = build_model(raw_rows, resolved.name)
    directions_by_id = {item["id"]: item for item in model["directions"]}
    campuses_by_id = {item["id"]: item for item in model["campuses"]}
    departments_by_id = {item["id"]: item for item in model["departments"]}
    links_by_program: dict[str, list[dict[str, Any]]] = {}
    for link in model["program_departments"]:
        links_by_program.setdefault(link["program_id"], []).append(link)

    structured_rows: list[dict[str, Any]] = []
    for program in model["programs"]:
        direction = directions_by_id[program["direction_id"]]
        campus = campuses_by_id[direction["campus_id"]]
        linked_departments = [
            {
                **departments_by_id[link["department_id"]],
                "source_page": link["source_page"],
                "source_table": link["source_table"],
                "source_row": link["source_row"],
            }
            for link in links_by_program.get(program["id"], [])
        ]
        primary_department = linked_departments[0] if linked_departments else {}
        program_source = program["source"]
        admission = program["admission"]
        record = {
            "record_type": "Admission",
            "source_id": source.id,
            "source_url": source.url,
            "source_scope": "head_university" if campus["name"] == "Москва" else "branch",
            "source_priority": "primary",
            "priority_rank": 100,
            "observed_at": captured_at,
            "year": 2026,
            "direction_code": direction["code"],
            "program_code": direction["code"],
            "direction_name": direction["name"],
            "education_level": _infer_level(direction["code"], direction.get("education_level")),
            "department_code": primary_department.get("code_raw"),
            "department_code_raw": primary_department.get("code_raw"),
            "department_name": primary_department.get("name"),
            "department_codes": [item.get("code_raw") for item in linked_departments if item.get("code_raw")],
            "department_names": [item.get("name") for item in linked_departments if item.get("name")],
            "program_departments": linked_departments,
            "program_name": program["name"],
            "program_profile": program["name"],
            "duration": program.get("duration"),
            "budget_places": admission.get("budget_places"),
            "paid_places": admission.get("paid_places"),
            "budget_special_quota_places": admission.get("special_quota_places"),
            "paid_special_quota_places": admission.get("separate_quota_places"),
            "campus": campus["name"],
            "pdf_program_id": program["id"],
            "pdf_page": program_source["page"],
            "pdf_table": program_source["table"],
            "pdf_row": program_source["row"],
            "is_data_row": True,
        }
        record["record_id"] = _record_id(record)
        records.append(record)
        structured_rows.append({key: record.get(key) for key in ADMISSION_PLAN_HEADERS})

    tables.append({
        "index": 0,
        "page": None,
        "table_index": None,
        "headers": ADMISSION_PLAN_HEADERS,
        "rows": structured_rows,
        "source_scope": "head_university_and_branches",
        "campus": None,
        "normalized_model": model,
    })

    document_record = {
        "record_type": "Document",
        "source_id": source.id,
        "source_url": source.url,
        "source_scope": "head_university_and_branches",
        "source_priority": "primary",
        "priority_rank": 100,
        "observed_at": captured_at,
        "title": metadata.get("title") or "План приёма на 1-й курс МГТУ им. Н.Э. Баумана в 2026 году",
        "url": source.url,
        "document_type": "pdf",
        "admission_year": 2026,
        "content_hash": sha256(raw_text).hexdigest(),
        "pages": metadata.get("pages"),
        "text_length": len(extracted_text),
    }
    document_record["record_id"] = f"{source.id}:Document:{sha1(source.url.encode('utf-8')).hexdigest()[:16]}"
    return ExtractionResult(
        source_id=source.id,
        source_url=source.url,
        parser="bmstu.priority_admission_pdf",
        captured_at=captured_at,
        records=[document_record, *records],
        tables=tables,
        text=extracted_text,
        warnings=warnings,
    )
