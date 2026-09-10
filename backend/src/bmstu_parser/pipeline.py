from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Iterable
from typing import Any
from urllib.parse import quote, urljoin, urlparse

from .adapters import parse_source
from .fetch import FetchConfig, Fetcher
from .hierarchy import build_hierarchy
from .models import ExtractionResult, SourceDefinition
from .pdf import is_pdf
from .priority_pdf import parse_priority_pdf, priority_source_definition
from .profile import build_profile
from .projector import project_fields
from .report import write_profile_assets
from .source_map import SourceMap

FOCUSED_PROFILE_SOURCE_IDS = frozenset({"S01", "S02", "S06", "S09", "S10", "S12", "S19"})
DISABLED_SOURCE_IDS = frozenset({"S16", "S17", "S18"})
FACULTIES_SOURCE_URL = "https://bmstu.ru/faculties-and-branches"
MAJORS_SOURCE_URL = "https://bmstu.ru/bachelor/majors"
MAJORS_API_URL = "https://api.www.bmstu.ru/majors/baccalaureate-and-specialty?limit=100&offset=0"


@dataclass(slots=True)
class ParserConfig:
    source_map: Path
    output_dir: Path
    sources: tuple[str, ...] = ()
    browser_mode: str = "auto"
    timeout_seconds: float = 30.0
    retries: int = 2
    max_body_bytes: int = 30_000_000
    download_documents: bool = False
    max_followups: int = 500
    followup_depth: int = 4
    priority_pdfs: tuple[Path, ...] = ()


