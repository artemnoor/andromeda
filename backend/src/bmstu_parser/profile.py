from __future__ import annotations

"""Build the deliberately small BMSTU profile used by the public dashboard.

The complete parser keeps many source records for auditability.  The profile
is a separate projection: it contains only the eight user-facing data blocks
and only the fields agreed for those blocks.  Missing values stay ``None`` or
an empty list; this module never fills them with guesses.
"""

import html
import re
from collections import Counter, defaultdict
from typing import Any, Iterable


_EDUCATION_CODE_RE = re.compile(r"(?<!\d)\d{1,2}\.\d{2}\.\d{2}(?:[-/]\d+)?(?!\d)")
_UNIT_CODE_RE = re.compile(r"(?<![А-ЯЁA-Z])([А-ЯЁA-Z]{1,6})(?:\s*-?\s*(\d{1,2}))?(?![А-ЯЁA-Z])", re.IGNORECASE)
_HEADER_NAMES = {
    "факультеты",
    "кафедры",
    "органы управления университета",
    "научно-исследовательские институты",
}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _norm(value: Any) -> str:
    return " ".join(_text(value).casefold().replace("ё", "е").split())


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _pick(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if _present(value):
            return value
    values = record.get("values")
    if isinstance(values, dict):
        lowered = {_norm(key): value for key, value in values.items()}
        for wanted in keys:
            wanted_norm = _norm(wanted)
            for key, value in lowered.items():
                if wanted_norm == key or wanted_norm in key or key in wanted_norm:
                    if _present(value):
                        return value
    return None


def _code(value: Any) -> str | None:
    match = _EDUCATION_CODE_RE.search(_text(value))
    return match.group(0) if match else None


def _canonical_program_code(value: Any) -> str:
    """Keep program identity stable across hyphen/en-dash PDF variants."""
    text = re.sub(r"\s+", "", _text(value)).replace("–", "-").replace("—", "-").replace("�", "-")
    match = _EDUCATION_CODE_RE.search(text)
    return match.group(0) if match else text


def _direction_base_code(value: Any) -> str:
    """Return the six-digit direction code without a profile suffix."""
    match = re.search(r"\d{2}\.\d{2}\.\d{2}", _text(value))
    return match.group(0) if match else _canonical_program_code(value)


def _unit_code(value: Any) -> str | None:
    match = _UNIT_CODE_RE.search(_text(value).upper().replace("Ё", "Е"))
    if not match:
        return None
    prefix, number = match.groups()
    return f"{prefix.upper()}-{number}" if number else prefix.upper()


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    cleaned = _text(value).replace(" ", "").replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    parsed = float(match.group(0))
    return int(parsed) if parsed.is_integer() else parsed


def _unique(items: Iterable[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        marker = _text(item.get(key))
        if not marker or marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def _node_indexes(hierarchy: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, str]]]:
    nodes = {str(node.get("id")): node for node in hierarchy.get("nodes", []) if node.get("id")}
    by_record: dict[str, dict[str, str]] = {}
    for node in nodes.values():
        for record_id in node.get("record_ids", []):
            by_record[str(record_id)] = {"id": str(node["id"]), "type": str(node.get("type") or "")}
    return nodes, by_record


def _node_id(record: dict[str, Any], by_record: dict[str, dict[str, str]], fallback: str) -> str:
    return by_record.get(str(record.get("record_id")), {}).get("id") or fallback


def _short_name(name: Any) -> str:
    return _text(name).strip(" \t\r\n-—")


def _abbreviation(record: dict[str, Any], name: str) -> str | None:
    value = _pick(record, "code", "Код")
    if _present(value):
        return _unit_code(value) or _text(value)
    match = re.search(r"\(([^()]{1,12})\)", name)
    if match:
        return match.group(1).strip()
    return _unit_code(name)


def _faculty_department_links(hierarchy: dict[str, Any]) -> dict[str, str]:
    links: dict[str, str] = {}
    nodes = {str(node.get("id")): node for node in hierarchy.get("nodes", []) if node.get("id")}
    for edge in hierarchy.get("edges", []):
        if edge.get("relation") != "contains":
            continue
        source = nodes.get(str(edge.get("from")))
        target = nodes.get(str(edge.get("to")))
        if source and target and source.get("type") == "Faculty" and target.get("type") == "Department":
            links[str(target["id"])] = str(source["id"])
    return links


def _table_rows(tables: Iterable[dict[str, Any]], source_id: str, index: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for table in tables:
        if str(table.get("source_id")) == source_id and int(table.get("index", -1)) == index:
            rows.extend(row for row in table.get("rows", []) if isinstance(row, dict))
    return rows


def _field_by_fragment(row: dict[str, Any], *fragments: str) -> Any:
    for key, value in row.items():
        if any(fragment in _norm(key) for fragment in fragments) and _present(value):
            return value
    return None


def _study_plan_program(
    record: dict[str, Any],
    program_by_code: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Resolve a plan by profile code before falling back to direction code."""
    profile_code = _canonical_program_code(_pick(record, "program_profile_code", "profile_code"))
    if profile_code:
        return program_by_code.get(profile_code) or {}
    direction_code = _canonical_program_code(_pick(record, "direction_code"))
    program_code = _canonical_program_code(_pick(record, "program_code", "code"))
    return (
        program_by_code.get(profile_code)
        or program_by_code.get(program_code)
        or program_by_code.get(direction_code)
        or {}
    )


def _study_plan_item(record: dict[str, Any], program_by_code: dict[str, dict[str, Any]]) -> dict[str, Any]:
    program = _study_plan_program(record, program_by_code)
    return {
        "program_id": program.get("id"),
        "program_code": program.get("code") or _canonical_program_code(_pick(record, "program_profile_code", "program_code", "direction_code", "code")),
        "program_profile_code": _pick(record, "program_profile_code", "profile_code") or program.get("code"),
        "direction_code": _pick(record, "direction_code") or program.get("direction_code"),
        "direction_name": _pick(record, "direction_name") or program.get("direction_name"),
        "faculty": _pick(record, "faculty") or program.get("faculty_name"),
        "department": _pick(record, "department") or program.get("department_name"),
        "chair": _pick(record, "chair"),
        "qualification": _pick(record, "qualification") or program.get("qualification"),
        "education_year": _pick(record, "education_year") or program.get("education_year"),
        "form": _pick(record, "form") or program.get("form"),
        "duration": _pick(record, "duration") or program.get("duration"),
        "discipline": _pick(record, "discipline", "subject", "name"),
        "course": _pick(record, "course"),
        "semester": _pick(record, "semester"),
        "semester_weeks": _pick(record, "semester_weeks"),
        "hours": _pick(record, "hours", "total_hours"),
        "credits": _pick(record, "credits", "zet", "ЗЕТ"),
        "audited_hours": _pick(record, "audited_hours"),
        "audited_hours_semester": _pick(record, "audited_hours_semester"),
        "lectures": _pick(record, "lectures", "lecture_hours"),
        "practices": _pick(record, "practices", "practice_hours"),
        "labs": _pick(record, "labs", "laboratory_hours"),
        "self_study": _pick(record, "self_study", "independent_hours"),
        "total_credits": _pick(record, "total_credits"),
        "total_hours": _pick(record, "total_hours"),
        "total_lectures": _pick(record, "total_lectures", "lectures", "lecture_hours"),
        "total_practices": _pick(record, "total_practices", "practices", "practice_hours"),
        "total_labs": _pick(record, "total_labs", "labs", "laboratory_hours"),
        "total_self_study": _pick(record, "total_self_study", "self_study", "independent_hours"),
        "assessment_type": _pick(record, "assessment_type", "control", "attestation"),
        "study_plan_url": _pick(record, "study_plan_url", "source_document_url") or program.get("study_plan_url"),
        "download_url": _pick(record, "download_url"),
    }


def _study_plans(records: list[dict[str, Any]], tables: list[dict[str, Any]], program_by_code: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    accepted_types = {"StudyPlan", "Curriculum", "AcademicPlan", "Discipline", "CourseUnit"}
    for record in records:
        if record.get("record_type") not in accepted_types:
            continue
        item = _study_plan_item(record, program_by_code)
        if _present(item.get("discipline")):
            result.append(item)
    for table in tables:
        headers = " ".join(_norm(header) for header in table.get("headers", []))
        if "семестр" not in headers or ("зет" not in headers and "кредит" not in headers):
            continue
        if "дисциплин" not in headers and "предмет" not in headers:
            continue
        for row in table.get("rows", []):
            if not isinstance(row, dict):
                continue
            values = {
                "program_code": _field_by_fragment(row, "код программы", "код направления"),
                "discipline": _field_by_fragment(row, "дисциплин", "предмет"),
                "course": _field_by_fragment(row, "курс"),
                "semester": _field_by_fragment(row, "семестр"),
                "hours": _field_by_fragment(row, "час"),
                "credits": _field_by_fragment(row, "зет", "кредит"),
                "lectures": _field_by_fragment(row, "лекц"),
                "practices": _field_by_fragment(row, "практи"),
                "labs": _field_by_fragment(row, "лаборатор"),
                "self_study": _field_by_fragment(row, "самостоятель"),
                "assessment_type": _field_by_fragment(row, "контрол", "аттеста"),
                "study_plan_url": _field_by_fragment(row, "ссылк", "документ"),
            }
            item = _study_plan_item(values, program_by_code)
            if _present(item.get("discipline")):
                result.append(item)
    return result


def _study_plan_summaries(records: list[dict[str, Any]], program_by_code: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for record in records:
        if record.get("record_type") != "StudyPlanSummary":
            continue
        program = _study_plan_program(record, program_by_code)
        plan_url = _pick(record, "study_plan_url", "source_document_url")
        marker = (program.get("id"), _text(plan_url) or None)
        if marker in seen:
            continue
        seen.add(marker)
        result.append({
            "id": f"study-plan-summary:{program.get('code') or _canonical_program_code(_pick(record, 'program_profile_code', 'direction_code'))}",
            "program_id": program.get("id"),
            "program_code": program.get("code") or _canonical_program_code(_pick(record, "program_profile_code", "program_code", "direction_code")),
            "program_profile_code": _pick(record, "program_profile_code", "profile_code") or program.get("code"),
            "direction_code": _pick(record, "direction_code") or program.get("direction_code"),
            "direction_name": _pick(record, "direction_name") or program.get("direction_name"),
            "faculty": _pick(record, "faculty") or program.get("faculty_name"),
            "department": _pick(record, "department") or program.get("department_name"),
            "qualification": _pick(record, "qualification") or program.get("qualification"),
            "education_year": _pick(record, "education_year") or program.get("education_year"),
            "form": _pick(record, "form") or program.get("form"),
            "duration": _pick(record, "duration") or program.get("duration"),
            "study_plan_url": plan_url or program.get("study_plan_url"),
            "download_url": _pick(record, "download_url"),
            "semester_count": _pick(record, "semester_count"),
            "semester_weeks": _pick(record, "semester_weeks") or [],
            "semesters": _pick(record, "semesters") or [],
            "overall_academic": _pick(record, "overall_academic"),
            "overall_astronomical": _pick(record, "overall_astronomical"),
        })
    return result


def _unit_key(value: Any) -> str:
    return re.sub(r"[^a-zа-я0-9]", "", _norm(value))


def _priority_program_match(record: dict[str, Any], programs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Attach a PDF admission row only when the program identity is provable.

    The admission-plan PDF contains several profiles under one direction and
    also contains branch/second-higher-education rows.  Matching by direction
    plus a few shared words is unsafe: it attaches a valid number of places
    to a different program.  Prefer exact text identity, then allow only a
    high-confidence unique containment/overlap with the same department.
    """
    direction_code = _direction_base_code(record.get("direction_code"))
    candidates = [item for item in programs if _direction_base_code(item.get("direction_code")) == direction_code]
    if not candidates:
        return None

    def normalize(value: Any) -> str:
        value = html.unescape(_text(value)).casefold().replace("ё", "е")
        return " ".join(re.findall(r"[a-zа-я0-9]+", value))

    def special_kind(value: Any) -> str:
        text = normalize(value)
        if "второе во" in text or "второе высшее" in text:
            return "second_higher"
        if "адаптационн" in text:
            return "adapted"
        return "standard"

    department_code = _unit_key(record.get("department_code"))
    program_name = normalize(record.get("program_name") or record.get("program_profile"))
    if not program_name:
        return None
    row_kind = special_kind(record.get("program_name") or record.get("program_profile"))
    scored: list[tuple[tuple[int, float, int], dict[str, Any]]] = []
    for candidate in candidates:
        candidate_name = normalize(candidate.get("profile") or candidate.get("name"))
        if not candidate_name:
            continue
        candidate_kind = special_kind(candidate.get("profile") or candidate.get("name"))
        if row_kind != candidate_kind:
            continue
        same_department = bool(department_code and _unit_key(candidate.get("department_code")) == department_code)
        exact = candidate_name == program_name
        contained = candidate_name in program_name or program_name in candidate_name
        left = set(program_name.split())
        right = set(candidate_name.split())
        overlap = len(left & right) / max(1, min(len(left), len(right)))
        if exact:
            scored.append(((3, 1.0, int(same_department)), candidate))
        elif contained:
            scored.append(((2, overlap, int(same_department)), candidate))
        elif same_department and len(left & right) >= 4 and overlap >= 0.78:
            scored.append(((1, overlap, 1), candidate))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_candidate = scored[0]
    equally_good = [candidate for score, candidate in scored if score == best_score]
    if len(equally_good) > 1 and not department_code:
        return None
    return best_candidate


def _new_admission(code: str, year: Any) -> dict[str, Any]:
    return {
        "id": f"admission:{code}:{year or 'unknown'}",
        "year": year,
        "direction_code": code,
        "program_code": None,
        "program_profile_code": None,
        "program_id": None,
        "program_name": None,
        "department_code": None,
        "department_name": None,
        "campus": None,
        "budget_places": None,
        "paid_places": None,
        "budget_special_quota_places": None,
        "paid_special_quota_places": None,
        "passing_score": None,
        "exams": [],
        "allowed_combinations": [],
        "minimum_scores": [],
        "source_id": None,
        "source_priority": None,
    }


def _admission(
    records: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    programs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    programs = programs or []
    detail_rows = [record for record in records if record.get("record_type") == "Admission" and record.get("source_id") == "S06"]
    site_grouped: dict[tuple[str, Any], dict[str, Any]] = {}
    for record in detail_rows:
        code = _canonical_program_code(record.get("direction_code") or record.get("program_code"))
        if not code:
            continue
        year = record.get("year")
        item = site_grouped.setdefault((code, year), _new_admission(code, year))
        if record.get("place_type") == "budget":
            item["budget_places"] = record.get("count")
        elif record.get("place_type") == "paid":
            item["paid_places"] = record.get("count")
        if record.get("score_type") == "budget":
            item["passing_score"] = record.get("score")
        if _present(record.get("exam")):
            exam = {
                "subject": record.get("exam"),
                "minimum_score": record.get("minimum_score"),
                "is_choice": bool(record.get("is_choice")),
            }
            if exam not in item["exams"]:
                item["exams"].append(exam)
            minimum = {"subject": record.get("exam"), "score": record.get("minimum_score")}
            if minimum not in item["minimum_scores"]:
                item["minimum_scores"].append(minimum)
    for item in site_grouped.values():
        choices = [exam["subject"] for exam in item["exams"] if exam.get("is_choice")]
        if choices:
            item["allowed_combinations"] = [{"type": "choice", "subjects": choices}]

    priority_rows = [record for record in records if record.get("record_type") == "Admission" and record.get("source_id") == "P01_BS_PDF"]
    if site_grouped or priority_rows:
        result: list[dict[str, Any]] = []
        priority_directions: set[tuple[str, Any]] = set()
        for record in priority_rows:
            direction_code = _canonical_program_code(record.get("direction_code") or record.get("program_code"))
            if not direction_code:
                continue
            year = record.get("year")
            priority_directions.add((direction_code, year))
            program = _priority_program_match(record, programs)
            program_code = program.get("code") if program else None
            identity = program_code or ":".join(filter(None, [direction_code, _unit_key(record.get("department_code")), _norm(record.get("program_name"))]))
            item = _new_admission(identity, year)
            site = site_grouped.get((direction_code, year)) or site_grouped.get((direction_code, None))
            if site:
                for key in ("passing_score", "exams", "allowed_combinations", "minimum_scores"):
                    item[key] = site.get(key)
            item.update({
                "id": f"admission:{identity}:{year or 'unknown'}:{record.get('pdf_page')}:{record.get('pdf_row')}",
                "direction_code": direction_code,
                "program_code": program_code,
                "program_profile_code": program_code,
                "program_id": program.get("id") if program else None,
                "program_name": record.get("program_name"),
                "department_name": record.get("department_name") or (program or {}).get("department_name"),
                "department_code": record.get("department_code") or (program or {}).get("department_code"),
                "campus": record.get("campus"),
                "budget_places": record.get("budget_places"),
                "paid_places": record.get("paid_places"),
                "budget_special_quota_places": record.get("budget_special_quota_places"),
                "paid_special_quota_places": record.get("paid_special_quota_places"),
                "source_id": record.get("source_id"),
                "source_priority": "primary",
                "source_url": record.get("source_url"),
                "pdf_page": record.get("pdf_page"),
                "pdf_row": record.get("pdf_row"),
            })
            result.append(item)
        for key, item in site_grouped.items():
            if key not in priority_directions:
                result.append(item)
        if result:
            return result

    minimum_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    # S09 is the current source family. Keep S10 as a compatibility fallback
    # for older snapshots and fixture tables with the same column layout.
    minimum_rows = _table_rows(tables, "S09", 3) or _table_rows(tables, "S10", 3)
    historical_rows = _table_rows(tables, "S09", 4) or _table_rows(tables, "S10", 4)
    for row in minimum_rows:
        code = _code(row.get("НП(С)"))
        score = _number(row.get("Пороговый балл по каждому предмету ЕГЭ"))
        if code and score is not None:
            minimum_by_code[code].append({"subject": "каждый предмет ЕГЭ", "score": score})

    result: list[dict[str, Any]] = []
    for row in historical_rows:
        code = _code(row.get("НАПРАВЛЕНИЕ ПОДГОТОВКИ / СПЕЦИАЛЬНОСТЬ"))
        if not code:
            continue
        for key, value in row.items():
            if not re.fullmatch(r"20\d{2}", str(key)):
                continue
            year = int(key)
            min_score = _number(row.get(f"{key}_2"))
            if min_score is None:
                continue
            result.append({
                "id": f"admission:{code}:{year}",
                "year": year,
                "direction_code": code,
                "budget_places": None,
                "paid_places": None,
                "passing_score": min_score,
                "exams": [],
                "allowed_combinations": [],
                "minimum_scores": minimum_by_code.get(code, []),
                "program_code": None,
                "program_profile_code": None,
                "program_id": None,
                "budget_special_quota_places": None,
                "paid_special_quota_places": None,
                "source_priority": None,
            })

    for code, minimum_scores in minimum_by_code.items():
        if not any(item["direction_code"] == code for item in result):
            result.append({
                "id": f"admission:{code}:current",
                "year": None,
                "direction_code": code,
                "budget_places": None,
                "paid_places": None,
                "passing_score": None,
                "exams": [],
                "allowed_combinations": [],
                "minimum_scores": minimum_scores,
                "program_code": None,
                "program_profile_code": None,
                "program_id": None,
                "budget_special_quota_places": None,
                "paid_special_quota_places": None,
                "source_priority": None,
            })
    return result


def build_profile(
    records: Iterable[dict[str, Any]],
    tables: Iterable[dict[str, Any]] | None = None,
    hierarchy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = [dict(record) for record in records if isinstance(record, dict)]
    tables = [dict(table) for table in (tables or []) if isinstance(table, dict)]
    hierarchy = hierarchy or {"nodes": [], "edges": []}
    nodes, by_record = _node_indexes(hierarchy)
    faculty_department = _faculty_department_links(hierarchy)
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_type[str(record.get("record_type") or "")].append(record)

    university_record = next(
        (record for record in by_type.get("University", []) if _present(record.get("city")) and _present(record.get("address"))),
        next(iter(by_type.get("University", [])), {}),
    )
    vuc = any(
        bool(record.get("vuc") or record.get("available"))
        for record in records
        if record.get("record_type") in {"Program", "Admission", "UniversityFeature"}
    ) or any("военный учебный центр" in _norm(record.get("name")) for record in by_type.get("OrganizationUnit", []))
    university = {
        "id": "university:bmstu",
        "name": university_record.get("name_short") or university_record.get("name_full") or "МГТУ им. Н.Э. Баумана",
        "city": university_record.get("city"),
        "site": university_record.get("official_site"),
        "address": university_record.get("address"),
        "vuc": vuc,
    }

    faculties: list[dict[str, Any]] = []
    faculty_by_name: dict[str, dict[str, Any]] = {}
    for record in by_type.get("Faculty", []):
        name = _short_name(record.get("name"))
        if not name or _norm(name) in _HEADER_NAMES:
            continue
        existing = faculty_by_name.get(_norm(name))
        abbreviation = _abbreviation(record, name)
        if existing:
            if not existing.get("abbreviation") and abbreviation:
                existing["abbreviation"] = abbreviation
            continue
        item = {
            "id": _node_id(record, by_record, f"faculty:{len(faculties) + 1}"),
            "name": name,
            "abbreviation": abbreviation,
            "university_id": university["id"],
        }
        faculties.append(item)
        faculty_by_name[_norm(name)] = item

    departments: list[dict[str, Any]] = []
    department_by_code: dict[str, dict[str, Any]] = {}
    department_by_name: dict[str, dict[str, Any]] = {}
    for record in by_type.get("Department", []):
        name = _short_name(record.get("name"))
        if not name or _norm(name) in _HEADER_NAMES:
            continue
        item_id = _node_id(record, by_record, f"department:{len(departments) + 1}")
        node = nodes.get(item_id, {})
        code = _unit_code(_pick(record, "code", "Код")) or _unit_code(name)
        faculty_id = faculty_department.get(item_id)
        parent_name = _pick(record, "parent_name")
        if not faculty_id and parent_name:
            faculty_id = faculty_by_name.get(_norm(parent_name), {}).get("id")
        item = {"id": item_id, "name": name, "code": code, "abbreviation": code, "faculty_id": faculty_id}
        departments.append(item)
        department_by_name.setdefault(_norm(name), item)
        if code:
            department_by_code[_norm(code.replace("-", ""))] = item
        for candidate in (code, _unit_code(name)):
            if candidate:
                department_by_code[_norm(candidate.replace("-", ""))] = item

    faculty_ids = {item["id"] for item in faculties}
    for item in departments:
        if item.get("faculty_id") in faculty_ids:
            continue
        code = _norm((item.get("code") or "").replace("-", ""))
        prefix = re.match(r"[а-яa-z]+", code).group(0) if re.match(r"[а-яa-z]+", code) else ""
        hint = {
            "фн": "фундаментальн",
            "ибм": "инженерный бизнес",
            "иу": "информатик",
            "см": "специальн",
            "мт": "машиностроительн",
            "э": "энергомашиностроен",
            "рл": "радиоэлектрон",
            "бмт": "биомедицинск",
            "л": "лингвист",
            "сгн": "социальн",
            "рк": "робототехник",
            "лт": "лесного хозяйства",
        }.get(prefix)
        if hint:
            item["faculty_id"] = next((faculty["id"] for faculty in faculties if hint in _norm(faculty["name"])), None)

    directions: list[dict[str, Any]] = []
    direction_by_code: dict[str, dict[str, Any]] = {}
    levels_by_code: dict[str, Counter[str]] = defaultdict(Counter)
    for record in by_type.get("Program", []):
        code = _text(record.get("direction_code")) or _code(record.get("code"))
        if code and _present(record.get("level")):
            levels_by_code[code][_text(record.get("level"))] += 1
    for record in by_type.get("Direction", []):
        code = _text(record.get("code")) or _code(record.get("name"))
        name = _short_name(record.get("name"))
        if not code or not name or code in direction_by_code:
            continue
        item = {
            "id": _node_id(record, by_record, f"direction:{code}"),
            "code": code,
            "name": name,
            "education_level": _text(record.get("level")) or (levels_by_code[code].most_common(1)[0][0] if levels_by_code[code] else None),
        }
        directions.append(item)
        direction_by_code[code] = item

    programs: list[dict[str, Any]] = []
    program_by_code: dict[str, dict[str, Any]] = {}
    detail_programs = [record for record in by_type.get("Program", []) if record.get("source_id") == "S06"]
    if not detail_programs:
        detail_programs = [record for record in by_type.get("Program", []) if record.get("source_id") == "S03"]
    profile_by_direction: dict[str, list[dict[str, Any]]] = defaultdict(list)
    profile_by_code: dict[str, dict[str, Any]] = {}
    for record in by_type.get("ProgramProfile", []):
        direction_code = _canonical_program_code(record.get("direction_code"))
        if direction_code:
            profile_by_direction[direction_code].append(record)
        profile_code = _canonical_program_code(record.get("profile_code") or record.get("program_code"))
        if profile_code:
            profile_by_code[profile_code] = record
    study_plan_urls_by_code: dict[str, str] = {}
    for record in by_type.get("ProgramProfile", []):
        profile_code = _canonical_program_code(record.get("profile_code") or record.get("program_code"))
        plan_url = _text(record.get("study_plan_url") or record.get("url"))
        if profile_code and plan_url:
            study_plan_urls_by_code.setdefault(profile_code, plan_url)
    summary_by_code: dict[str, dict[str, Any]] = {}
    for record in by_type.get("StudyPlanSummary", []):
        for candidate in (
            record.get("program_profile_code"),
            record.get("program_code"),
            record.get("direction_code"),
        ):
            candidate_code = _canonical_program_code(candidate)
            if candidate_code:
                summary_by_code.setdefault(candidate_code, record)
    for record in detail_programs:
        code = _canonical_program_code(record.get("code"))
        direction_code = _canonical_program_code(record.get("direction_code")) or _canonical_program_code(_code(code))
        code = code or direction_code
        if not direction_code or not code:
            continue
        department_code = _unit_code(record.get("department_code")) or _unit_code(record.get("department_code", ""))
        department = department_by_name.get(_norm(record.get("department"))) if record.get("department") else None
        department = department or department_by_code.get(_norm((department_code or "").replace("-", "")))
        faculty = faculty_by_name.get(_norm(record.get("faculty"))) if record.get("faculty") else None
        candidates = profile_by_direction.get(direction_code) or [None]
        for profile_record in candidates:
            profile_code = _canonical_program_code(profile_record.get("profile_code") or profile_record.get("program_code")) if profile_record else ""
            program_code = profile_code or code
            if program_code in program_by_code:
                continue
            summary = summary_by_code.get(program_code) or summary_by_code.get(direction_code) or {}
            faculty_name = (profile_record or {}).get("faculty") or record.get("faculty")
            department_name = (profile_record or {}).get("department") or record.get("department")
            profile_name = (profile_record or {}).get("name") or (profile_record or {}).get("title")
            item = {
                "id": f"program:{program_code}",
                "name": _short_name(profile_name or record.get("name")),
                "profile": (profile_record or {}).get("profile") or profile_name or record.get("profile"),
                "code": program_code,
                "direction_id": direction_by_code.get(direction_code, {}).get("id"),
                "direction_code": direction_code,
                "department_id": department.get("id") if department else None,
                "faculty_id": department.get("faculty_id") if department else faculty.get("id") if faculty else None,
                "direction_name": record.get("direction_name") or record.get("name"),
                "description": (profile_record or {}).get("description") or record.get("description"),
                "level": record.get("level"),
                "qualification": record.get("qualification") or summary.get("qualification"),
                "faculty_name": faculty_name or summary.get("faculty"),
                "faculty_code": record.get("faculty_code"),
                "faculty_url": record.get("faculty_url"),
                "department_name": department_name or summary.get("department"),
                "department_code": record.get("department_code"),
                "department_url": record.get("department_url"),
                "place": (profile_record or {}).get("place"),
                "form": record.get("form") or summary.get("form"),
                "duration": record.get("duration") or summary.get("duration"),
                "language": record.get("language"),
                "education_year": summary.get("education_year"),
                "program_url": (profile_record or {}).get("url") or record.get("url"),
                "study_plan_url": study_plan_urls_by_code.get(program_code) or summary.get("study_plan_url"),
            }
            programs.append(item)
            program_by_code[program_code] = item
            program_by_code.setdefault(direction_code, item)

    tuition: list[dict[str, Any]] = []
    seen_tuition: set[tuple[Any, ...]] = set()
    paid_education = [
        record for record in by_type.get("PaidEducation", [])
        if record.get("source_id") != "S09" or record.get("table_index") in {1, 2}
    ]
    tuition_records = [
        record for record in by_type.get("Tuition", [])
        if record.get("source_id") == "S06"
    ]
    tuition_records += paid_education
    if not tuition_records:
        tuition_records = by_type.get("Tuition", [])
    for record in tuition_records:
        code = _text(record.get("code"))
        if not code:
            continue
        key = (code, record.get("year"), record.get("academic_year"), record.get("price"))
        if key in seen_tuition:
            continue
        seen_tuition.add(key)
        tuition.append({
            "id": f"tuition:{code}:{record.get('year') or record.get('academic_year') or 'unknown'}:{record.get('price')}",
            "program_ids": [item["id"] for item in programs if item.get("direction_code") == code or item.get("code") == code],
            "program_code": record.get("program_code"),
            "direction_code": code,
            "year": record.get("year"),
            "academic_year": record.get("academic_year"),
            "amount": record.get("price"),
            "currency": record.get("currency") or "RUB",
        })

    study_plans = _study_plans(records, tables, program_by_code)
    study_plan_summaries = _study_plan_summaries(records, program_by_code)
    admission = _admission(records, tables, programs)
    return {
        "format": "andromeda-bmstu-profile",
        "version": 3,
        "title": "МГТУ им. Н.Э. Баумана — профиль данных",
        "selected_blocks": [
            "university",
            "faculties",
            "departments",
            "directions",
            "programs",
            "admission",
            "tuition",
            "study_plans",
        ],
        "fields": {
            "university": ["name", "city", "site", "address", "vuc"],
            "faculty": ["name", "abbreviation", "university_id"],
            "department": ["name", "code", "abbreviation", "faculty_id"],
            "direction": ["code", "name", "education_level"],
            "program": ["name", "profile", "code", "direction_code", "direction_name", "description", "level", "qualification", "direction_id", "department_id", "department_name", "department_code", "department_url", "faculty_id", "faculty_name", "faculty_code", "faculty_url", "place", "form", "duration", "language", "education_year", "program_url", "study_plan_url"],
            "admission": ["year", "direction_code", "program_code", "program_profile_code", "program_id", "program_name", "department_code", "department_name", "budget_places", "paid_places", "budget_special_quota_places", "paid_special_quota_places", "passing_score", "exams", "allowed_combinations", "minimum_scores", "campus", "source_id", "source_priority", "source_url"],
            "tuition": ["program_code", "direction_code", "year", "academic_year", "amount", "currency"],
            "study_plan": ["program_id", "program_code", "program_profile_code", "direction_code", "direction_name", "faculty", "department", "chair", "qualification", "education_year", "form", "duration", "discipline", "course", "semester", "semester_weeks", "hours", "credits", "audited_hours", "audited_hours_semester", "lectures", "practices", "labs", "self_study", "total_credits", "total_hours", "total_lectures", "total_practices", "total_labs", "total_self_study", "assessment_type", "study_plan_url", "download_url"],
            "study_plan_summary": ["program_id", "program_code", "program_profile_code", "direction_code", "direction_name", "faculty", "department", "qualification", "education_year", "form", "duration", "study_plan_url", "download_url", "semester_count", "semester_weeks", "semesters", "overall_academic", "overall_astronomical"],
        },
        "university": university,
        "faculties": sorted(faculties, key=lambda item: _norm(item["name"])),
        "departments": sorted(departments, key=lambda item: _norm(item["name"])),
        "directions": sorted(directions, key=lambda item: (item.get("code") or "", _norm(item["name"]))),
        "programs": sorted(programs, key=lambda item: (item.get("direction_code") or "", item.get("code") or "")),
        "admission": sorted(admission, key=lambda item: (item.get("direction_code") or "", item.get("year") or 0)),
        "tuition": sorted(tuition, key=lambda item: (item.get("direction_code") or "", item.get("year") or 0, item.get("amount") or 0)),
        "study_plans": study_plans,
        "study_plan_summaries": study_plan_summaries,
        "stats": {
            "faculties": len(faculties),
            "departments": len(departments),
            "directions": len(directions),
            "programs": len(programs),
            "admission": len(admission),
            "tuition": len(tuition),
            "study_plans": len(study_plans),
            "study_plan_summaries": len(study_plan_summaries),
        },
    }
