from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable

from .models import ExtractionResult, FieldDefinition
from .source_map import norm


ENTITY_TYPES: dict[str, set[str]] = {
    "University": {"University"},
    "UniversityLocation": {"University", "UniversityLocation"},
    "UniversityBranch": {"UniversityBranch"},
    "Faculty": {"Faculty"},
    "Department": {"Department"},
    "FacultyDirection": {"ProgramOffering"},
    "FacultyProgram": {"Program"},
    "DepartmentDirection": {"ProgramOffering"},
    "DepartmentProgram": {"Program"},
    "Direction": {"Direction"},
    "DirectionOffering": {"ProgramOffering"},
    "DirectionRelation": {"ProgramOffering", "Course"},
    "DirectionStandard": {"DirectionStandard"},
    "DirectionAccreditation": {"DirectionStandard"},
    "Program": {"Program", "ProgramCard"},
    "ProgramOffering": {"ProgramOffering"},
    "Curriculum": {"Curriculum", "Document"},
    "CurriculumDiscipline": {"CurriculumDiscipline", "SourceRow"},
    "CurriculumMetric": {"CurriculumMetric", "SourceRow"},
    "Admission": {"AdmissionRow", "AdmissionRule", "EnrollmentRow"},
    "Enrollment": {"EnrollmentRow", "AdmissionRow"},
    "AdmissionStats": {"AdmissionRow", "EnrollmentRow"},
    "AdmissionOutcome": {"EnrollmentRow", "AdmissionRow"},
    "AdmissionDemand": {"AdmissionRow"},
    "AdmissionDemandMetric": {"AdmissionRow"},
    "AdmissionFillRate": {"EnrollmentRow"},
    "AdmissionDemandSeries": {"AdmissionRow"},
    "Tuition": {"Tuition", "PaidEducation"},
    "TuitionSeries": {"Tuition"},
    "TuitionMetric": {"Tuition"},
    "TuitionDiscount": {"PaidEducation", "Tuition"},
    "TuitionAid": {"PaidEducation", "Tuition"},
    "TuitionDiscountRule": {"PaidEducation", "AdmissionRule"},
    "EducationCredit": {"PaidEducation", "Auxiliary"},
    "Installment": {"PaidEducation", "Auxiliary"},
    "UniversityRanking": {"UniversityRanking"},
    "PartnerRelation": {"PartnerRelation"},
    "InternationalPartner": {"InternationalPartner"},
    "InternationalOpportunity": {"PartnerRelation"},
    "InternationalProgram": {"PartnerRelation"},
    "DoubleDegree": {"PartnerRelation"},
    "InternationalRequirement": {"PartnerRelation"},
    "UniversityFeature": {"UniversityFeature"},
    "OlympiadBenefit": {"OlympiadBenefit", "AdmissionRule"},
    "Course": {"Course"},
}


