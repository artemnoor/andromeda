from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .hierarchy import build_hierarchy
from .profile import build_profile
from .priority_pdf import parse_priority_pdf, priority_source_definition


def merge_runs(
    input_dirs: Iterable[Path],
    output_dir: Path,
    priority_pdfs: Iterable[Path] = (),
) -> dict[str, Any]:
    """Объединяет независимые запуски в одну аудируемую выгрузку."""
    run_dirs = [Path(path) for path in input_dirs]
    entries: list[tuple[Path, dict[str, Any]]] = []
    for run_dir in run_dirs:
        run_path = run_dir / "run.json"
        if not run_path.exists():
            continue
        entries.append((run_dir, json.loads(run_path.read_text(encoding="utf-8"))))
    if not entries:
        raise ValueError("Не найден ни один run.json для объединения")

    output_dir.mkdir(parents=True, exist_ok=True)
    first_map = entries[0][0] / "source_map.json"
    if first_map.exists():
        (output_dir / "source_map.json").write_text(first_map.read_text(encoding="utf-8"), encoding="utf-8")

    merged_records = _merge_records(entries, "records.jsonl")
    merged_tables = _merge_jsonl(entries, "tables.jsonl")
    merged_network = _merge_jsonl(entries, "network.jsonl")
    merged_snapshots = _merge_jsonl(entries, "snapshots.jsonl")
    merged_conflicts = _merge_jsonl(entries, "conflicts.jsonl")
    merged_extractions = _merge_jsonl(entries, "extractions.jsonl")
    merged_facts = _merge_facts(entries)
    priority_paths = [Path(path).expanduser().resolve() for path in priority_pdfs]
    priority_sources = [priority_source_definition(path) for path in priority_paths]
    for path, source in zip(priority_paths, priority_sources):
        extraction = parse_priority_pdf(path)
        merged_records.extend(extraction.records)
        merged_tables.extend({
            "source_id": source.id,
            "source_url": extraction.source_url,
            **table,
        } for table in extraction.tables)
        merged_extractions.append(extraction.to_dict(include_text=False))
        merged_snapshots.append({
            "source_id": source.id,
            "requested_url": source.url,
            "final_url": source.url,
            "status_code": 200,
            "content_type": "application/pdf",
            "fetched_at": extraction.captured_at,
            "access_mode": "local",
            "content_hash": next((item.get("content_hash") for item in extraction.records if item.get("record_type") == "Document"), None),
            "bytes": path.stat().st_size,
            "path": str(path),
            "network_payload_count": 0,
        })
    source_definitions: list[dict[str, Any]] = []
    if first_map.exists():
        source_definitions = list(json.loads(first_map.read_text(encoding="utf-8")).get("sources", []))
    source_definitions.extend(source.to_dict() for source in priority_sources)
    if source_definitions:
        source_map_payload = json.loads(first_map.read_text(encoding="utf-8")) if first_map.exists() else {}
        source_map_payload["sources"] = source_definitions
        (output_dir / "source_map.json").write_text(
            json.dumps(source_map_payload, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
    hierarchy = build_hierarchy(merged_records, source_definitions)
    profile = build_profile(merged_records, merged_tables, hierarchy)

    _write_jsonl(output_dir / "records.jsonl", merged_records)
    _write_jsonl(output_dir / "tables.jsonl", merged_tables)
    _write_jsonl(output_dir / "network.jsonl", merged_network)
    _write_jsonl(output_dir / "snapshots.jsonl", merged_snapshots)
    _write_jsonl(output_dir / "conflicts.jsonl", merged_conflicts)
    _write_jsonl(output_dir / "extractions.jsonl", merged_extractions)
    _write_jsonl(output_dir / "facts.jsonl", merged_facts)
    (output_dir / "hierarchy.json").write_text(
        json.dumps(hierarchy, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (output_dir / "profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    write_profile_assets(output_dir, profile)

    source_states: dict[str, list[str]] = defaultdict(list)
    warnings: list[str] = []
    for run_dir, run in entries:
        snapshots = _read_jsonl(run_dir / "snapshots.jsonl")
        for snapshot in snapshots:
            if snapshot.get("kind") == "followup":
                continue
            source_id = snapshot.get("source_id")
            if source_id is None:
                continue
            source_states[str(source_id)].append(_snapshot_status(snapshot))
        # Старые/неполные запуски могли не успеть сохранить snapshots.jsonl.
        if not snapshots:
            for source_id in run.get("selected_sources", []):
                statuses = run.get("source_statuses", {})
                source_states[str(source_id)].extend(str(status) for status, count in statuses.items() if count)
        warnings.extend(str(item) for item in run.get("warnings", []))
    for source in priority_sources:
        source_states[source.id] = ["ok"]
    source_statuses = {
        source_id: _best_source_status(statuses)
        for source_id, statuses in sorted(source_states.items())
    }

    summary = {
        "run_type": "merged",
        "input_runs": [str(path.resolve()) for path, _ in entries],
        "output_dir": str(output_dir.resolve()),
        "source_count": len(source_statuses),
        "selected_sources": list(source_statuses),
        "source_statuses": {
            status: sum(value == status for value in source_statuses.values())
            for status in sorted(set(source_statuses.values()))
        },
        "source_status_by_id": source_statuses,
        "field_count": len(merged_facts),
        "fact_count": len(merged_facts),
        "facts_with_value": sum(item.get("value") is not None for item in merged_facts),
        "fact_statuses": _counts(merged_facts, "status"),
        "record_count": len(merged_records),
        "table_count": len(merged_tables),
        "network_payload_count": len(merged_network),
        "snapshot_count": len(merged_snapshots),
        "conflict_count": len(merged_conflicts),
        "hierarchy_node_count": hierarchy["stats"]["node_count"],
        "hierarchy_edge_count": hierarchy["stats"]["edge_count"],
        "hierarchy_unresolved_count": hierarchy["stats"]["unresolved_count"],
        "profile_stats": profile["stats"],
        "priority_pdf_paths": [str(path) for path in priority_paths],
        "priority_source_ids": [source.id for source in priority_sources],
        "warnings": sorted(set(warnings)),
    }
    (output_dir / "run.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return summary


def write_profile_assets(output_dir: Path, profile: dict[str, Any]) -> None:
    """Writes the browser-ready profile alongside profile.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(profile, ensure_ascii=False, separators=(",", ":"), default=str)
    (output_dir / "bmstu-profile-data.js").write_text(
        f"window.BMSTU_PROFILE = {payload};\n",
        encoding="utf-8",
    )


def _merge_jsonl(entries: list[tuple[Path, dict[str, Any]]], filename: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for run_dir, _ in entries:
        for item in _read_jsonl(run_dir / filename):
            item = dict(item)
            item["run_dir"] = str(run_dir.resolve())
            result.append(item)
    return result


def _merge_records(entries: list[tuple[Path, dict[str, Any]]], filename: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for run_dir, _ in entries:
        for item in _read_jsonl(run_dir / filename):
            key = json.dumps(
                {
                    "source_id": item.get("source_id"),
                    "record_type": item.get("record_type"),
                    "url": item.get("url") or item.get("document_url"),
                    "code": item.get("code") or item.get("program_code"),
                    "name": item.get("name") or item.get("title"),
                    "row_no": item.get("row_no"),
                    "applicant_id": item.get("applicant_id"),
                    "year": item.get("year") or item.get("academic_year"),
                    "program_profile_code": item.get("program_profile_code") or item.get("profile_code"),
                    "discipline": item.get("discipline") or item.get("subject"),
                    "course": item.get("course"),
                    "semester": item.get("semester"),
                    "hours": item.get("hours") or item.get("total_hours"),
                    "credits": item.get("credits") or item.get("zet"),
                    "assessment_type": item.get("assessment_type") or item.get("control"),
                    "subject_group": item.get("subject_group") or item.get("discipline_group"),
                },
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
            if key in seen:
                continue
            seen.add(key)
            item = dict(item)
            if item.get("record_type") == "ProgramProfile":
                # Profile disciplines were removed from the focused contract;
                # do not carry them forward from an older snapshot.
                item.pop("disciplines", None)
            item["run_dir"] = str(run_dir.resolve())
            result.append(item)
    return result


def _merge_facts(entries: list[tuple[Path, dict[str, Any]]]) -> list[dict[str, Any]]:
    by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
    followup_by_run = {
        str(run_dir.resolve()): int(run.get("followup_count", 0))
        for run_dir, run in entries
    }
    for run_dir, _ in entries:
        for item in _read_jsonl(run_dir / "facts.jsonl"):
            candidate = dict(item)
            candidate["run_dir"] = str(run_dir.resolve())
            by_field[str(item.get("field_id"))].append(candidate)

    result: list[dict[str, Any]] = []
    for field_id, candidates in sorted(by_field.items(), key=lambda pair: int(pair[0])):
        winner = max(candidates, key=lambda item: _fact_priority(item, followup_by_run))
        present = [item for item in candidates if item.get("value") is not None]
        merged = dict(winner)
        merged["source_ids"] = _unique(
            source_id for item in present for source_id in item.get("source_ids", [])
        ) or list(winner.get("source_ids", []))
        merged["source_urls"] = _unique(
            url for item in present for url in item.get("source_urls", [])
        ) or list(winner.get("source_urls", []))
        merged["source_runs"] = _unique(str(item.get("run_dir")) for item in present)
        merged["merge_candidates"] = [
            {
                "run_dir": item.get("run_dir"),
                "status": item.get("status"),
                "value": item.get("value"),
                "source_ids": item.get("source_ids", []),
            }
            for item in present
        ]
        result.append(merged)
    return result


def _fact_priority(item: dict[str, Any], followup_by_run: dict[str, int]) -> tuple[int, int, int, str]:
    status_priority = {
        "conflict": 5,
        "extracted": 4,
        "derived": 4,
        "reserve": 3,
        "source_unavailable": 2,
        "not_found": 1,
        "not_selected": 0,
        "unsupported": 0,
    }
    run_dir = str(item.get("run_dir", ""))
    return (
        int(item.get("value") is not None),
        status_priority.get(str(item.get("status")), 0),
        followup_by_run.get(run_dir, 0),
        run_dir,
    )


def _best_source_status(statuses: list[str]) -> str:
    priority = {"ok": 4, "empty": 2, "failed": 1}
    return max(statuses, key=lambda status: priority.get(status, 0), default="unknown")


def _snapshot_status(snapshot: dict[str, Any]) -> str:
    if snapshot.get("error"):
        return "failed"
    status_code = snapshot.get("status_code")
    if isinstance(status_code, int) and status_code >= 400:
        return "failed"
    if not snapshot.get("bytes"):
        return "empty"
    return "ok"


def _counts(items: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _unique(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    values: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            values.append(json.loads(line))
    return values


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for value in values:
            handle.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
