from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Iterable
from hashlib import sha1
from typing import Any
from urllib.parse import urljoin, urlparse

from ..html import (
    clean_text,
    extract_emails,
    extract_phones,
    extract_years,
    looks_like_code,
    parse_number,
    parse_page,
)
from ..models import ExtractionResult, FetchedResource, SourceDefinition
from ..pdf import (
    extract_admission_year,
    extract_pdf_tables,
    extract_pdf_text,
    is_pdf,
    iter_registered_rows,
    iter_order_rows,
    pdf_metadata,
)


def _record(source: SourceDefinition, captured_at: str, record_type: str, values: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "record_type": record_type,
        "source_id": source.id,
        "source_url": source.url,
        "source_scope": _scope(source.url, source.scope),
        "observed_at": captured_at,
        **values,
    }
    stable = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    payload["record_id"] = f"{source.id}:{record_type}:{sha1(stable.encode('utf-8')).hexdigest()[:16]}"
    return payload


def _scope(url: str, configured_scope: str | None) -> str:
    host = urlparse(url).hostname or ""
    if host.startswith(("mf.", "kf.")):
        return "branch"
    if configured_scope:
        return configured_scope
    return "head_university"


def _first_label(labels: dict[str, str], *parts: str) -> str | None:
    lowered = [(key.casefold(), value) for key, value in labels.items()]
    matches = [(key, value) for key, value in lowered if all(part.casefold() in key for part in parts)]
    return min(matches, key=lambda item: len(item[0]))[1] if matches else None


def _row_values(row: dict[str, str]) -> list[str]:
    return [value.strip() for value in row.values() if value and value.strip()]


def _value_by_header(row: dict[str, str], *patterns: str) -> str | None:
    for key, value in row.items():
        if any(pattern.casefold() in key.casefold() for pattern in patterns) and value.strip():
            return value.strip()
    return None


def _infer_level(code: str | None) -> str | None:
    code = (code or "").replace(" ", "")
    if ".03." in code:
        return "бакалавриат"
    if ".04." in code:
        return "магистратура"
    if ".05." in code:
        return "специалитет"
    return None


_EDUCATION_CODE_RE = re.compile(r"(?<!\d)(?:\d{2}|\d)\.\d{2}\.\d{2}(?:-\d+)?(?!\d)")
_UNIT_PREFIXES = (
    "ИБМ", "ПИШ", "РКТ", "ФН", "РЛ", "РТ", "РК", "СГН", "СМ", "МТ", "ИУ",
    "АК", "БМТ", "ТБД", "ТИП", "ТБС", "ТЛА", "ТМО", "ТМР", "ТСА", "ТСР",
    "ТУС", "ТЭ", "Л", "ПС", "Э", "ЮР", "МОП",
)
_UNIT_CODE_RE = re.compile(
    r"(?<![А-ЯЁ])(" + "|".join(sorted(_UNIT_PREFIXES, key=len, reverse=True)) + r")(?:-?(\d{1,2}))?(?![А-ЯЁ])",
    re.IGNORECASE,
)


def _normalized_text(value: Any) -> str:
    return re.sub(r"\s+", " ", clean_text(value)).strip().casefold()


def _is_repeated_header(table: dict[str, Any], row: dict[str, str]) -> bool:
    """Не превращает повторённую строку заголовка в сущность."""
    comparable = [
        (str(header), str(row.get(header, "")))
        for header in table.get("headers", [])
        if row.get(header)
    ]
    if not comparable:
        return False
    equal = sum(_normalized_text(header) == _normalized_text(value) for header, value in comparable)
    return equal >= max(1, len(comparable) // 2)


def _education_code(value: Any) -> str | None:
    match = _EDUCATION_CODE_RE.search(clean_text(value))
    return match.group(0) if match else None


def _strip_code(value: str | None, code: str | None) -> str | None:
    if not value:
        return None
    text = clean_text(value)
    if code:
        text = re.sub(r"^\s*" + re.escape(code) + r"\s*", "", text, flags=re.IGNORECASE)
    return text.strip(" —:-") or None


def _unit_code(value: Any) -> str | None:
    match = _UNIT_CODE_RE.search(clean_text(value).upper())
    if not match:
        return None
    prefix, number = match.groups()
    return f"{prefix.upper()}-{number}" if number else prefix.upper()


def _unit_type(name: str) -> str:
    text = _normalized_text(name)
    if text.startswith(("ф-т", "факультет", "физкультурно-оздоровительный")):
        return "faculty"
    if "кафедр" in text:
        return "department"
    if "научно-учебн" in text and "комплекс" in text:
        return "complex"
    if "институт" in text:
        return "institute"
    if "школ" in text:
        return "school"
    if "центр" in text:
        return "center"
    if text.isupper() and len(text) > 3:
        return "section"
    return "unit"


def _raw_unit_values(row: dict[str, str]) -> dict[str, Any]:
    leader_name = _value_by_header(row, "фамили", "имя", "отчеств")
    role = _value_by_header(row, "должност")
    room = _value_by_header(row, "помещ")
    address = _value_by_header(row, "местонахожден")
    official_site = _value_by_header(row, "официального сайта")
    email = _value_by_header(row, "электронной почт")
    provision = _value_by_header(row, "положени")
    return {
        "leader_name": leader_name,
        "role": role,
        "room": room,
        "address": address,
        "official_site": official_site,
        "email": email,
        "provision": provision,
        "contacts": {"email": email} if email else {},
    }


def _code_records(source: SourceDefinition, page: Any, captured_at: str, record_type: str = "Program") -> list[dict[str, Any]]:
    """Разбирает карточки/таблицы с кодом, сохраняя исходную строку."""
    records: list[dict[str, Any]] = []
    for table in page.tables:
        for row_index, row in enumerate(table["rows"]):
            if _is_repeated_header(table, row):
                continue
            values = _row_values(row)
            code = next((value.replace(" ", "") for value in values if looks_like_code(value)), None)
            if not code:
                continue
            name = _value_by_header(row, "наименование", "название", "программа", "направление")
            if not name:
                code_index = values.index(next(value for value in values if value.replace(" ", "") == code))
                name = values[code_index + 1] if code_index + 1 < len(values) else None
            records.append(
                _record(
                    source,
                    captured_at,
                    record_type,
                    {
                        "code": code,
                        "name": _strip_code(name, code),
                        "level": _value_by_header(row, "уровень") or _infer_level(code),
                        "form": _value_by_header(row, "форма"),
                        "duration": _value_by_header(row, "срок", "продолж"),
                        "language": _value_by_header(row, "язык"),
                        "profile": _value_by_header(row, "профиль", "профил", "направленност"),
                        "faculty": _value_by_header(row, "факультет", "институт"),
                        "department": _value_by_header(row, "кафедр"),
                        "table_index": table["index"],
                        "row_index": row_index,
                        "table_context": table["context"],
                        "raw_values": row,
                        "is_data_row": True,
                    },
                )
            )
    return _dedupe_records(records)


def _education_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    """Строит три разных уровня: направление, программа и её реализация."""
    records: list[dict[str, Any]] = []
    for table in page.tables:
        if table.get("index") not in {1, 2, 3, 4, 5, 6}:
            continue
        for row_index, row in enumerate(table["rows"]):
            if _is_repeated_header(table, row):
                continue
            direction_cell = _value_by_header(row, "код и наименование специальности", "код и наименование направления", "код и наименование")
            direction_code = _education_code(direction_cell)
            if not direction_code:
                continue
            direction_name = _strip_code(direction_cell, direction_code) or direction_code
            profile = _value_by_header(row, "направленность", "профиль")
            education_code = _value_by_header(row, "код в эу", "код в эо")
            department_code = _value_by_header(row, "кафедр")
            form = _value_by_header(row, "форма обуч")
            duration = _value_by_header(row, "срок обуч", "нормативный срок")
            qualification = _value_by_header(row, "квалификац")
            raw_values = row
            common = {
                "direction_code": direction_code,
                "direction_name": direction_name,
                "program_code": education_code or direction_code,
                "department_code": department_code,
                "form": form,
                "duration": duration,
                "qualification": qualification,
                "profile": profile,
                "level": _infer_level(direction_code),
                "table_index": table["index"],
                "row_index": row_index,
                "table_context": table["context"],
                "raw_values": raw_values,
                "is_data_row": True,
            }
            records.append(_record(source, captured_at, "Direction", {
                "code": direction_code,
                "name": direction_name,
                "level": common["level"],
                "table_index": table["index"],
                "row_index": row_index,
                "raw_values": raw_values,
                "is_data_row": True,
            }))
            program_name = profile or direction_name
            records.append(_record(source, captured_at, "Program", {
                "code": education_code or direction_code,
                "direction_code": direction_code,
                "name": program_name,
                "profile": profile,
                "department_code": department_code,
                "level": common["level"],
                "form": form,
                "duration": duration,
                "table_index": table["index"],
                "row_index": row_index,
                "raw_values": raw_values,
                "is_data_row": True,
            }))
            records.append(_record(source, captured_at, "ProgramOffering", common))
    return _dedupe_records(records)


def _standard_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for table in page.tables:
        for row_index, row in enumerate(table["rows"]):
            if _is_repeated_header(table, row):
                continue
            code = _education_code(_value_by_header(row, "шифр", "код"))
            if not code:
                continue
            name = _value_by_header(row, "наименован")
            kind = next((header for header in table.get("headers", []) if any(token in header.casefold() for token in ("фгос", "суос", "стандарт"))), "standard")
            records.append(_record(source, captured_at, "DirectionStandard", {
                "direction_code": code,
                "code": code,
                "name": name or code,
                "standard_type": kind,
                "title": name or code,
                "table_index": table["index"],
                "row_index": row_index,
                "raw_values": row,
                "is_data_row": True,
            }))
    return _dedupe_records(records)


def _program_card_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    """Извлекает карточки направления, когда каталог отрисован без HTML-таблиц."""
    records: list[dict[str, Any]] = []
    code_pattern = re.compile(r"\b\d{2}\.\d{2}\.\d{2}\b")
    for link in page.links:
        match = code_pattern.search(link["text"])
        if not match:
            continue
        code = match.group(0)
        before_code = link["text"][: match.start()].strip(" —:-")
        name = re.sub(r"\s+", " ", before_code).strip()
        if not name:
            name = link["text"][match.end() :].strip(" —:-")
        records.append(
            _record(
                source,
                captured_at,
                "ProgramCard",
                {
                    "code": code,
                    "name": name,
                    "level": _infer_level(code),
                    "url": link["url"],
                    "form": None,
                    "profile": None,
                },
            )
        )
    return _dedupe_records(records)


def _next_data(page: Any) -> dict[str, Any] | None:
    """Return the server-side JSON model embedded by the BMSTU Next page."""
    script = page.soup.find("script", id="__NEXT_DATA__")
    if script is None:
        return None
    raw = script.string or script.get_text()
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _next_state(data: dict[str, Any] | None, key: str) -> dict[str, Any]:
    if not data:
        return {}
    props = data.get("props")
    initial = props.get("initialState") if isinstance(props, dict) else None
    value = initial.get(key) if isinstance(initial, dict) else None
    result = value.get("data") if isinstance(value, dict) else None
    return result if isinstance(result, dict) else {}


def _html_fragment(value: Any) -> str | None:
    if not value:
        return None
    from bs4 import BeautifulSoup

    return clean_text(BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)) or None


