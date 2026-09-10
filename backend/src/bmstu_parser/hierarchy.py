from __future__ import annotations

"""Build a provenance-aware hierarchy from the parser's canonical records.

The hierarchy deliberately keeps a distinction between relationships that are
printed in an official row and relationships inferred by joining codes.  The
dashboard can therefore show a useful tree without presenting a derived link
as if it had been published directly by the university.
"""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from hashlib import sha1
from statistics import mean
from typing import Any, Iterable


_EDUCATION_CODE_RE = re.compile(r"(?<!\d)(?:\d{1,2})\.\d{2}\.\d{2}(?:[-/]\d+)?(?!\d)")
_UNIT_CODE_RE = re.compile(
    r"(?<![А-ЯЁA-Z])([А-ЯЁA-Z]{1,5})\s*-?\s*(\d{1,2})?(?![А-ЯЁA-Z])",
    re.IGNORECASE,
)
_ROW_TYPES = {"AdmissionRow", "EnrollmentRow"}
_STRUCTURE_TYPES = {
    "Faculty",
    "Department",
    "OrganizationalComplex",
    "OrganizationUnit",
    "StructuralSection",
}


def _norm(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKC", text).replace("ё", "е").casefold()
    return " ".join(text.split()).strip()


def _slug(value: Any) -> str:
    text = _norm(value)
    text = re.sub(r"[^\w.-]+", "-", text, flags=re.UNICODE).strip("-")
    return text or "unknown"


def _stable(prefix: str, *values: Any) -> str:
    payload = "|".join(_norm(value) for value in values)
    return f"{prefix}:{sha1(payload.encode('utf-8')).hexdigest()[:16]}"


def _record_value(record: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = record.get(name)
        if value not in (None, "", []):
            return value
    values = record.get("values")
    if isinstance(values, dict):
        lowered = {_norm(key): value for key, value in values.items()}
        for name in names:
            wanted = _norm(name)
            for key, value in lowered.items():
                if wanted == key or wanted in key or key in wanted:
                    if value not in (None, "", []):
                        return value
    return None


def _code(value: Any) -> str | None:
    if value is None:
        return None
    match = _EDUCATION_CODE_RE.search(str(value))
    return match.group(0) if match else None


def _unit_code(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).upper().replace("Ё", "Е")
    # Prefer codes commonly used by BMSTU (ФН-3, ИУ-7, РКТ, etc.).
    matches = list(_UNIT_CODE_RE.finditer(text))
    if not matches:
        return None
    match = matches[0]
    prefix, number = match.groups()
    if len(prefix) > 5:
        return None
    return f"{prefix.upper()}-{number}" if number else prefix.upper()


def _source_url(record: dict[str, Any]) -> str | None:
    value = record.get("source_url") or record.get("url") or record.get("document_url")
    return str(value) if value else None


def _source_scope(record: dict[str, Any]) -> str:
    return str(record.get("source_scope") or "Университет / головная организация")


def _is_data(record: dict[str, Any]) -> bool:
    return bool(record.get("is_data_row", True))


def _record_view(record: dict[str, Any]) -> dict[str, Any]:
    """Keep the complete extracted row while avoiding duplicated run paths."""
    return {
        key: value
        for key, value in record.items()
        if key not in {"run_dir"} and value is not None
    }


class _Graph:
    def __init__(self, source_definitions: Iterable[Any] | None = None) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        self.records: dict[str, dict[str, Any]] = {}
        self.sources: dict[str, dict[str, Any]] = {}
        for source in source_definitions or ():
            if hasattr(source, "to_dict"):
                value = source.to_dict()
            elif isinstance(source, dict):
                value = dict(source)
            else:
                continue
            source_id = str(value.get("id") or "")
            if source_id:
                self.sources[source_id] = value

    def node(
        self,
        node_id: str,
        node_type: str,
        label: Any,
        *,
        attributes: dict[str, Any] | None = None,
        record: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        item = self.nodes.get(node_id)
        if item is None:
            item = {
                "id": node_id,
                "type": node_type,
                "label": str(label or node_id),
                "attributes": {},
                "record_ids": [],
                "source_ids": [],
                "source_urls": [],
                "records": [],
            }
            self.nodes[node_id] = item
        if attributes:
            for key, value in attributes.items():
                if value not in (None, "", [], {}):
                    item["attributes"][key] = value
        if record:
            record_id = str(record.get("record_id") or _stable("record", json.dumps(record, sort_keys=True, default=str)))
            self.records.setdefault(record_id, _record_view(record))
            if record_id not in item["record_ids"]:
                item["record_ids"].append(record_id)
                # Full row data is attached to the node for direct inspection.
                item["records"].append(record_id)
            source_id = record.get("source_id")
            if source_id and source_id not in item["source_ids"]:
                item["source_ids"].append(source_id)
            source_url = _source_url(record)
            if source_url and source_url not in item["source_urls"]:
                item["source_urls"].append(source_url)
        return item

    def edge(
        self,
        from_id: str,
        to_id: str,
        relation: str,
        basis: str,
        *,
        record: dict[str, Any] | None = None,
        note: str | None = None,
    ) -> None:
        key = (from_id, to_id, relation, basis)
        item = self.edges.get(key)
        if item is None:
            item = {
                "id": _stable("edge", *key),
                "from": from_id,
                "to": to_id,
                "relation": relation,
                "basis": basis,
                "record_ids": [],
                "source_ids": [],
                "notes": [],
            }
            self.edges[key] = item
        if note and note not in item["notes"]:
            item["notes"].append(note)
        if record:
            record_id = str(record.get("record_id") or "")
            if record_id and record_id not in item["record_ids"]:
                item["record_ids"].append(record_id)
            source_id = record.get("source_id")
            if source_id and source_id not in item["source_ids"]:
                item["source_ids"].append(source_id)


def build_hierarchy(
    records: Iterable[dict[str, Any]],
    source_definitions: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Return a stable node/edge graph suitable for both JSON and the UI."""
    records = [dict(record) for record in records if isinstance(record, dict)]
    graph = _Graph(source_definitions)
    graph.node(
        "university:bmstu",
        "University",
        "МГТУ им. Н.Э. Баумана",
        attributes={"role": "root", "description": "Федеральное государственное автономное образовательное учреждение высшего образования"},
    )

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        record_type = str(record.get("record_type") or "SourceRecord")
        by_type[record_type].append(record)
        record_id = str(record.get("record_id") or _stable("record", json.dumps(record, sort_keys=True, default=str)))
        graph.records[record_id] = _record_view(record)

    for record in by_type.get("University", []):
        graph.node("university:bmstu", "University", record.get("name_short") or record.get("name_full") or "МГТУ им. Н.Э. Баумана", attributes={
            key: record.get(key)
            for key in ("name_full", "name_short", "type", "city", "address", "official_site", "contacts", "license", "accreditation", "founder", "ownership", "labels")
            if record.get(key) not in (None, "", [], {})
        }, record=record)

    # The first level is an explicit contour/site node. It is based on the
    # source map scope, not on an invented faculty relation.
    site_nodes: dict[str, str] = {}
    for record in records:
        scope = _source_scope(record)
        scope_id = site_nodes.setdefault(scope, _stable("site", scope))
        graph.node(scope_id, "Site", scope, attributes={"scope": scope}, record=record)
        graph.edge("university:bmstu", scope_id, "has_scope", "published", record=record)

    def attach(node_id: str, record: dict[str, Any], relation: str = "contains") -> None:
        scope_id = site_nodes.get(_source_scope(record))
        if scope_id:
            graph.edge(scope_id, node_id, relation, "published", record=record)

    # Organization tree.
    structure_by_key: dict[tuple[str, str], str] = {}
    structure_by_code: dict[str, str] = {}
    faculty_by_code: dict[str, str] = {}
    structure_by_name: dict[str, str] = {}
    faculty_by_name: dict[str, str] = {}
    for record_type in _STRUCTURE_TYPES:
        for record in by_type.get(record_type, []):
            name = _record_value(record, "name", "Наименование структурного подразделения") or record_type
            if _norm(name) in {"факультеты", "кафедры", "органы управления университета", "научно-исследовательские институты"}:
                # These are section labels. Keep them visible, but do not make
                # them look like a faculty or a department.
                node_type = "StructuralSection"
            else:
                node_type = record_type
            explicit_code = _record_value(record, "code", "Код")
            # A faculty/complex name often starts with «Ф-т» or «Научно-»;
            # it must never be shortened to a fake one-letter code. Only
            # departments need code extraction from their published name.
            code = _unit_code(explicit_code)
            if not code and node_type == "Department":
                code = _unit_code(name)
            node_id = _stable(node_type.lower(), code or name)
            structure_by_key[(node_type, _norm(name))] = node_id
            if code:
                structure_by_code.setdefault(_norm(code), node_id)
                if node_type == "Faculty":
                    faculty_by_code.setdefault(_norm(code), node_id)
            structure_by_name.setdefault(_norm(name), node_id)
            if node_type == "Faculty":
                faculty_by_name.setdefault(_norm(name), node_id)
            graph.node(node_id, node_type, name, attributes={
                key: _record_value(record, key)
                for key in ("code", "unit_type", "parent_name", "leader_name", "role", "room", "address", "official_site", "email", "provision", "contacts")
                if _record_value(record, key) not in (None, "", {}, [])
            }, record=record)
            attach(node_id, record)
    for record_type in _STRUCTURE_TYPES:
        for record in by_type.get(record_type, []):
            name = _record_value(record, "name", "Наименование структурного подразделения") or record_type
            node_type = "StructuralSection" if _norm(name) in {"факультеты", "кафедры", "органы управления университета", "научно-исследовательские институты"} else record_type
            node_id = structure_by_key.get((node_type, _norm(name)))
            if not node_id:
                continue
            parent_name = _record_value(record, "parent_name")
            if parent_name:
                parent_id = structure_by_name.get(_norm(parent_name))
                if parent_id:
                    basis = "derived" if record.get("parent_relation") == "derived_code_prefix" else "published"
                    graph.edge(parent_id, node_id, "contains", basis, record=record,
                               note="Кафедра сопоставлена с факультетом по префиксу кода" if basis == "derived" else None)
            elif node_type == "Department":
                # A department code can identify its faculty prefix, but this
                # is intentionally marked as a derived join in the graph.
                code = _unit_code(_record_value(record, "code", "name"))
                prefix = code.split("-", 1)[0] if code else None
                parent_id = faculty_by_code.get(_norm(prefix)) if prefix else None
                if not parent_id and prefix:
                    # The published S02 table has explicit department codes,
                    # but most faculty rows do not repeat their short code.
                    # These are transparent, reviewable prefix-to-name joins;
                    # they are never labelled as a published parent.
                    prefix_hints = {
                        "ФН": ("фундаментальн",),
                        "ИБМ": ("инженерный бизнес",),
                        "ИУ": ("информатик", "систем управления"),
                        "СМ": ("специальн", "машиностроен"),
                        "МТ": ("машиностроительн", "технолог"),
                        "Э": ("энергомашиностроен",),
                        "РЛ": ("радиоэлектрон", "лазерн"),
                        "БМТ": ("биомедицинск",),
                        "Л": ("лингвист",),
                        "СГН": ("социальн", "гуманитарн"),
                        "РК": ("робототехник", "комплексн", "автоматизац"),
                        "РКТ": ("ракетно-космическ",),
                        "ПС": ("приборостроительн",),
                        "АК": ("аэрокосмическ",),
                        "ЛТ": ("лесного хозяйства", "лесопромышленн"),
                    }
                    hints = prefix_hints.get(prefix)
                    if hints:
                        for candidate_name, candidate_id in faculty_by_name.items():
                            if candidate_name and all(hint in candidate_name for hint in hints):
                                parent_id = candidate_id
                                break
                if parent_id:
                    graph.edge(parent_id, node_id, "contains", "derived", record=record,
                               note="Связь выведена из префикса кода кафедры и названия факультета")

    direction_nodes: dict[str, str] = {}
    program_nodes: dict[str, str] = {}
    offering_nodes: dict[str, str] = {}

    for record in by_type.get("Direction", []):
        code = str(record.get("code") or _code(record.get("name")) or "")
        if not code:
            continue
        node_id = direction_nodes.setdefault(_norm(code), _stable("direction", code))
        graph.node(node_id, "Direction", record.get("name") or code, attributes={
            "code": code, "level": record.get("level"),
        }, record=record)
        attach(node_id, record)
        level = record.get("level")
        if level:
            level_id = _stable("level", level)
            graph.node(level_id, "EducationLevel", level)
            graph.edge(level_id, node_id, "has_direction", "published", record=record)
            graph.edge("university:bmstu", level_id, "offers_level", "published", record=record)

    for record in by_type.get("Program", []):
        direction_code = str(record.get("direction_code") or _code(record.get("code")) or "")
        program_code = str(record.get("code") or record.get("program_code") or direction_code)
        if not program_code:
            continue
        node_id = program_nodes.setdefault(_norm(program_code), _stable("program", program_code, record.get("name")))
        graph.node(node_id, "Program", record.get("name") or program_code, attributes={
            key: record.get(key) for key in ("code", "direction_code", "profile", "level", "form", "duration", "qualification", "department_code") if record.get(key) not in (None, "", [], {})
        }, record=record)
        attach(node_id, record)
        direction_id = direction_nodes.get(_norm(direction_code))
        if direction_id:
            graph.edge(direction_id, node_id, "has_program", "published", record=record)

    for record in by_type.get("ProgramOffering", []):
        program_code = str(record.get("program_code") or record.get("code") or "")
        direction_code = str(record.get("direction_code") or _code(program_code) or "")
        key = record.get("record_id") or f"{program_code}|{record.get('form')}|{record.get('department_code')}|{record.get('row_index')}"
        node_id = offering_nodes.setdefault(str(key), _stable("offering", key))
        graph.node(node_id, "ProgramOffering", record.get("profile") or program_code, attributes={
            key: record.get(key) for key in ("program_code", "direction_code", "profile", "department_code", "form", "duration", "qualification", "table_index", "row_index") if record.get(key) not in (None, "", [], {})
        }, record=record)
        attach(node_id, record)
        program_id = program_nodes.get(_norm(program_code))
        if program_id:
            graph.edge(program_id, node_id, "has_offering", "published", record=record)
        department_code = _unit_code(record.get("department_code"))
        department_id = structure_by_code.get(_norm(department_code)) if department_code else None
        if department_id:
            graph.edge(node_id, department_id, "owned_by_department", "published", record=record)
        elif record.get("department_code"):
            graph.node(_stable("unresolved-department", record.get("department_code")), "UnresolvedReference", str(record.get("department_code")), attributes={"field": "department_code", "value": record.get("department_code")}, record=record)

    for record_type in ("DirectionStandard",):
        for record in by_type.get(record_type, []):
            code = str(record.get("direction_code") or record.get("code") or "")
            node_id = _stable("standard", code, record.get("standard_type"), record.get("name"))
            graph.node(node_id, "DirectionStandard", record.get("name") or code, attributes={
                key: record.get(key) for key in ("code", "direction_code", "standard_type", "title") if record.get(key) not in (None, "", [], {})
            }, record=record)
            attach(node_id, record)
            direction_id = direction_nodes.get(_norm(code))
            if direction_id:
                graph.edge(direction_id, node_id, "has_standard", "code_join", record=record)

    # Tuition and paid education use the published education code as a join
    # key. There is intentionally no tuition -> faculty shortcut.
    for record_type in ("Tuition", "PaidEducation"):
        for record in by_type.get(record_type, []):
            code = str(record.get("code") or _code(record.get("name")) or "")
            if not code:
                continue
            node_id = _stable("tuition", record_type, code, record.get("academic_year"), record.get("price"))
            graph.node(node_id, record_type, record.get("name") or code, attributes={
                key: record.get(key) for key in ("code", "academic_year", "year", "level", "price", "currency", "table_index", "row_index") if record.get(key) not in (None, "", [], {})
            }, record=record)
            attach(node_id, record, "publishes")
            target = direction_nodes.get(_norm(code)) or program_nodes.get(_norm(code))
            if target:
                graph.edge(target, node_id, "has_price", "code_join", record=record)
            else:
                graph.node(_stable("unresolved-code", code), "UnresolvedReference", code, attributes={"field": "education_code", "value": code}, record=record)

    for record in by_type.get("Course", []):
        code = str(record.get("direction_code") or _code(record.get("name")) or "")
        node_id = _stable("course", code, record.get("name"), record.get("eor_code"))
        graph.node(node_id, "Course", record.get("name") or code, attributes={
            key: record.get(key) for key in ("direction_code", "department_code", "eor_code", "table_index", "row_index") if record.get(key) not in (None, "", [], {})
        }, record=record)
        attach(node_id, record)
        direction_id = direction_nodes.get(_norm(code))
        if direction_id:
            graph.edge(direction_id, node_id, "has_course", "code_join", record=record)
        department_id = structure_by_code.get(_norm(_unit_code(record.get("department_code")))) if record.get("department_code") else None
        if department_id:
            graph.edge(node_id, department_id, "owned_by_department", "code_join", record=record)

    _add_admission_graph(graph, by_type, direction_nodes, program_nodes, offering_nodes, site_nodes)

    for record in by_type.get("InternationalPartner", []):
        name = record.get("partner_name") or record.get("name") or "Партнёр"
        partner_id = _stable("partner", name, record.get("country"))
        graph.node(partner_id, "InternationalPartner", name, attributes={
            key: record.get(key) for key in ("country", "partner_name") if record.get(key) not in (None, "", [], {})
        }, record=record)
        attach(partner_id, record)
        graph.edge("university:bmstu", partner_id, "has_partner", "published", record=record)
    for record in by_type.get("PartnerRelation", []):
        name = record.get("partner_name") or record.get("name")
        partner_id = _stable("partner", name, record.get("country")) if name else None
        relation_id = _stable("agreement", name, record.get("agreement_type"), record.get("agreement_date"), record.get("validity"))
        graph.node(relation_id, "PartnerAgreement", record.get("agreement_type") or "Соглашение", attributes={
            key: record.get(key) for key in ("country", "agreement_type", "agreement_date", "validity") if record.get(key) not in (None, "", [], {})
        }, record=record)
        attach(relation_id, record)
        if partner_id:
            graph.edge(partner_id, relation_id, "has_agreement", "published", record=record)

    for record_type in ("UniversityRanking", "UniversityFeature", "OlympiadBenefit", "AdmissionRule", "Enrichment", "Auxiliary", "Document", "SourceRecord"):
        for record in by_type.get(record_type, []):
            label = record.get("name") or record.get("title") or record.get("feature") or record_type
            node_id = _stable("evidence", record_type, label, record.get("source_id"), record.get("url"), record.get("row_index"))
            graph.node(node_id, record_type, label, attributes={
                key: record.get(key) for key in ("year", "rank", "ranking", "feature", "title", "url", "document_type", "table_index", "row_index", "values", "raw_values") if record.get(key) not in (None, "", [], {})
            }, record=record)
            attach(node_id, record, "has_evidence")
            if record_type == "Enrichment":
                linked = structure_by_name.get(_norm(label))
                if linked:
                    graph.edge(linked, node_id, "has_details", "published", record=record)
            else:
                graph.edge("university:bmstu", node_id, "has_evidence", "published", record=record)

    for item in graph.nodes.values():
        item["record_count"] = len(item["record_ids"])
        item["source_count"] = len(item["source_ids"])
        # Keep the UI payload compact: record bodies remain in the indexed
        # records map, while nodes only store IDs.
        item.pop("records", None)

    edges = list(graph.edges.values())
    node_values = list(graph.nodes.values())
    unresolved = [node for node in node_values if node["type"] == "UnresolvedReference"]
    return {
        "version": 2,
        "generated_from": "canonical parser records",
        "root_id": "university:bmstu",
        "nodes": node_values,
        "edges": edges,
        "records": graph.records,
        "sources": graph.sources,
        "stats": {
            "record_count": len(records),
            "node_count": len(node_values),
            "edge_count": len(edges),
            "records_by_type": dict(Counter(str(item.get("record_type") or "SourceRecord") for item in records)),
            "nodes_by_type": dict(Counter(str(item.get("type")) for item in node_values)),
            "edges_by_basis": dict(Counter(str(item.get("basis")) for item in edges)),
            "unresolved_count": len(unresolved),
        },
    }


def _add_admission_graph(
    graph: _Graph,
    by_type: dict[str, list[dict[str, Any]]],
    direction_nodes: dict[str, str],
    program_nodes: dict[str, str],
    offering_nodes: dict[str, str],
    site_nodes: dict[str, str],
) -> None:
    for record_type in _ROW_TYPES:
        records = by_type.get(record_type, [])
        if not records:
            continue
        campaign_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            year = str(record.get("admission_year") or record.get("year") or "текущая")
            campaign_groups[(str(record.get("source_id")), year)].append(record)
        for (source_id, year), campaign_records in campaign_groups.items():
            campaign_id = _stable("campaign", record_type, source_id, year)
            campaign_type = "AdmissionCampaign" if record_type == "AdmissionRow" else "EnrollmentCampaign"
            graph.node(campaign_id, campaign_type, f"Кампания {year}", attributes={
                "source_id": source_id,
                "year": year,
                "row_count": len(campaign_records),
                "data_row_count": sum(_is_data(item) for item in campaign_records),
            })
            for record in campaign_records:
                graph.node(campaign_id, campaign_type, f"Кампания {year}", record=record)
            scope = str(campaign_records[0].get("source_scope") or "")
            if scope in site_nodes:
                graph.edge(site_nodes[scope], campaign_id, "has_campaign", "published", record=campaign_records[0])
            competitions: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for record in campaign_records:
                url = str(record.get("document_url") or record.get("url") or record.get("title") or "без документа")
                competitions[url].append(record)
            for competition_key, competition_records in competitions.items():
                title = competition_records[0].get("document_title") or competition_records[0].get("title") or competition_key.rsplit("/", 1)[-1]
                competition_id = _stable("competition", record_type, source_id, year, competition_key)
                scores = [record.get("score") for record in competition_records if isinstance(record.get("score"), (int, float))]
                program_codes = sorted({code for record in competition_records for code in _EDUCATION_CODE_RE.findall(str(record.get("programs") or record.get("program_code") or ""))})
                graph.node(competition_id, "AdmissionCompetition", title, attributes={
                    "document_url": competition_key if competition_key != "без документа" else None,
                    "row_count": len(competition_records),
                    "program_codes": program_codes,
                    "score_min": min(scores) if scores else None,
                    "score_max": max(scores) if scores else None,
                    "score_average": round(mean(scores), 2) if scores else None,
                })
                for record in competition_records:
                    graph.node(competition_id, "AdmissionCompetition", title, record=record)
                graph.edge(campaign_id, competition_id, "has_competition", "published", record=competition_records[0])
                # Individual admission rows stay in the complete records map
                # and are attached to the competition node. This keeps the
                # tree usable while still allowing the detail pane to show
                # every applicant/order field after opening the competition.
                record_for_code: dict[str, dict[str, Any]] = {}
                for record in competition_records:
                    for code in _EDUCATION_CODE_RE.findall(str(record.get("programs") or record.get("program_code") or "")):
                        record_for_code.setdefault(code, record)
                offering_by_code = {
                    _norm(str(node.get("attributes", {}).get("program_code"))): node["id"]
                    for node in graph.nodes.values()
                    if node.get("type") == "ProgramOffering" and node.get("attributes", {}).get("program_code")
                }
                for code, record in record_for_code.items():
                    target = offering_by_code.get(_norm(code)) or program_nodes.get(_norm(code)) or direction_nodes.get(_norm(code))
                    if target:
                        graph.edge(competition_id, target, "applies_to", "code_join", record=record)
