"""Export sanitized, versioned decision examples for jevcal."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from andromeda.infrastructure.jev.question_registry import QuestionRegistry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export typed Jev calibration examples")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    registry = QuestionRegistry.from_file(ROOT / "config" / "jev" / "question-definitions.v1.yaml")
    rows = _load_rows(ROOT / "evals" / "jev" / "corpus" / "decision-cases.v1.jsonl", registry)
    serialized = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8")
    metadata = {
        "schema_version": "jevcal-export.v1",
        "tool": json.loads((ROOT / "evals" / "jev" / "TOOLS.lock").read_text(encoding="utf-8"))["tools"]["jevcal"],
        "definitions": sorted({row["definition_id"] for row in rows}),
        "splits": sorted({row["split"] for row in rows}),
        "case_count": len(rows),
        "dataset_hash": "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
    }
    args.output.with_suffix(args.output.suffix + ".meta.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


def _load_rows(path: Path, registry: QuestionRegistry) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        definition = registry.get(row["definition_id"])
        if row["definition_version"] != definition.version:
            raise ValueError(f"definition version mismatch: {row['case_id']}")
        rows.append(
            {
                "case_id": row["case_id"],
                "definition_id": definition.definition_id,
                "definition_version": definition.version,
                "split": row["split"],
                "input": row["input"],
                "expected": row["expected"],
            }
        )
    return tuple(rows)


if __name__ == "__main__":
    raise SystemExit(main())