def _faculty_label(value: Any) -> tuple[str | None, str | None]:
    text = clean_text(value)
    match = re.match(r"^([А-ЯЁA-Z]{1,8})\s+(.+)$", text)
    if match:
        return match.group(2).strip(), match.group(1).upper()
    return text or None, None


def _faculty_index_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    state = _next_state(_next_data(page), "facultiesAndBranches")
    content = state.get("content") if isinstance(state, dict) else None
    if not isinstance(content, dict):
        return []
    records: list[dict[str, Any]] = []
    groups = [
        (content.get("faculties"), False),
        ((content.get("industryFaculties") or {}).get("faculties"), True),
    ]
    for items, industry in groups:
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            raw_name = clean_text(item.get("name"))
            name, abbreviation = _faculty_label(raw_name)
            slug = clean_text(item.get("slug"))
            detail_url = urljoin(page.links[0]["url"] if page.links else source.url, f"/faculty/{slug}") if slug and not slug.startswith("/") else (urljoin(source.url, slug) if slug else None)
            is_non_faculty = abbreviation in {"ВУЦ", "ГУИМЦ", "ФОФ", "ИСОТ", "МТКП"}
            records.append(_record(source, captured_at, "OrganizationUnit" if is_non_faculty else "Faculty", {
                "name": name or raw_name,
                "raw_name": raw_name,
                "code": abbreviation or clean_text(item.get("code")),
                "abbreviation": abbreviation or clean_text(item.get("code")),
                "url": detail_url,
                "slug": slug,
                "industry": bool(industry or item.get("is_industry_faculty")),
                "is_data_row": True,
            }))
    return _dedupe_records(records)


def _faculty_detail_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    state = _next_state(_next_data(page), "facultyDetails")
    title = clean_text(state.get("title"))
    faculty_name, faculty_code = _faculty_label(title)
    faculty_code = clean_text(state.get("code")) or faculty_code
    faculty_url = page.soup.find("link", rel="canonical")
    faculty_url_value = faculty_url.get("href") if faculty_url else page.links[0]["url"] if page.links else source.url
    records: list[dict[str, Any]] = []
    if title:
        records.append(_record(source, captured_at, "Faculty", {
            "name": faculty_name or title,
            "raw_name": title,
            "code": faculty_code,
            "abbreviation": faculty_code,
            "url": faculty_url_value,
            "description": _html_fragment(state.get("mainText")) or _html_fragment(state.get("about")),
            "is_industry_faculty": bool(state.get("is_industry_faculty")),
            "is_data_row": True,
        }))
    chairs = state.get("chairs")
    for chair in chairs if isinstance(chairs, list) else []:
        if not isinstance(chair, dict) or not chair.get("title"):
            continue
        chair_name, chair_code = _faculty_label(chair.get("title"))
        slug = clean_text(chair.get("slug"))
        records.append(_record(source, captured_at, "Department", {
            "name": chair_name or clean_text(chair.get("title")),
            "raw_name": clean_text(chair.get("title")),
            "code": chair_code,
            "abbreviation": chair_code,
            "faculty_name": faculty_name or title,
            "faculty_code": faculty_code,
            "parent_name": faculty_name or title,
            "parent_relation": "published",
            "url": urljoin(page.links[0]["url"] if page.links else source.url, f"/chair/{slug}") if slug else None,
            "description": _html_fragment(chair.get("text")),
            "is_data_row": True,
        }))
    return _dedupe_records(records)


def _program_card_from_api(source: SourceDefinition, item: dict[str, Any], captured_at: str) -> dict[str, Any] | None:
    code = clean_text(item.get("code"))
    name = clean_text(item.get("name"))
    slug = clean_text(item.get("slug"))
    if not code or not name or not slug:
        return None
    return _record(source, captured_at, "ProgramCard", {
        "code": code,
        "name": name,
        "level": _infer_level(code),
        "qualification": clean_text(item.get("qualification")),
        "url": f"https://bmstu.ru/bachelor/majors/{slug}",
        "faculties": item.get("faculties") if isinstance(item.get("faculties"), list) else [],
        "is_data_row": True,
    })


