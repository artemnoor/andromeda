from __future__ import annotations

"""Rebuild a browser profile with a fresh, direct-text priority PDF parse."""

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from bmstu_parser.hierarchy import build_hierarchy
from bmstu_parser.priority_pdf import parse_priority_pdf, priority_source_definition
from bmstu_parser.profile import build_profile
from bmstu_parser.report import write_profile_assets


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(value, ensure_ascii=False, default=str) + "\n" for value in values),
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: rebuild_direct_priority_profile.py INPUT_RUN OUTPUT_RUN PRIORITY_PDF")
    input_dir, output_dir, pdf_path = map(Path, sys.argv[1:])
    if output_dir.exists():
        raise SystemExit(f"output already exists: {output_dir}")
    shutil.copytree(input_dir, output_dir)

    records = _read_jsonl(input_dir / "records.jsonl")
    records = [record for record in records if record.get("source_id") != "P01_BS_PDF"]
    extraction = parse_priority_pdf(pdf_path)
    records.extend(extraction.records)

    source_map_path = output_dir / "source_map.json"
    source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"] = [
        source for source in source_map.get("sources", []) if source.get("id") != "P01_BS_PDF"
    ]
    source_map["sources"].append(priority_source_definition(pdf_path).to_dict())
    source_map_path.write_text(json.dumps(source_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    hierarchy = build_hierarchy(records, source_map["sources"])
    profile = build_profile(records, [], hierarchy)
    _write_jsonl(output_dir / "records.jsonl", records)
    (output_dir / "hierarchy.json").write_text(json.dumps(hierarchy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_profile_assets(output_dir, profile)

    run_path = output_dir / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run.update({
        "run_type": "rebuild-direct-pdf-text",
        "record_count": len(records),
        "hierarchy_node_count": hierarchy["stats"]["node_count"],
        "hierarchy_edge_count": hierarchy["stats"]["edge_count"],
        "hierarchy_unresolved_count": hierarchy["stats"]["unresolved_count"],
        "profile_stats": profile["stats"],
        "priority_pdf_paths": [str(pdf_path.resolve())],
        "priority_source_ids": ["P01_BS_PDF"],
        "warnings": sorted(set(run.get("warnings", [])) | set(extraction.warnings)),
    })
    run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir.resolve()), "profile_stats": profile["stats"], "pdf_warnings": extraction.warnings}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