def _flatten_records(extractions: Iterable[ExtractionResult]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for extraction in extractions:
        records.extend(extraction.records)
    return records


def _allowed_types(entity: str) -> set[str]:
    if entity in ENTITY_TYPES:
        return ENTITY_TYPES[entity]
    return {entity}


def _keys_for_field(definition: FieldDefinition) -> list[str]:
    text = norm(definition.name)
    target = norm(definition.extraction_target)
    both = f"{text} {target}"
    if definition.entity in {"AdmissionDemandMetric", "AdmissionFillRate"}:
        return []
    if "истори" in text or definition.entity.endswith("Series"):
        return ["academic_year", "year", "price", "score", "values"]
    if "изменение" in text or definition.entity.endswith("Metric"):
        return ["price", "score", "values", "year"]
    if "полное" in text and "наимен" in text:
        return ["name_full", "name"]
    if "сокращ" in text and "наимен" in text:
        return ["name_short", "short_name"]
    if text in {"название", "наименование", "полное название"} or "официальное название" in both:
        return ["name", "name_full", "title"]
    if "адрес" in text or "адрес" in target:
        return ["address"]
    if "уровен" in text:
        return ["level"]
    if "город" in text:
        return ["city"]
    if "контакт" in text or "e-mail" in both or "телефон" in both:
        return ["contacts", "email", "phone"]
    if "официальн" in both and ("сайт" in both or "страниц" in both or "url" in both):
        return ["official_site", "url", "source_url"]
    if "лиценз" in both:
        return ["license"]
    if "аккредит" in both:
        return ["accreditation"]
    if "форма собственности" in text or ("государствен" in text and "частн" in text):
        return ["ownership", "form"]
    if "учред" in both:
        return ["founder"]
    if "тип" in text:
        return ["type", "unit_type", "level", "program_type"]
    if "форма" in text:
        return ["form"]
    if "срок" in text or "продолж" in both:
        return ["duration"]
    if "язык" in text:
        return ["language"]
    if "профил" in both:
        return ["profile"]
    if definition.entity == "UniversityFeature":
        return ["available", "feature", "name"]
    if definition.entity in {"ProgramOffering", "DirectionOffering"}:
        if "профил" in both:
            return ["profile"]
        if "форма" in both:
            return ["form"]
        if "срок" in both:
            return ["duration"]
        if "код" in both:
            return ["program_code", "direction_code"]
    if definition.entity == "DirectionStandard":
        return ["standard_type", "title", "name"]
    if "факультет" in both or "институт" in both:
        return ["faculty"]
    if "кафедр" in both:
        return ["department"]
    if "стоим" in both or "цен" in both:
        return ["price", "tuition", "cost"]
    if "код" in text or ("код" in target and "цен" not in both and "стоим" not in both):
        return ["code", "id"]
    if "минимальн" in both and "балл" in both:
        return ["min_score", "minimum_score", "score"]
    if "максимальн" in both and "балл" in both:
        return ["max_score", "maximum_score", "score"]
    if "балл" in both:
        return ["score", "min_score", "max_score"]
    if "кцп" in both or "бюджетн" in both and "мест" in both:
        return ["budget_places", "places", "budget_plan"]
    if "платн" in both and "мест" in both:
        return ["paid_places", "paid_plan"]
    if "мест" in both:
        return ["places", "budget_places", "paid_places"]
    if "заяв" in both:
        return ["applications", "application_count"]
    if "участ" in both:
        return ["participants", "participant_count"]
    if "зачисл" in both:
        return ["enrolled", "budget_enrolled", "paid_enrolled"]
    if "рейтинг" in both or "позици" in both:
        return ["rank", "score", "name", "year"]
    if "партнер" in both or "партнер" in text:
        return ["partner_name", "name", "values"]
    if "олимпиад" in both:
        return ["olympiad", "name", "values"]
    if "год" in both or "year" in both:
        return ["academic_year", "admission_year", "year"]
    if "связ" in both:
        return ["relations", "faculty", "department", "program"]
    return ["value", "values", "name", "title"]


def _value(record: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _derived_value(definition: FieldDefinition, record: dict[str, Any]) -> Any:
    """Возвращает вычисляемое значение, сохраняя его привязанным к исходной записи."""
    value = _value(record, _keys_for_field(definition))
    if value in (None, "", [], {}):
        return None
    if "за семестр" in norm(definition.name) and isinstance(value, (int, float)):
        # На странице стоимости годовая цена оплачивается двумя равными платежами.
        return round(value / 2, 2)
    return value


def _derived_series(definition: FieldDefinition, records: list[dict[str, Any]]) -> Any:
    if not records:
        return None
    data_records = [record for record in records if record.get("is_data_row")]
    if definition.entity == "DirectionRelation":
        values = []
        seen: set[str] = set()
        for record in data_records:
            key = str(record.get("program_code") or record.get("direction_code") or record.get("name") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            values.append({
                "code": record.get("program_code") or record.get("direction_code"),
                "name": record.get("profile") or record.get("direction_name") or record.get("name"),
            })
        return values or None
    if definition.entity in {"FacultyDirection", "FacultyProgram", "DepartmentDirection", "DepartmentProgram"}:
        # Связь конкретного подразделения определяется в hierarchy.json по
        # published department_code/derived faculty prefix. Здесь нельзя
        # безопасно подставлять общий список во все факультеты.
        return None
    if definition.entity == "AdmissionStats":
        scores = [
            record.get("score")
            for record in data_records
            if isinstance(record.get("score"), (int, float))
        ]
        if not scores:
            return None
        name = norm(definition.name)
        if "средн" in name:
            return round(sum(scores) / len(scores), 2)
        if "минимальн" in name:
            return min(scores)
        if "максимальн" in name:
            return max(scores)
        if "проходн" in name:
            preferred = [
                record
                for record in data_records
                if _is_main_budget_document(record.get("document_title"))
            ]
            if preferred:
                scores = [
                    record.get("score")
                    for record in preferred
                    if isinstance(record.get("score"), (int, float))
                ]
            year = next(
                (record.get("admission_year") for record in (preferred or data_records) if record.get("admission_year")),
                None,
            )
            return [{"year": year, "score": min(scores)}]
        return None
    if definition.entity == "AdmissionDemand":
        if not data_records:
            return None
        name = norm(definition.name)
        if "заявлен" in name:
            rows = [record for record in data_records if record.get("programs")]
        elif "участ" in name:
            rows = [record for record in data_records if not record.get("programs")]
        else:
            rows = data_records
        if not rows:
            return None
        if "уникальн" in name:
            identifiers = {str(record.get("applicant_id")) for record in rows if record.get("applicant_id")}
            return len(identifiers) if identifiers else None
        return len(rows)
    if definition.entity == "AdmissionOutcome":
        if not data_records:
            return None
        name = norm(definition.name)
        if "дол" in name:
            return None
        channel_tokens = ("бви", "целев", "особ", "отдельн", "общему конкурсу")
        if any(token in name for token in channel_tokens):
            categorized = [record for record in data_records if record.get("admission_channel")]
            if not categorized:
                return None
            rows = [
                record
                for record in categorized
                if any(token in norm(record.get("admission_channel")) for token in channel_tokens if token in name)
            ]
            return len(rows) if rows else None
        return len(data_records)
    if definition.entity == "AdmissionDemandSeries":
        if not data_records:
            return None
        year = next(
            (record.get("admission_year") for record in data_records if record.get("admission_year")),
            None,
        )
        metric = "applications" if any(record.get("programs") for record in data_records) else "participants"
        return [{"year": year, metric: len(data_records)}]
    if definition.entity in {"AdmissionDemandMetric", "AdmissionFillRate"}:
        # Для этих метрик нужны согласованные числитель и знаменатель
        # одного competition_scope. Ссылки на PDF сами по себе метрикой не
        # являются и не должны попадать в facts как будто это число.
        return None
    if definition.entity.endswith("Metric") or "изменение" in norm(definition.name):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            if record.get("price") is None:
                continue
            grouped[str(record.get("code") or record.get("name") or "unknown")].append(record)
        changes: list[dict[str, Any]] = []
        for code, items in grouped.items():
            items.sort(key=lambda item: (item.get("year") or 0, item.get("academic_year") or ""))
            for previous, current in zip(items, items[1:]):
                old_price = previous.get("price")
                new_price = current.get("price")
                if not isinstance(old_price, (int, float)) or not isinstance(new_price, (int, float)):
                    continue
                delta = new_price - old_price
                changes.append(
                    {
                        "code": code,
                        "from_year": previous.get("year"),
                        "to_year": current.get("year"),
                        "from_price": old_price,
                        "to_price": new_price,
                        "delta": delta,
                        "delta_pct": round(delta / old_price * 100, 4) if old_price else None,
                    }
                )
        return changes or None
    if definition.entity.endswith("Series") or "истори" in norm(definition.name):
        return [
            {
                "code": record.get("code"),
                "name": record.get("name"),
                "level": record.get("level"),
                "academic_year": record.get("academic_year"),
                "year": record.get("year"),
                "price": record.get("price"),
                "currency": record.get("currency"),
            }
            for record in records
            if record.get("price") is not None or record.get("year") is not None
        ]
    return None


def _is_main_budget_document(title: Any) -> bool:
    text = norm(title)
    return (
        "бюджет" in text
        and "основн" in text
        and "мгту" in text
        and "филиал" not in text
        and "бви" not in text
        and "квот" not in text
    )


def _canonical(value: Any) -> str:
    if isinstance(value, dict):
        return repr(sorted((str(key), _canonical(item)) for key, item in value.items()))
    if isinstance(value, list):
        return repr(sorted(_canonical(item) for item in value))
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def _dedupe_values(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        key = _canonical(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _confidence(definition: FieldDefinition, source_id: str, is_reserve: bool) -> float:
    reliability = norm(definition.reliability)
    base = {"высокая": 0.95, "средняя": 0.75, "низкая": 0.55}.get(reliability, 0.7)
    if is_reserve:
        base -= 0.15
    if "частич" in norm(definition.acquisition_status) or "частич" in norm(definition.coverage):
        base -= 0.1
    return max(0.1, min(1.0, round(base, 3)))


def project_fields(
    fields: list[FieldDefinition],
    extractions: list[ExtractionResult],
    source_states: dict[str, dict[str, Any]],
    selected_source_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = _flatten_records(extractions)
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_source[str(record.get("source_id", ""))].append(record)

    facts: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for definition in fields:
        considered_sources = list(dict.fromkeys(definition.source_ids + definition.reserve_source_ids))
        if not considered_sources:
            facts.append(_empty_fact(definition, "unsupported", "source is not configured"))
            continue
        if not set(considered_sources).intersection(selected_source_ids):
            facts.append(_empty_fact(definition, "not_selected", "source was not selected for this run"))
            continue

        candidates: list[dict[str, Any]] = []
        for source_id in considered_sources:
            if source_id not in selected_source_ids:
                continue
            is_reserve = source_id in definition.reserve_source_ids and source_id not in definition.source_ids
            source_records = [
                record
                for record in by_source.get(source_id, [])
                if record.get("record_type") in _allowed_types(definition.entity)
            ]
            derived = _derived_series(definition, source_records)
            if derived not in (None, [], {}):
                candidates.append(
                    {
                        "source_id": source_id,
                        "source_url": source_records[0].get("source_url") if source_records else None,
                        "record_id": source_records[0].get("record_id") if source_records else None,
                        "value": derived,
                        "confidence": _confidence(definition, source_id, is_reserve),
                        "is_reserve": is_reserve,
                    }
                )
                continue
            for record in source_records:
                value = _derived_value(definition, record)
                if value in (None, "", [], {}):
                    continue
                candidates.append(
                    {
                        "source_id": source_id,
                        "source_url": record.get("source_url"),
                        "record_id": record.get("record_id"),
                        "value": value,
                        "confidence": _confidence(definition, source_id, is_reserve),
                        "is_reserve": is_reserve,
                    }
                )

        state_candidates = [source_states.get(source_id, {}) for source_id in considered_sources if source_id in selected_source_ids]
        if not candidates:
            if state_candidates and all(state.get("status") in {"failed", "empty"} for state in state_candidates):
                facts.append(_empty_fact(definition, "source_unavailable", "all selected source requests failed", considered_sources))
            elif "нет надежного" in norm(definition.acquisition_status):
                facts.append(_empty_fact(definition, "unsupported", definition.limitation or "no reliable source"))
            else:
                facts.append(_empty_fact(definition, "not_found", "field was not found in extracted records", considered_sources))
            continue

        primary_candidates = [candidate for candidate in candidates if not candidate["is_reserve"]]
        winner_pool = primary_candidates or candidates
        winner = winner_pool[0]
        values = _dedupe_values([candidate["value"] for candidate in winner_pool])
        value: Any = values[0] if len(values) == 1 else values
        source_ids = list(dict.fromkeys(candidate["source_id"] for candidate in winner_pool))
        source_urls = list(dict.fromkeys(candidate["source_url"] for candidate in winner_pool if candidate.get("source_url")))
        candidate_sources = {candidate["source_id"] for candidate in candidates}
        different_values = len({_canonical(candidate["value"]) for candidate in candidates}) > 1
        different = len(candidate_sources) > 1 and different_values
        if different:
            conflict = {
                "field_id": definition.id,
                "field": definition.name,
                "entity": definition.entity,
                "candidates": candidates,
                "winner_source_id": winner["source_id"],
                "winner_reason": "primary source wins over reserve; otherwise first configured source",
            }
            conflicts.append(conflict)
        status = "conflict" if different else ("reserve" if winner["is_reserve"] else "extracted")
        if "вычисля" in norm(definition.acquisition_status):
            status = "derived" if not different else "conflict"
        facts.append(
            {
                "field_id": definition.id,
                "field": definition.name,
                "entity": definition.entity,
                "value": value,
                "status": status,
                "source_ids": source_ids,
                "source_urls": source_urls,
                "observed_at": max((state.get("fetched_at", "") for state in state_candidates), default=None),
                "confidence": winner["confidence"],
                "coverage": definition.coverage,
                "priority": definition.priority,
                "evidence": [
                    {
                        "record_id": candidate["record_id"],
                        "source_id": candidate["source_id"],
                        "source_url": candidate["source_url"],
                    }
                    for candidate in winner_pool
                ],
                "limitation": definition.limitation,
            }
        )
    return facts, conflicts


def _empty_fact(
    definition: FieldDefinition,
    status: str,
    reason: str,
    source_ids: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "field_id": definition.id,
        "field": definition.name,
        "entity": definition.entity,
        "value": None,
        "status": status,
        "source_ids": list(source_ids),
        "source_urls": [],
        "observed_at": None,
        "confidence": 0.0,
        "coverage": definition.coverage,
        "priority": definition.priority,
        "evidence": [],
        "reason": reason,
        "limitation": definition.limitation,
    }