def _program_api_records(source: SourceDefinition, resource: FetchedResource, captured_at: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(resource.body.decode(resource.encoding or "utf-8", errors="replace"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    items = payload.get("data") if isinstance(payload, dict) else None
    records: list[dict[str, Any]] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        card = _program_card_from_api(source, item, captured_at)
        if card:
            records.append(card)
    return _dedupe_records(records)


def _program_detail_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    state = _next_state(_next_data(page), "bachelorMajorsDetails")
    if not state.get("slug") or not isinstance(state.get("additional"), dict):
        return []
    additional = state["additional"]
    direction_code = clean_text(additional.get("code"))
    direction_name = clean_text(additional.get("name"))
    description = _html_fragment(state.get("description"))
    chairs = state.get("chairs") if isinstance(state.get("chairs"), dict) else {}
    first_chair = next((item for item in chairs.get("items", []) if isinstance(item, dict)), {})
    faculty = first_chair.get("faculty") if isinstance(first_chair.get("faculty"), dict) else {}
    faculty_name = clean_text(faculty.get("title"))
    faculty_code = clean_text(faculty.get("code"))
    department_name = clean_text(first_chair.get("title"))
    department_code = clean_text(first_chair.get("code"))
    if department_name:
        department_name, department_code_from_title = _faculty_label(department_name)
        department_code = department_code or department_code_from_title
    page_url = page.soup.find("link", rel="canonical")
    page_url_value = page_url.get("href") if page_url else (page.links[0]["url"] if page.links else source.url)
    common = {
        "direction_code": direction_code,
        "direction_name": direction_name,
        "description": description,
        "level": _infer_level(direction_code),
        "form": clean_text(additional.get("studyForm")) or "Очная",
        "duration": clean_text(additional.get("studyPeriod")),
        "qualification": clean_text(additional.get("qualification")),
        "vuc": bool(additional.get("military")),
        "faculty": faculty_name,
        "faculty_code": faculty_code,
        "faculty_url": f"https://bmstu.ru/faculty/{faculty.get('slug')}" if faculty.get("slug") else None,
        "department": department_name,
        "department_code": department_code,
        "department_url": f"https://bmstu.ru/chair/{first_chair.get('slug')}" if first_chair.get("slug") else None,
        "url": page_url_value,
        "is_data_row": True,
    }
    records: list[dict[str, Any]] = []
    records.append(_record(source, captured_at, "Direction", {
        "code": direction_code,
        "name": direction_name,
        "level": common["level"],
        "url": page_url_value,
        "description": description,
        "is_data_row": True,
    }))
    records.append(_record(source, captured_at, "Program", {
        "code": direction_code,
        "name": direction_name,
        "direction_code": direction_code,
        "profile": None,
        **common,
    }))
    for place in state.get("places", []) if isinstance(state.get("places"), list) else []:
        if not isinstance(place, dict):
            continue
        title = _normalized_text(place.get("title"))
        count = parse_number(place.get("count"))
        if count is None:
            continue
        records.append(_record(source, captured_at, "Admission", {
            "direction_code": direction_code,
            "program_code": direction_code,
            "year": 2026,
            "place_type": "budget" if "бюджет" in title else "paid" if "плат" in title else title,
            "count": count,
            "is_data_row": True,
        }))
    old_points = additional.get("oldPoints") if isinstance(additional.get("oldPoints"), dict) else {}
    for year, point in old_points.items():
        if not isinstance(point, dict):
            continue
        for kind, field in (("budget", "budget"), ("paid", "paid"), ("average", "average")):
            value = parse_number(point.get(kind))
            if value is None:
                continue
            records.append(_record(source, captured_at, "Admission", {
                "direction_code": direction_code,
                "program_code": direction_code,
                "year": int(year) if str(year).isdigit() else year,
                "score_type": field,
                "score": value,
                "is_data_row": True,
            }))
    for point in state.get("points", []) if isinstance(state.get("points"), list) else []:
        if not isinstance(point, dict):
            continue
        score = parse_number(point.get("point"))
        if score is None:
            continue
        records.append(_record(source, captured_at, "Admission", {
            "direction_code": direction_code,
            "program_code": direction_code,
            "year": 2026,
            "exam": clean_text(point.get("title")),
            "minimum_score": score,
            "is_choice": bool(point.get("isChoice")),
            "is_data_row": True,
        }))
    for price in state.get("price", []) if isinstance(state.get("price"), list) else []:
        if not isinstance(price, dict):
            continue
        for amount_key, amount_type in (("value", "regular"), ("discountValue", "discount") ):
            amount = parse_number(price.get(amount_key))
            if amount is None:
                continue
            records.append(_record(source, captured_at, "Tuition", {
                "code": direction_code,
                "direction_code": direction_code,
                "program_code": direction_code,
                "year": 2026,
                "academic_year": "2026/2027",
                "price": amount,
                "price_type": amount_type,
                "currency": clean_text(price.get("currency")) or "RUB",
                "form": clean_text(price.get("studyForm")),
                "condition": clean_text(price.get("term")),
                "is_data_row": True,
            }))
    programs = chairs.get("items") if isinstance(chairs.get("items"), list) else []
    for chair in programs:
        if not isinstance(chair, dict):
            continue
        for program in (chair.get("educationalProgram", {}) or {}).get("items", []) if isinstance(chair.get("educationalProgram"), dict) else []:
            if not isinstance(program, dict):
                continue
            profile_code = clean_text(program.get("code"))
            records.append(_record(source, captured_at, "ProgramProfile", {
                "program_code": profile_code or direction_code,
                "direction_code": direction_code,
                "name": clean_text(program.get("name")),
                "profile": clean_text(program.get("name")),
                "profile_code": profile_code,
                "place": clean_text(program.get("place")),
                "description": _html_fragment(program.get("description")),
                "study_plan_url": clean_text(program.get("plan")),
                "url": clean_text(program.get("plan")),
                "title": clean_text(program.get("name")) or "Учебный план",
                "faculty": faculty_name,
                "department": department_name,
                "is_data_row": True,
            }))
    return _dedupe_records(records)


def _dedupe_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for record in records:
        key = (
            record.get("record_type"),
            record.get("source_id"),
            record.get("code"),
            record.get("name"),
            record.get("url"),
            record.get("document_url"),
            record.get("row_no"),
            record.get("applicant_id"),
            record.get("program_code"),
            record.get("direction_code"),
            record.get("discipline"),
            record.get("semester"),
            record.get("course"),
            record.get("profile_code"),
            record.get("source_document_url"),
            record.get("place_type"),
            record.get("score_type"),
            record.get("exam"),
            record.get("minimum_score"),
            record.get("price_type"),
            record.get("year"),
            record.get("academic_year"),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def _document_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for link in page.links:
        url = link["url"]
        lowered = url.casefold()
        text = link["text"]
        if not (
            lowered.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx"))
            or "документ" in text.casefold()
            or "приём" in text.casefold()
            or "прием" in text.casefold()
        ):
            continue
        combined = f"{text} {url}"
        years = extract_years(combined)
        records.append(
            _record(
                source,
                captured_at,
                "Document",
                {
                    "title": text or url.rsplit("/", 1)[-1],
                    "url": url,
                    "document_type": (
                        urlparse(url).path.casefold().rsplit(".", 1)[-1]
                        if "." in urlparse(url).path.rsplit("/", 1)[-1]
                        else "html"
                    ),
                    "admission_year": years[-1] if years else None,
                    "published_at": None,
                },
            )
        )
    return _dedupe_records(records)


def _university_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    title = page.soup.find("h1") or page.soup.find("title")
    title_text = title.get_text(" ", strip=True) if title else None
    name_full = _first_label(page.labels, "полное", "наимен") or _first_label(page.labels, "наимен") or title_text
    name_short = _first_label(page.labels, "сокращ", "наимен")
    location = _first_label(page.labels, "местонахождение") or _first_label(page.labels, "адрес")
    city = None
    if location:
        city_match = re.search(r"(?:г\.|город)\s*([^,]+)", location, re.IGNORECASE)
        city = city_match.group(1).strip() if city_match else None
    contact_text = _first_label(page.labels, "контактные", "телефон") or page.text
    emails = extract_emails(contact_text)
    phones = extract_phones(contact_text)
    founder = _first_label(page.labels, "учредитель")
    ownership = (
        "государственный"
        if founder and re.search(r"министер|российск(?:ой|ая) федераци", founder, re.IGNORECASE)
        else None
    )
    if not any((name_full, name_short, location, city, emails, phones, page.labels)):
        return []
    return [
        _record(
            source,
            captured_at,
            "University",
            {
                "name_full": name_full,
                "name_short": name_short,
                "type": "университет",
                "city": city,
                "address": location,
                "official_site": "https://bmstu.ru/",
                "contacts": {"emails": emails, "phones": phones},
                "license": _first_label(page.labels, "лиценз"),
                "accreditation": _first_label(page.labels, "аккредит"),
                "founder": founder,
                "ownership": ownership,
                "labels": page.labels,
            },
        )
    ]


def _organization_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for table in page.tables:
        for row_index, row in enumerate(table["rows"]):
            if _is_repeated_header(table, row):
                continue
            name = _value_by_header(row, "наименование структурного подразделения")
            if not name:
                continue
            unit_type = _unit_type(name)
            fields = _raw_unit_values(row)
            if unit_type == "section":
                record_type = "StructuralSection"
            elif unit_type == "department":
                record_type = "Department"
            elif unit_type in {"faculty", "institute", "school"}:
                record_type = "Faculty"
            elif unit_type == "complex":
                record_type = "OrganizationalComplex"
            else:
                record_type = "OrganizationUnit"
            embedded_parent = None
            parent_match = re.search(r"НУК\s*[\"«](.+?)[\"»]", name, re.IGNORECASE)
            if parent_match:
                embedded_parent = parent_match.group(1).strip()
            records.append(
                _record(
                    source,
                    captured_at,
                    record_type,
                    {
                        "name": name,
                        "unit_type": unit_type,
                        "code": _unit_code(name),
                        "parent_name": embedded_parent,
                        "table_index": table["index"],
                        "row_index": row_index,
                        "raw_values": row,
                        "is_data_row": True,
                        **fields,
                    },
                )
            )

    records = _dedupe_records(records)
    faculties = [record for record in records if record.get("record_type") == "Faculty"]
    faculty_by_code = {
        str(record.get("code")): record.get("name")
        for record in faculties
        if record.get("code")
    }
    for record in records:
        if record.get("record_type") != "Department":
            continue
        code = str(record.get("code") or "")
        prefix = code.split("-", 1)[0]
        if prefix in faculty_by_code and not record.get("parent_name"):
            record["parent_name"] = faculty_by_code[prefix]
            record["parent_relation"] = "derived_code_prefix"
    return records


def _cost_records(source: SourceDefinition, page: Any, captured_at: str, record_type: str = "Tuition") -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for table in page.tables:
        context = f"{table.get('caption', '')} {table.get('context', '')}"
        years = extract_years(context)
        academic_year = None
        year_match = re.search(r"(20\d{2})\s*/\s*(20\d{2})", context)
        if year_match:
            academic_year = f"{year_match.group(1)}/{year_match.group(2)}"
        for row_index, row in enumerate(table["rows"]):
            if _is_repeated_header(table, row):
                continue
            values = _row_values(row)
            code = next((value.replace(" ", "") for value in values if looks_like_code(value)), None)
            if not code:
                continue
            name = _value_by_header(row, "наименование", "название")
            if not name:
                code_position = next(index for index, value in enumerate(values) if value.replace(" ", "") == code)
                name = values[code_position + 1] if code_position + 1 < len(values) else None
            price_text = _value_by_header(row, "цена", "стоимость", "руб")
            # Do not treat an arbitrary number (minimum score, place count,
            # year) as tuition. A cost record requires an explicit price
            # column in the source table.
            if price_text is None:
                continue
            price = parse_number(price_text)
            if price is None:
                continue
            records.append(
                _record(
                    source,
                    captured_at,
                    record_type,
                    {
                        "academic_year": academic_year,
                        "year": int(year_match.group(1)) if year_match else (years[0] if len(years) == 1 else None),
                        "code": code,
                        "name": name,
                        "level": _infer_level(code),
                        "price": price,
                        "currency": "RUB",
                        "table_index": table["index"],
                        "row_index": row_index,
                        "raw_values": row,
                        "is_data_row": True,
                    },
                )
            )
    return _dedupe_records(records)


def _generic_row_records(source: SourceDefinition, page: Any, captured_at: str, record_type: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for table in page.tables:
        for row_index, row in enumerate(table["rows"]):
            if _is_repeated_header(table, row):
                continue
            values = _row_values(row)
            if not values:
                continue
            records.append(
                _record(
                    source,
                    captured_at,
                    record_type,
                    {
                        "values": row,
                        "name": values[0],
                        "year": next((int(value) for value in values if re.fullmatch(r"20\d{2}", value)), None),
                        "table_index": table["index"],
                        "row_index": row_index,
                        "table_context": table["context"],
                        "raw_values": row,
                        "is_data_row": True,
                    },
                )
            )
    return _dedupe_records(records)


def _international_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for table in page.tables:
        for row_index, row in enumerate(table["rows"]):
            if _is_repeated_header(table, row):
                continue
            partner_name = _value_by_header(row, "наименовани")
            country = _value_by_header(row, "стран")
            if not partner_name or partner_name.casefold() in {"наименование организации", "организация"}:
                continue
            agreement = _value_by_header(row, "реквизит", "соглашен")
            agreement_date = _value_by_header(row, "дат")
            validity = _value_by_header(row, "срок действ")
            common = {
                "name": partner_name,
                "partner_name": partner_name,
                "country": country,
                "agreement_type": agreement,
                "agreement_date": agreement_date,
                "validity": validity,
                "table_index": table["index"],
                "row_index": row_index,
                "table_context": table["context"],
                "raw_values": row,
                "is_data_row": True,
            }
            records.append(_record(source, captured_at, "InternationalPartner", common))
            records.append(_record(source, captured_at, "PartnerRelation", common))
    return _dedupe_records(records)


def _course_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for table in page.tables:
        for row_index, row in enumerate(table["rows"]):
            if _is_repeated_header(table, row):
                continue
            direction_code = _value_by_header(row, "шифр", "код")
            name = _value_by_header(row, "направлен")
            if not direction_code or not name or not _education_code(direction_code):
                continue
            records.append(_record(source, captured_at, "Course", {
                "name": name,
                "direction_code": _education_code(direction_code),
                "department_code": _value_by_header(row, "кафедр"),
                "eor_code": _value_by_header(row, "эор"),
                "table_index": table["index"],
                "row_index": row_index,
                "table_context": table["context"],
                "raw_values": row,
                "is_data_row": True,
            }))
    return _dedupe_records(records)


def _feature_records(source: SourceDefinition, page: Any, captured_at: str) -> list[dict[str, Any]]:
    text = _normalized_text(page.text)
    if "военный учебный центр" not in text and "воуц" not in text:
        return []
    return [_record(source, captured_at, "UniversityFeature", {
        "feature": "Военный учебный центр",
        "name": "Военный учебный центр",
        "available": True,
        "is_data_row": True,
    })]


def _link_records(source: SourceDefinition, page: Any, captured_at: str, record_type: str, keywords: tuple[str, ...]) -> list[dict[str, Any]]:
    """Turns meaningful catalogue links into auditable records.

    Some BMSTU contours are link catalogues rather than HTML tables (notably
    the olympiad site). Keeping the link and its label is more honest and more
    useful than reporting that the source contained no data.
    """
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for link in page.links:
        label = clean_text(link.get("text"))
        url = str(link.get("url") or "")
        combined = f"{label} {url}".casefold()
        if not label or not any(keyword.casefold() in combined for keyword in keywords):
            continue
        key = (label, url)
        if key in seen:
            continue
        seen.add(key)
        records.append(_record(source, captured_at, record_type, {
            "name": label,
            "title": label,
            "url": url,
            "link_text": label,
            "is_data_row": True,
        }))
    return records


def _network_records(source: SourceDefinition, payloads: list[dict[str, Any]], captured_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for payload in payloads:
        raw = payload.get("body")
        if not isinstance(raw, str):
            continue
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for item in _walk_json(decoded):
            if not isinstance(item, dict) or len(item) < 2:
                continue
            keys = " ".join(str(key).casefold() for key in item)
            admission_keys = ("applicant", "заяв", "балл", "priority", "приоритет", "enroll", "зачис")
            is_admission_payload = any(token in keys for token in admission_keys)
            is_list_document = (
                source.id in {"S07", "S08"}
                and "href" in item
                and any(key in item for key in ("title", "name", "shortTitle"))
            )
            if not is_admission_payload and not is_list_document:
                continue
            record_type = "AdmissionRow" if source.id == "S07" else "EnrollmentRow"
            title = item.get("title") or item.get("name") or item.get("shortTitle")
            href = item.get("href")
            if isinstance(href, str):
                href = urljoin(source.url, href)
            records.append(
                _record(
                    source,
                    captured_at,
                    record_type,
                    {
                        "values": item,
                        "name": title,
                        "title": title,
                        "url": href,
                        "network_url": payload.get("url"),
                    },
                )
            )
    return _dedupe_records(records)


def _pdf_admission_records(
    source: SourceDefinition,
    resource: FetchedResource,
    text: str,
    captured_at: str,
) -> list[dict[str, Any]]:
    """Извлекает строки конкурсных/зачислительных PDF в каноническую форму."""
    if source.id not in {"S07", "S08"}:
        return []
    record_type = "AdmissionRow" if source.id == "S07" else "EnrollmentRow"
    document_url = resource.final_url or resource.requested_url
    admission_year = extract_admission_year(text)
    records: list[dict[str, Any]] = []

    if source.id == "S08" or "/orders/" in document_url.casefold():
        for row in iter_order_rows(text):
            records.append(
                _record(
                    source,
                    captured_at,
                    "EnrollmentRow",
                    {"document_url": document_url, "admission_year": admission_year, **row},
                )
            )
        return _dedupe_records(records)

    if "/registered/" in document_url.casefold():
        for row in iter_registered_rows(text):
            records.append(
                _record(
                    source,
                    captured_at,
                    "AdmissionRow",
                    {
                        "document_url": document_url,
                        "admission_year": admission_year,
                        "programs": " ".join(row.pop("raw_parts", [])),
                        **row,
                    },
                )
            )
        return _dedupe_records(records)

    # Registered lists and current competition lists are real PDF tables.
    # The first row is the header; column names vary between campaign years,
    # so retain raw cells and only normalize stable numeric/code values.
    code_pattern = re.compile(r"\b\d{2}\.\d{2}\.\d{2}\b")
    for table in extract_pdf_tables(resource.body):
        rows = table["rows"]
        for row in rows[1:]:
            if not row or not re.search(r"\d", row[0]):
                continue
            row_number_match = re.search(r"\d+", row[0])
            if not row_number_match:
                continue
            joined = " ".join(row)
            applicant_numbers = re.findall(r"\b\d{5,8}\b", joined)
            codes = code_pattern.findall(joined)
            values: dict[str, Any] = {
                "document_url": document_url,
                "admission_year": admission_year,
                "row_no": int(row_number_match.group(0)),
                "raw_cells": row,
                "applicant_id": applicant_numbers[0] if applicant_numbers else None,
                "program_code": codes[0] if codes else None,
                "is_data_row": True,
                "page": table["page"],
            }
            if source.id == "S07" and "/registered/" in document_url.casefold():
                values["programs"] = row[-1] if row else None
            else:
                numeric_values = [
                    int(match.group(0).rstrip("*"))
                    for cell in row[2:]
                    for match in re.finditer(r"\b\d{1,3}\*?\b", cell)
                ]
                if numeric_values:
                    values["score"] = numeric_values[0]
                    values["score_subjects"] = numeric_values[1:]
                values["status"] = row[2] if len(row) > 2 else None
            records.append(_record(source, captured_at, record_type, values))
    return _dedupe_records(records)


def _pdf_layout_text(body: bytes) -> str:
    """Extract text with Poppler when available.

    BMSTU study-plan PDFs use a font encoding that fitz/pdfplumber expose as
    replacement characters. Poppler's text layer preserves the Cyrillic and
    the fixed column layout, so it is the preferred reader for this document
    family. The normal PDF reader remains the portable fallback.
    """
    executable = shutil.which("pdftotext")
    if not executable:
        for candidate in (
            r"C:\\poppler-24.08.0\\Library\\bin\\pdftotext.exe",
            r"C:\\Program Files\\poppler\\Library\\bin\\pdftotext.exe",
        ):
            if shutil.which(candidate):
                executable = candidate
                break
    if not executable:
        return ""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
        handle.write(body)
        pdf_path = handle.name
    try:
        result = subprocess.run(
            [executable, "-layout", "-enc", "UTF-8", pdf_path, "-"],
            capture_output=True,
            timeout=60,
            check=False,
        )
        return result.stdout.decode("utf-8", errors="replace").strip()
    except (OSError, subprocess.SubprocessError):
        return ""
    finally:
        try:
            import os

            os.unlink(pdf_path)
        except OSError:
            pass


_PLAN_PROFILE_CODE_RE = re.compile(r"(?<!\d)(\d{1,2}\.\d{2}\.\d{2})\s*([\-–—/])\s*(\d{1,3})(?!\d)")


def _canonical_plan_code(value: Any) -> str:
    """Normalise profile separators without changing slash-based codes."""
    return re.sub(r"\s+", "", clean_text(value)).replace("–", "-").replace("—", "-")


def _plan_header_value(line: str) -> str | None:
    parts = re.split(r"\s+[—–]\s+", line, maxsplit=1)
    return clean_text(parts[1]) if len(parts) == 2 else None


def _plan_header(lines: list[str]) -> dict[str, Any]:
    direction_line = next((line for line in lines[:35] if "Направление подготовки" in line), "")
    profile_line = next((line for line in lines[:35] if re.search(r"\bПрофиль\b", line)), "")
    qualification_line = next((line for line in lines[:35] if "Квалификация" in line), "")
    duration_line = next((line for line in lines[:35] if "Срок обучения" in line), "")
    form_line = next((line for line in lines[:35] if "Форма обучения" in line), "")
    faculty_line = next((line for line in lines[:35] if "Факультет" in line), "")
    department_line = next((line for line in lines[:35] if "Кафедра" in line), "")

    direction_value = _plan_header_value(direction_line) or ""
    direction_code = _education_code(direction_value or direction_line)
    direction_name = direction_value
    if direction_code:
        direction_name = re.sub(rf"^\s*{re.escape(direction_code)}\s*,?\s*", "", direction_value).strip() or None

    profile_value = _plan_header_value(profile_line) or ""
    profile_match = _PLAN_PROFILE_CODE_RE.search(profile_value)
    profile_code = _canonical_plan_code(profile_match.group(0)) if profile_match else None
    profile_name = _PLAN_PROFILE_CODE_RE.sub("", profile_value).strip(" ,—–-") or None

    duration_value = _plan_header_value(duration_line) or ""
    year_match = re.search(r"Год начала обучения\s*[—–-]\s*(20\d{2})", duration_line)
    duration_match = re.search(r"Срок обучения\s*[—–-]\s*(.*?)(?=\s+Год начала обучения|\s*$)", duration_line)
    return {
        "direction_code": direction_code,
        "direction_name": direction_name,
        "program_profile_code": profile_code,
        "program_profile": profile_name,
        "qualification": _plan_header_value(qualification_line),
        "duration": duration_match.group(1).strip() if duration_match else duration_value or None,
        "education_year": int(year_match.group(1)) if year_match else None,
        "form": _plan_header_value(form_line),
        "faculty": _plan_header_value(faculty_line),
        "department": _plan_header_value(department_line),
    }


def _semester_columns(header: str) -> tuple[list[int], list[int | None]]:
    matches = list(re.finditer(r"Семестр\s+(\d+)\s*-\s*(\d+)\s+нед", header))
    starts = [max(0, match.start() - 4) for match in matches[:12]]
    weeks = [int(match.group(2)) for match in matches[:12]]
    return starts, weeks


def _numeric_values(value: str) -> list[int | float]:
    return [parse_number(item) for item in re.findall(r"-?\d+(?:[.,]\d+)?", value)]


def _study_plan_semester_summary(lines: list[str]) -> list[dict[str, Any]]:
    marker = next((index for index, line in enumerate(lines) if "IV. РАСПРЕДЕЛЕНИЕ ПО СЕМЕСТРАМ" in line), None)
    if marker is None:
        return []
    header_index = next((index for index in range(marker, min(len(lines), marker + 8)) if "Семестр 1" in lines[index]), None)
    if header_index is None:
        return []
    starts, weeks = _semester_columns(lines[header_index])
    if not starts:
        plain_matches = list(re.finditer(r"Семестр\s+(\d+)", lines[header_index]))
        starts = [max(0, match.start() - 4) for match in plain_matches[:12]]
        week_header = next(
            (line for line in lines[:marker] if "Семестр 1" in line and "нед" in line),
            "",
        )
        _, weeks = _semester_columns(week_header)
        weeks = weeks[: len(starts)] if weeks else [None] * len(starts)
    if not starts:
        return []
    metric_names = {
        "трудоемкость в неделю": "weekly_hours",
        "аудиторные занятия в неделю": "weekly_audited_hours",
        "количество курсовых работ": "coursework_count",
        "количество курсовых проектов": "course_project_count",
        "количество зачетов": "credits_control_count",
        "количество экзаменов": "exam_count",
        "государственный экзамен": "state_exam_count",
        "квалификационная работа": "vkr_defense_count",
    }
    metrics: dict[str, list[int | float | None]] = {}
    for line in lines[header_index + 1 :]:
        label = _normalized_text(line[: starts[0]])
        if not label:
            continue
        metric = next((name for fragment, name in metric_names.items() if fragment in label), None)
        if not metric:
            if "стр " in label:
                break
            continue
        values: list[int | float | None] = []
        numbers = _numeric_values(line)
        for index in range(len(starts)):
            values.append(numbers[index] if index < len(numbers) else None)
        metrics[metric] = values
    result: list[dict[str, Any]] = []
    for index, week_count in enumerate(weeks, start=1):
        item = {
            "semester": index,
            "course": (index + 1) // 2,
            "weeks": week_count,
        }
        for key, values in metrics.items():
            item[key] = values[index - 1] if index - 1 < len(values) else None
        result.append(item)
    return result


def _study_plan_overall_totals(lines: list[str], first_semester_start: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for index, line in enumerate(lines):
        if "Общая трудоемкость основной образовательной" not in line:
            continue
        values = _numeric_values(line[:first_semester_start])
        if len(values) < 7:
            continue
        label = " ".join(lines[index : index + 2])
        key = "overall_astronomical" if "астрономических" in label else "overall_academic"
        result[key] = {
            "total_credits": values[0],
            "total_hours": values[1],
            "audited_hours": values[2],
            "lectures": values[3],
            "practices": values[4],
            "labs": values[5],
            "self_study": values[6],
        }
    return result


def _study_plan_records(
    source: SourceDefinition,
    resource: FetchedResource,
    captured_at: str,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Parse a BMSTU study-plan PDF into header, summary and semester rows.

    The PDF is a fixed-width A3 table.  A discipline has one total workload
    block followed by one compact block per semester: ZET, hours, audited
    hours, self-study and the control type.  The previous parser copied the
    total lecture/practice/lab values into every semester and associated a
    plan with the first profile of a direction.  Keep those values as totals,
    but make the semester data explicit and preserve the PDF's own profile
    code so the projection can link the document to the right programme.
    """
    context = context or {}
    text = _pdf_layout_text(resource.body)
    if not text or "ПЛАН УЧЕБНОГО ПРОЦЕССА" not in text:
        return []
    lines = text.splitlines()
    plan_header = _plan_header(lines)
    direction_code = plan_header.get("direction_code") or context.get("direction_code")
    profile_code = plan_header.get("program_profile_code") or context.get("profile_code")
    profile_name = plan_header.get("program_profile") or context.get("program_profile") or context.get("title")
    faculty = plan_header.get("faculty")
    department = plan_header.get("department")
    form = plan_header.get("form")

    header_index = next((index for index, line in enumerate(lines) if "Шифр" in line and "Семестр 1" in line), None)
    if header_index is None:
        return []
    # The PDF repeats the plan header on every page, but the fixed-width
    # coordinates are not identical on all pages. Keep a separate set of
    # semester columns for every repeated header; otherwise page 2/3 rows are
    # sliced with page 1 coordinates and most of their semester cells vanish.
    table_headers = [
        (index, line)
        for index, line in enumerate(lines)
        if "Шифр" in line and "Семестр 1" in line
    ]
    if not table_headers:
        table_headers = [(header_index, lines[header_index])]
    plan_end = next(
        (
            index
            for index, line in enumerate(lines[header_index + 1 :], start=header_index + 1)
            if "IV. РАСПРЕДЕЛЕНИЕ ПО СЕМЕСТРАМ" in line
        ),
        len(lines),
    )
    sections: list[tuple[int, int, list[int], list[int | None]]] = []
    for section_index, (section_header_index, section_header) in enumerate(table_headers):
        if section_header_index >= plan_end:
            continue
        section_end = min(
            table_headers[section_index + 1][0] if section_index + 1 < len(table_headers) else plan_end,
            plan_end,
        )
        starts, weeks = _semester_columns(section_header)
        if len(starts) < 1:
            starts = [193 + index * 35 for index in range(12)]
            weeks = [None] * len(starts)
        sections.append((section_header_index + 1, section_end, starts[:12], weeks[:12]))
    if not sections:
        return []
    semester_starts = sections[0][2]
    semester_weeks = sections[0][3]
    number_re = re.compile(r"-?\d+(?:[.,]\d+)?")
    records: list[dict[str, Any]] = []
    summary_semesters = _study_plan_semester_summary(lines)
    overall_totals = _study_plan_overall_totals(lines, semester_starts[0])
    summary_record = {
        **plan_header,
        "program_code": profile_code or direction_code,
        "direction_code": direction_code,
        "program_profile_code": profile_code,
        "program_profile": profile_name,
        "study_plan_url": context.get("study_plan_url") or context.get("document_url"),
        "download_url": context.get("download_url") or resource.final_url,
        "source_document_url": context.get("document_url") or resource.requested_url,
        "semester_count": len(semester_starts),
        "semester_weeks": semester_weeks,
        "semesters": summary_semesters,
        **overall_totals,
        "is_data_row": True,
    }
    records.append(_record(source, captured_at, "StudyPlanSummary", summary_record))

    for section_start, section_end, section_starts, section_weeks in sections:
        # Re-anchor every semester to the actual number positions observed in
        # this page section. This handles both empty early semesters and the
        # small horizontal shifts in the repeated PDF table header.
        observed_positions: list[list[int]] = [[] for _ in section_starts]
        for line in lines[section_start:section_end]:
            if not re.match(r"^\s*\d+\s+", line):
                continue
            positions = [match.start() for match in number_re.finditer(line)]
            for index, expected in enumerate(section_starts):
                # Do not borrow the last total-workload value from the column
                # immediately to the left. It can sit 8–12 characters before
                # a semester header and would shift the whole page backwards.
                nearby = [position for position in positions if expected - 5 <= position <= expected + 16]
                if nearby:
                    observed_positions[index].append(min(nearby))
        aligned_starts = [
            sorted(values)[len(values) // 2] if values else start
            for start, values in zip(section_starts, observed_positions)
        ]

        for line_index in range(section_start, section_end):
            line = lines[line_index]
            stripped = line.strip()
            if not stripped or stripped.startswith("стр "):
                continue
            row_match = re.match(r"^\s*(\d+)\s+", line)
            if not row_match:
                continue

            # Locate the seven total-workload values by their numeric pattern,
            # rather than by the old hard-coded [80:193] slice. The table
            # shifts on later pages and the old slice dropped valid rows.
            first_semester_start = aligned_starts[0] if aligned_starts else len(line)
            matches = [
                match
                for match in number_re.finditer(line)
                if match.start() >= 55 and match.start() < first_semester_start
            ]
            total_match_index: int | None = None
            total_values: list[int | float | None] = []
            for candidate_index in range(max(0, len(matches) - 6)):
                candidate = matches[candidate_index : candidate_index + 7]
                if len(candidate) < 7:
                    continue
                values = [parse_number(item.group(0)) for item in candidate]
                credits, hours = values[0], values[1]
                if credits is None or hours is None:
                    continue
                if not (0 <= float(credits) <= 100 and float(hours) >= 0):
                    continue
                if float(hours) and float(hours) % 36:
                    continue
                if candidate[-1].end() > first_semester_start:
                    continue
                total_match_index = candidate_index
                total_values = values
                break

            # Some rows intentionally leave total ZET blank. Preserve
            # their remaining total columns instead of dropping the discipline.
            if not total_values:
                fallback = matches[-6:]
                if len(fallback) >= 6:
                    total_values = [parse_number(item.group(0)) for item in fallback]
                    total_values = [None] + total_values
                elif len(fallback) == 5:
                    values = [parse_number(item.group(0)) for item in fallback]
                    total_values = [None, values[0], values[1], values[2], values[3], 0, values[4]]
                if total_values:
                    total_match_index = len(matches) - len(fallback)
            if len(total_values) < 7:
                continue

            row_no = int(row_match.group(1))
            total_start = matches[total_match_index].start() if total_match_index is not None else first_semester_start
            prefix = line[row_match.end() : total_start]
            prefix_tokens = list(re.finditer(r"\S+", prefix))
            chair_match = next(
                (
                    token
                    for token in reversed(prefix_tokens)
                    if len(token.group(0)) <= 8
                    and token.group(0).upper() == token.group(0)
                    and re.fullmatch(r"[A-ZА-ЯЁ][A-ZА-ЯЁ0-9]{0,7}", token.group(0))
                ),
                None,
            )
            name_end = chair_match.start() if chair_match else len(prefix)
            name = clean_text(prefix[:name_end])
            chair = clean_text(prefix[chair_match.start() : chair_match.end()]) if chair_match else None
            # Long discipline names are wrapped onto the next physical line.
            continuation_index = line_index + 1
            while continuation_index < section_end:
                continuation = lines[continuation_index]
                if re.match(r"^\s*\d+\s+", continuation) or continuation.strip().startswith("стр "):
                    break
                continuation_prefix = continuation[:total_start].strip()
                if not continuation_prefix:
                    if continuation.strip():
                        break
                    continuation_index += 1
                    continue
                if number_re.search(continuation_prefix):
                    break
                normalized_continuation = _normalized_text(continuation_prefix)
                if normalized_continuation.startswith((
                    "вариативная часть",
                    "обязательная часть",
                    "фундаментальная",
                    "дисциплины",
                    "общая трудоемкость",
                )):
                    break
                name = clean_text(f"{name} {continuation_prefix}")
                continuation_index += 1
            if not name or name.casefold() in {"дисциплины (модули)", "дисциплины по выбору"}:
                continue

            total = {
                "total_credits": total_values[0],
                "total_hours": total_values[1],
                "audited_hours": total_values[2],
                "total_lectures": total_values[3],
                "total_practices": total_values[4],
                "total_labs": total_values[5],
                "total_self_study": total_values[6],
            }
            base = {
                "program_code": direction_code or context.get("direction_code"),
                "direction_code": direction_code or context.get("direction_code"),
                "program_profile_code": profile_code or context.get("profile_code"),
                "program_profile": profile_name,
                "direction_name": plan_header.get("direction_name"),
                "faculty": faculty,
                "department": department,
                "chair": chair,
                "qualification": plan_header.get("qualification"),
                "education_year": plan_header.get("education_year") or context.get("year"),
                "form": form,
                "duration": plan_header.get("duration") or context.get("duration"),
                "discipline": name,
                "row_no": row_no,
                "study_plan_url": context.get("study_plan_url") or context.get("document_url"),
                "download_url": context.get("download_url") or resource.final_url,
                "source_document_url": context.get("document_url") or resource.requested_url,
                **total,
                "is_data_row": True,
            }
            emitted = 0
            for semester, start in enumerate(aligned_starts, start=1):
                end = aligned_starts[semester] if semester < len(aligned_starts) else min(len(line), start + 55)
                chunk = line[max(0, start) : max(start, end)]
                tokens = chunk.split()
                semester_numbers = [parse_number(value) for value in tokens if number_re.fullmatch(value)]
                if len(semester_numbers) < 4:
                    continue
                if semester_numbers[0] > 60 or semester_numbers[1] > 2_000:
                    repaired = _repair_semester_cell(line, start, number_re)
                    if repaired is not None:
                        semester_numbers, control = repaired
                    else:
                        control = " ".join(value for value in tokens[4:] if not number_re.fullmatch(value)) or None
                else:
                    control = " ".join(value for value in tokens[4:] if not number_re.fullmatch(value)) or None
                records.append(_record(source, captured_at, "StudyPlan", {
                    **base,
                    "course": (semester + 1) // 2,
                    "semester": semester,
                    "credits": semester_numbers[0],
                    "hours": semester_numbers[1],
                    "audited_hours_semester": semester_numbers[2],
                    "self_study": semester_numbers[3],
                    "lectures": None,
                    "practices": None,
                    "labs": None,
                    "total_lectures": total_values[3],
                    "total_practices": total_values[4],
                    "total_labs": total_values[5],
                    "assessment_type": control,
                    "semester_weeks": section_weeks[semester - 1] if semester - 1 < len(section_weeks) else None,
                }))
                emitted += 1
            if not emitted:
                records.append(_record(source, captured_at, "StudyPlan", {
                    **base,
                    "course": None,
                    "semester": None,
                    "credits": total_values[0],
                    "hours": total_values[1],
                    "self_study": total_values[6],
                    "lectures": total_values[3],
                    "practices": total_values[4],
                    "labs": total_values[5],
                    "total_lectures": total_values[3],
                    "total_practices": total_values[4],
                    "total_labs": total_values[5],
                    "assessment_type": None,
                }))
    return _dedupe_records(records)


def _repair_semester_cell(
    line: str,
    expected_start: int,
    number_re: re.Pattern[str],
) -> tuple[list[int | float], str | None] | None:
    """Recover a valid semester cell when a PDF row is horizontally shifted.

    The study-plan PDFs occasionally render elective rows up to one cell left
    of their header. Candidate values are accepted only when the complete
    four-number workload tuple satisfies the domain-level numeric shape.
    """
    matches = list(number_re.finditer(line))
    for candidate_index, candidate in enumerate(matches):
        if not expected_start - 24 <= candidate.start() <= expected_start + 16:
            continue
        following = matches[candidate_index : candidate_index + 4]
        if len(following) < 4 or following[-1].start() - candidate.start() > 55:
            continue
        values = [parse_number(match.group(0)) for match in following]
        if not (0 <= float(values[0]) <= 60 and 0 <= float(values[1]) <= 2_000):
            continue
        if float(values[2]) > float(values[1]) or float(values[3]) > float(values[1]):
            continue
        next_number = next((match for match in matches[candidate_index + 4 :] if match.start() > following[-1].end()), None)
        control_text = line[following[-1].end() : next_number.start() if next_number else len(line)]
        control = " ".join(token for token in control_text.split() if not number_re.fullmatch(token)) or None
        return values, control
    return None


def _walk_json(value: Any) -> Iterable[Any]:
    if isinstance(value, list):
        for item in value:
            yield item
            yield from _walk_json(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield item
            yield from _walk_json(item)


def parse_source(
    source: SourceDefinition,
    resource: FetchedResource,
    context: dict[str, Any] | None = None,
) -> ExtractionResult:
    captured_at = resource.fetched_at
    warnings: list[str] = []
    if resource.error:
        warnings.append(resource.error)
    if not resource.body:
        return ExtractionResult(
            source_id=source.id,
            source_url=resource.final_url or source.url,
            parser="bmstu.empty",
            captured_at=captured_at,
            warnings=warnings or ["source returned empty body"],
        )

    if is_pdf(resource.body, resource.content_type, resource.final_url):
        text = extract_pdf_text(resource.body)
        metadata = pdf_metadata(resource.body)
        record = _record(
            source,
            captured_at,
            "Document",
            {
                "title": metadata.get("title")
                or (resource.final_url or resource.requested_url).split("?", 1)[0].rsplit("/", 1)[-1]
                or source.url.rsplit("/", 1)[-1],
                "url": resource.final_url,
                "document_type": "pdf",
                "admission_year": extract_admission_year(text),
                "content_hash": resource.content_hash,
                "pages": metadata.get("pages"),
                "text_length": len(text),
            },
        )
        records = [record]
        records.extend(_pdf_admission_records(source, resource, text, captured_at))
        if source.id == "S06":
            records.extend(_study_plan_records(source, resource, captured_at, context))
        return ExtractionResult(
            source_id=source.id,
            source_url=resource.final_url,
            parser="bmstu.pdf",
            captured_at=captured_at,
            records=records,
            text=text,
            network_payloads=resource.network_payloads,
            warnings=warnings if text else warnings + ["PDF text extraction returned empty text"],
        )

    if source.id == "S06" and "json" in (resource.content_type or "").casefold():
        records = _program_api_records(source, resource, captured_at)
        return ExtractionResult(
            source_id=source.id,
            source_url=resource.final_url,
            parser="bmstu.majors.api",
            captured_at=captured_at,
            records=records,
            text=resource.body.decode(resource.encoding or "utf-8", errors="replace"),
            warnings=warnings,
        )

    page = parse_page(resource.body, resource.final_url)
    source_id = source.id.upper()
    records: list[dict[str, Any]] = []
    parser_name = "bmstu.generic"

    if source_id in {"S01", "S19"}:
        parser_name = "bmstu.university"
        records.extend(_university_records(source, page, captured_at))
        records.extend(_document_records(source, page, captured_at))
    elif source_id == "S02":
        parser_name = "bmstu.faculties"
        if "/faculty/" in resource.final_url.casefold():
            records.extend(_faculty_detail_records(source, page, captured_at))
        else:
            records.extend(_faculty_index_records(source, page, captured_at))
    elif source_id == "S03":
        parser_name = "bmstu.education"
        records.extend(_education_records(source, page, captured_at))
        records.extend(_document_records(source, page, captured_at))
    elif source_id == "S04":
        parser_name = "bmstu.standards"
        records.extend(_standard_records(source, page, captured_at))
        records.extend(_document_records(source, page, captured_at))
    elif source_id == "S05":
        parser_name = "bmstu.admission_documents"
        records.extend(_document_records(source, page, captured_at))
        records.extend(_generic_row_records(source, page, captured_at, "AdmissionRule"))
    elif source_id == "S06":
        parser_name = "bmstu.majors"
        if "/bachelor/majors/" in resource.final_url.casefold():
            records.extend(_program_detail_records(source, page, captured_at))
        else:
            cards = _program_card_records(source, page, captured_at)
            next_data = _next_state(_next_data(page), "bachelorMajors")
            items = next_data.get("data") if isinstance(next_data, dict) else None
            if isinstance(items, dict):
                items = items.get("data")
            if isinstance(items, list):
                cards.extend(
                    card for item in items if isinstance(item, dict)
                    for card in [_program_card_from_api(source, item, captured_at)] if card
                )
            records.extend(cards)
    elif source_id == "S07":
        parser_name = "bmstu.admissions"
        records.extend(_generic_row_records(source, page, captured_at, "AdmissionRow"))
        records.extend(_network_records(source, resource.network_payloads, captured_at))
    elif source_id == "S08":
        parser_name = "bmstu.enrollment"
        records.extend(_generic_row_records(source, page, captured_at, "EnrollmentRow"))
        records.extend(_network_records(source, resource.network_payloads, captured_at))
    elif source_id == "S10":
        parser_name = "bmstu.tuition"
        records.extend(_cost_records(source, page, captured_at))
    elif source_id == "S09":
        parser_name = "bmstu.paid_education"
        records.extend(_cost_records(source, page, captured_at, "PaidEducation"))
    elif source_id == "S13":
        parser_name = "bmstu.partners"
        records.extend(_international_records(source, page, captured_at))
    elif source_id == "S14":
        parser_name = "bmstu.olympiads"
        records.extend(_link_records(source, page, captured_at, "OlympiadBenefit", ("олимпиад", "победител", "призёр", "призер", "профил", "итог")))
    elif source_id == "S15":
        parser_name = "bmstu.open_courses"
        records.extend(_course_records(source, page, captured_at))
    elif source_id == "S16":
        parser_name = "bmstu.enrichment"
        records.extend(_generic_row_records(source, page, captured_at, "Enrichment"))
    elif source_id in {"S11", "S12"}:
        parser_name = "bmstu.auxiliary"
        records.extend(_generic_row_records(source, page, captured_at, "Auxiliary"))
        records.extend(_document_records(source, page, captured_at))
        if source_id == "S12":
            records.extend(_feature_records(source, page, captured_at))
    else:
        records.extend(_generic_row_records(source, page, captured_at, "SourceRow"))
    if not page.text and not page.tables and not page.links:
        warnings.append("HTML body contains no extractable text, tables or links")
    return ExtractionResult(
        source_id=source.id,
        source_url=resource.final_url,
        parser=parser_name,
        captured_at=captured_at,
        records=_dedupe_records(records),
        tables=page.tables,
        labels=page.labels,
        links=page.links,
        text=page.text,
        network_payloads=resource.network_payloads,
        warnings=warnings,
    )