def run_parser(config: ParserConfig) -> dict[str, Any]:
    source_map = SourceMap.from_xlsx(config.source_map)
    _apply_effective_source_urls(source_map)
    priority_sources = [priority_source_definition(path) for path in config.priority_pdfs]
    # The default run is intentionally limited to sources that can populate
    # the focused eight-block profile. Ratings are outside that profile and
    # are never requested, even when they remain listed in the workbook.
    selected_sources = source_map.selected_sources(config.sources)
    if not config.sources:
        selected_sources = [source for source in selected_sources if source.id in FOCUSED_PROFILE_SOURCE_IDS]
    selected_sources = [source for source in selected_sources if source.id not in DISABLED_SOURCE_IDS]
    selected_ids = {source.id for source in selected_sources}
    source_map.sources.extend(priority_sources)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = config.output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    _write_json(config.output_dir / "source_map.json", source_map.to_dict())
    run_started = datetime.now(timezone.utc).isoformat()
    fetcher = Fetcher(
        FetchConfig(
            timeout_seconds=config.timeout_seconds,
            retries=config.retries,
            browser_mode=config.browser_mode,
            max_body_bytes=config.max_body_bytes,
        )
    )
    snapshots: list[dict[str, Any]] = []
    source_states: dict[str, dict[str, Any]] = {}
    extractions: list[ExtractionResult] = []
    all_records: list[dict[str, Any]] = []
    all_tables: list[dict[str, Any]] = []
    all_network_payloads: list[dict[str, Any]] = []

    try:
        for source in selected_sources:
            resource = fetcher.fetch(source.url, force_browser=source.id in {"S07", "S08"})
            extension = _extension(resource.content_type, resource.final_url, resource.body)
            content_path = None
            if resource.body:
                filename = f"{source.id}_{resource.content_hash[:16]}.{extension}"
                target = raw_dir / filename
                target.write_bytes(resource.body)
                content_path = str(Path("raw") / filename)
            snapshots.append({"source_id": source.id, **resource.snapshot_dict(content_path)})
            source_states[source.id] = {
                "status": "ok" if resource.ok else ("empty" if not resource.body else "failed"),
                "fetched_at": resource.fetched_at,
                "status_code": resource.status_code,
                "access_mode": resource.access_mode,
                "error": resource.error,
            }
            extraction = parse_source(source, resource)
            extractions.append(extraction)
            all_records.extend(extraction.records)
            all_tables.extend(
                {
                    "source_id": source.id,
                    "source_url": extraction.source_url,
                    **table,
                }
                for table in extraction.tables
            )
            all_network_payloads.extend(
                {"source_id": source.id, **payload}
                for payload in extraction.network_payloads
            )

        linked_count = 0
        linked_pdf_count = 0
        if config.download_documents or source.id in {"S02", "S06"}:
            for source in selected_sources:
                base_extraction = next(
                    (item for item in extractions if item.source_id == source.id),
                    None,
                )
                if base_extraction is None:
                    continue
                linked = _follow_discovered_documents(
                    source=source,
                    extraction=base_extraction,
                    fetcher=fetcher,
                    raw_dir=raw_dir,
                    max_followups=max(0, config.max_followups),
                    max_depth=max(1, config.followup_depth),
                )
                linked_count += len(linked["snapshots"])
                linked_pdf_count += len(linked["pdf_extractions"])
                snapshots.extend(linked["snapshots"])
                for extraction in linked["extractions"]:
                    extractions.append(extraction)
                    all_records.extend(extraction.records)
                    all_tables.extend(
                        {
                            "source_id": source.id,
                            "source_url": extraction.source_url,
                            **table,
                        }
                        for table in extraction.tables
                    )
    finally:
        fetcher.close()

    for path, source in zip(config.priority_pdfs, priority_sources):
        extraction = parse_priority_pdf(path)
        raw_body = Path(path).read_bytes()
        filename = f"{source.id}_{__import__('hashlib').sha256(raw_body).hexdigest()[:16]}.pdf"
        (raw_dir / filename).write_bytes(raw_body)
        snapshots.append({
            "source_id": source.id,
            "requested_url": source.url,
            "final_url": source.url,
            "status_code": 200,
            "content_type": "application/pdf",
            "fetched_at": extraction.captured_at,
            "access_mode": "local",
            "content_hash": __import__('hashlib').sha256(raw_body).hexdigest(),
            "bytes": len(raw_body),
            "path": str(Path("raw") / filename),
            "network_payload_count": 0,
        })
        source_states[source.id] = {
            "status": "ok",
            "fetched_at": extraction.captured_at,
            "status_code": 200,
            "access_mode": "local",
            "error": None,
        }
        extractions.append(extraction)
        all_records.extend(extraction.records)
        all_tables.extend({
            "source_id": source.id,
            "source_url": extraction.source_url,
            **table,
        } for table in extraction.tables)
    selected_ids.update(source.id for source in priority_sources)

    facts, conflicts = project_fields(source_map.fields, extractions, source_states, selected_ids)
    hierarchy = build_hierarchy(all_records, source_map.sources)
    profile = build_profile(all_records, all_tables, hierarchy)
    _write_jsonl(config.output_dir / "snapshots.jsonl", snapshots)
    _write_jsonl(config.output_dir / "records.jsonl", all_records)
    _write_jsonl(config.output_dir / "tables.jsonl", all_tables)
    _write_jsonl(config.output_dir / "network.jsonl", all_network_payloads)
    _write_jsonl(config.output_dir / "facts.jsonl", facts)
    _write_jsonl(config.output_dir / "conflicts.jsonl", conflicts)
    _write_jsonl(
        config.output_dir / "extractions.jsonl",
        [extraction.to_dict(include_text=False) for extraction in extractions],
    )
    _write_json(config.output_dir / "hierarchy.json", hierarchy)
    _write_json(config.output_dir / "profile.json", profile)
    write_profile_assets(config.output_dir, profile)

    status_counts: dict[str, int] = {}
    for fact in facts:
        status = str(fact.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
    source_status_counts: dict[str, int] = {}
    for state in source_states.values():
        status = str(state.get("status", "unknown"))
        source_status_counts[status] = source_status_counts.get(status, 0) + 1
    summary = {
        "run_started": run_started,
        "run_finished": datetime.now(timezone.utc).isoformat(),
        "source_map": str(config.source_map.resolve()),
        "output_dir": str(config.output_dir.resolve()),
        "browser_mode": config.browser_mode,
        "selected_sources": [source.id for source in selected_sources],
        "source_count": len(selected_sources),
        "source_statuses": source_status_counts,
        "field_count": len(source_map.fields),
        "fact_count": len(facts),
        "facts_with_value": sum(fact.get("value") is not None for fact in facts),
        "fact_statuses": status_counts,
        "record_count": len(all_records),
        "table_count": len(all_tables),
        "network_payload_count": len(all_network_payloads),
        "followup_count": linked_count,
        "followup_pdf_count": linked_pdf_count,
        "priority_pdf_paths": [str(Path(path).resolve()) for path in config.priority_pdfs],
        "priority_source_ids": [source.id for source in priority_sources],
        "conflict_count": len(conflicts),
        "hierarchy_node_count": hierarchy["stats"]["node_count"],
        "hierarchy_edge_count": hierarchy["stats"]["edge_count"],
        "hierarchy_unresolved_count": hierarchy["stats"]["unresolved_count"],
        "warnings": [warning for extraction in extractions for warning in extraction.warnings],
    }
    _write_json(config.output_dir / "run.json", summary)
    return summary


_FOLLOWUP_EXTENSIONS = (".json", ".pdf", ".doc", ".docx", ".xls", ".xlsx")
_FOLLOWUP_KEYS = {"href", "file", "data", "url", "download", "path"}


def _follow_discovered_documents(
    source: SourceDefinition,
    extraction: ExtractionResult,
    fetcher: Fetcher,
    raw_dir: Path,
    max_followups: int,
    max_depth: int,
) -> dict[str, list[Any]]:
    if max_followups == 0:
        return {"snapshots": [], "extractions": []}
    queue: deque[tuple[str, int, str, dict[str, Any]]] = deque()
    initial_urls: list[str] = []
    document_meta = {
        str(record.get("url")): {
            key: value for key, value in record.items()
            if key in {"title", "program_code", "direction_code", "program_profile", "profile_code", "study_plan_url", "description", "duration"}
        }
        for record in extraction.records
        if isinstance(record.get("url"), str)
    }
    initial_urls.extend(
        str(record["url"])
        for record in extraction.records
        if isinstance(record.get("url"), str)
    )
    for payload in extraction.network_payloads:
        body = payload.get("body")
        if not isinstance(body, str):
            continue
        try:
            decoded = json.loads(body)
        except json.JSONDecodeError:
            continue
        initial_urls.extend(_urls_from_json(decoded, extraction.source_url))
    if source.id == "S06" and extraction.source_url.rstrip("/") == MAJORS_SOURCE_URL.rstrip("/"):
        initial_urls.append(MAJORS_API_URL)
    for url in _unique_allowed_urls(initial_urls, source.url, source.id):
        queue.append((url, 1, extraction.source_url, dict(document_meta.get(url, {}))))

    snapshots: list[dict[str, Any]] = []
    linked_extractions: list[ExtractionResult] = []
    seen: set[str] = set()
    while queue and len(snapshots) < max_followups:
        url, depth, discovered_from, context = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        resource = fetcher.fetch(url)
        extension = _extension(resource.content_type, resource.final_url, resource.body)
        content_path = None
        if resource.body:
            filename = f"{source.id}_linked_{resource.content_hash[:16]}.{extension}"
            target = raw_dir / filename
            target.write_bytes(resource.body)
            content_path = str(Path("raw") / filename)
        snapshots.append(
            {
                "source_id": source.id,
                "kind": "followup",
                "discovered_from": discovered_from,
                "depth": depth,
                **resource.snapshot_dict(content_path),
            }
        )
        if not resource.body:
            continue
        if is_pdf(resource.body, resource.content_type, resource.final_url):
            linked_extraction = parse_source(source, resource, {
                **context,
                "document_url": context.get("study_plan_url") or context.get("document_url") or discovered_from,
                "download_url": resource.final_url,
            })
            for record in linked_extraction.records:
                record["discovered_from"] = discovered_from
                if context.get("title"):
                    record["document_title"] = context["title"]
            linked_extractions.append(linked_extraction)
            continue
        host = (urlparse(resource.final_url or url).hostname or "").casefold()
        if source.id == "S06" and host == "disk.yandex.ru" and depth < max_depth:
            public_url = resource.final_url or url
            api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources?public_key={quote(public_url, safe='')}"
            queue.append((api_url, depth + 1, public_url, context))
            continue
        if source.id == "S06" and host == "cloud-api.yandex.net":
            for download_url in _yandex_download_urls(resource.body, resource.encoding):
                queue.append((download_url, depth, resource.final_url or url, context))
            continue
        if source.id in {"S02", "S06"} and (
            "json" in (resource.content_type or "").casefold()
            or "html" in (resource.content_type or "").casefold()
            or resource.body.lstrip().startswith(b"<!DOCTYPE")
            or resource.body.lstrip().startswith(b"<html")
        ):
            linked_extraction = parse_source(source, resource, context)
            for record in linked_extraction.records:
                record["discovered_from"] = discovered_from
            linked_extractions.append(linked_extraction)
            if depth < max_depth:
                child_records = [
                    record for record in linked_extraction.records
                    if isinstance(record.get("url"), str)
                ]
                child_urls = [str(record["url"]) for record in child_records]
                for child_url in _unique_allowed_urls(child_urls, source.url, source.id):
                    if child_url not in seen:
                        child_context = dict(context)
                        child_context.update(document_meta.get(child_url, {}))
                        child_record = next((record for record in child_records if record.get("url") == child_url), None)
                        if child_record:
                            child_context.update({
                                key: child_record.get(key)
                                for key in ("title", "program_code", "direction_code", "program_profile", "profile_code", "study_plan_url", "description", "duration")
                                if child_record.get(key) not in (None, "", [], {})
                            })
                        queue.append((child_url, depth + 1, resource.final_url or url, child_context))
        if depth >= max_depth:
            continue
        if "json" not in (resource.content_type or "").casefold() and not resource.final_url.casefold().split("?", 1)[0].endswith(".json"):
            continue
        try:
            decoded = json.loads(resource.body.decode(resource.encoding or "utf-8", errors="replace"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        for child_url in _unique_allowed_urls(_urls_from_json(decoded, resource.final_url), source.url, source.id):
            if child_url not in seen:
                queue.append((child_url, depth + 1, resource.final_url, context))
    return {
        "snapshots": snapshots,
        "extractions": linked_extractions,
        "pdf_extractions": [item for item in linked_extractions if item.parser == "bmstu.pdf"],
    }


def _urls_from_json(value: Any, base_url: str) -> list[str]:
    urls: list[str] = []

    def visit(node: Any, key: str | None = None) -> None:
        if isinstance(node, dict):
            for child_key, child in node.items():
                normalized_key = str(child_key).casefold()
                if normalized_key in _FOLLOWUP_KEYS and isinstance(child, str):
                    urls.append(urljoin(base_url, child.strip()))
                visit(child, normalized_key)
        elif isinstance(node, list):
            for child in node:
                visit(child, key)

    visit(value)
    return urls


def _unique_allowed_urls(urls: Iterable[str], source_url: str, source_id: str | None = None) -> list[str]:
    source_host = urlparse(source_url).hostname
    result: list[str] = []
    seen: set[str] = set()
    for raw_url in urls:
        if not isinstance(raw_url, str) or not raw_url:
            continue
        url = urljoin(source_url, raw_url)
        parsed = urlparse(url)
        host = (parsed.hostname or "").casefold()
        allowed_hosts = {source_host.casefold() if source_host else ""}
        if source_id == "S06":
            allowed_hosts.update({"api.www.bmstu.ru", "clck.ru", "disk.yandex.ru", "cloud-api.yandex.net", "downloader.disk.yandex.ru"})
        if parsed.scheme not in {"http", "https"} or host not in allowed_hosts:
            continue
        path = parsed.path.casefold()
        is_special = source_id == "S02" and "/faculty/" in path
        is_major = source_id == "S06" and (
            "/bachelor/majors/" in path
            or path.endswith("/majors/baccalaureate-and-specialty")
            or host == "clck.ru"
            or (host == "disk.yandex.ru" and "/d/" in path)
            or host in {"cloud-api.yandex.net", "downloader.disk.yandex.ru"}
        )
        if not parsed.path.casefold().endswith(_FOLLOWUP_EXTENSIONS) and not is_special and not is_major:
            continue
        if url in seen:
            continue
        seen.add(url)
        result.append(url)
    # В SPA рядом с полезными списками встречаются служебные PDF (например,
    # инструкция по привязке заявления). Сначала обрабатываем JSON-реестры и
    # URL под /lists/, чтобы небольшой лимит follow-up давал полезные данные.
    return sorted(
        result,
        key=lambda url: (
            _followup_path_rank(urlparse(url).path),
            0 if urlparse(url).path.casefold().endswith(".json") else 1,
            url,
        ),
    )


def _yandex_download_urls(body: bytes, encoding: str | None) -> list[str]:
    try:
        payload = json.loads(body.decode(encoding or "utf-8", errors="replace"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    items = payload.get("_embedded", {}).get("items", []) if isinstance(payload, dict) else []
    result: list[str] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        direct = item.get("file")
        if isinstance(direct, str) and direct:
            result.append(direct)
    return result


def _apply_effective_source_urls(source_map: SourceMap) -> None:
    """Apply the current official page routes over legacy workbook aliases.

    The workbook is retained as the source-map contract, but S02 used to
    point at the old structural-information table. The parser must never
    request that route after the migration to the public faculty catalogue.
    """
    replacements = {
        "S02": (FACULTIES_SOURCE_URL, "Факультеты и кафедры — официальный каталог"),
        "S06": (MAJORS_SOURCE_URL, "Программы первого курса — официальный каталог"),
        "S16": (FACULTIES_SOURCE_URL, "Отключено: старый дубль структурной страницы"),
    }
    for source in source_map.sources:
        replacement = replacements.get(source.id)
        if not replacement:
            continue
        source.url, source.name = replacement
        source_map._aliases[source.url.casefold()] = source.id
    for field in source_map.fields:
        if field.url and "/sveden/struct/" in field.url.casefold():
            field.url = FACULTIES_SOURCE_URL
        if field.reserve_url and "/sveden/struct/" in field.reserve_url.casefold():
            field.reserve_url = FACULTIES_SOURCE_URL


def _followup_path_rank(path: str) -> int:
    lowered = path.casefold()
    if lowered.endswith(("/orders.json", "/registered.json")):
        return 0
    if "/lists/upload/orders/" in lowered or "/lists/upload/registered/" in lowered:
        return 1
    if "/lists/upload/enrollees/" in lowered:
        return 2
    if "/lists/" in lowered:
        return 3
    return 4


def _extension(content_type: str | None, url: str, body: bytes) -> str:
    lowered = (content_type or "").casefold()
    if body.startswith(b"%PDF") or "pdf" in lowered or url.casefold().split("?", 1)[0].endswith(".pdf"):
        return "pdf"
    if "json" in lowered or url.casefold().split("?", 1)[0].endswith(".json"):
        return "json"
    return "html"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, values: Iterable[Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for value in values:
            handle.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
