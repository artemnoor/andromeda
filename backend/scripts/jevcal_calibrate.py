"""Build and validate the immutable Jev calibration lock.

The script consumes labeled probability observations produced by an evaluation
tool. It does not invent probabilities and it never runs during a user query.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from andromeda.infrastructure.jev.question_registry import QuestionRegistry


LOCK_PATH = ROOT / "config" / "jev" / "locks" / "decisions.v1.lock.json"
SCHEMA_PATH = ROOT / "config" / "jev" / "schemas" / "decision-lock.schema.json"
OBSERVATIONS_PATH = ROOT / "evals" / "jev" / "corpus" / "calibration-observations.v1.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or validate a Jev calibration lock")
    parser.add_argument("--check", action="store_true", help="validate the committed lock only")
    parser.add_argument("--output", type=Path, default=LOCK_PATH)
    args = parser.parse_args(argv)
    if args.check:
        _validate_lock(args.output)
        print(json.dumps({"valid": True, "lock": str(args.output)}, indent=2))
        return 0
    lock = _build_lock()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _validate_lock(args.output)
    print(json.dumps(lock, ensure_ascii=False, indent=2))
    return 0


def _build_lock() -> dict[str, object]:
    registry = QuestionRegistry.from_file(ROOT / "config" / "jev" / "question-definitions.v1.yaml")
    observations = _read_observations()
    grouped: dict[str, list[dict[str, object]]] = {definition.definition_id: [] for definition in registry.all()}
    for observation in observations:
        definition_id = observation["definition_id"]
        if definition_id not in grouped:
            raise ValueError(f"unknown definition id: {definition_id}")
        probability = float(observation["probability"])
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError(f"invalid probability: {observation['case_id']}")
        grouped[definition_id].append(observation)

    definitions: dict[str, object] = {}
    for definition in registry.all():
        rows = grouped[definition.definition_id]
        heldout = [row for row in rows if row["split"] == "heldout"]
        if not heldout:
            raise ValueError(f"heldout observations are required: {definition.definition_id}")
        threshold = _select_threshold(heldout)
        accepted = [row for row in heldout if float(row["probability"]) >= threshold]
        accepted_accuracy = _accuracy(accepted)
        definitions[definition.definition_id] = {
            "definition_version": definition.version,
            "threshold": threshold,
            "coverage": len(accepted) / len(heldout),
            "heldout_count": len(heldout),
            "ece": _ece(heldout),
            "accepted_accuracy": accepted_accuracy,
        }

    dataset_hash = _hash_file(OBSERVATIONS_PATH)
    tool = json.loads((ROOT / "evals" / "jev" / "TOOLS.lock").read_text(encoding="utf-8"))["tools"]["jevcal"]
    body = {
        "schema_version": "decision-lock.v1",
        "status": "validated",
        "dataset_hash": dataset_hash,
        "tool": {"name": "jevcal", "commit": tool["commit"]},
        "model": {
            "provider": "deterministic-fixture",
            "model": "calibration-observations",
            "version": "calibration-observations.v1",
            "source": "shadow_only",
        },
        "definitions": definitions,
    }
    lock_id = "decision-lock-v1-" + hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()[:12]
    body["lock_id"] = lock_id
    body["generated_at"] = datetime.now(UTC).isoformat()
    return body


def _validate_lock(path: Path) -> None:
    if not path.exists():
        raise ValueError(f"calibration lock does not exist: {path}")
    lock = json.loads(path.read_text(encoding="utf-8"))
    try:
        from jsonschema import validate
    except ImportError:  # pragma: no cover - dev extra is present in CI
        required = {"schema_version", "lock_id", "status", "dataset_hash", "tool", "model", "definitions"}
        if not required.issubset(lock):
            raise ValueError("calibration lock is missing required fields")
    else:
        validate(lock, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    registry = QuestionRegistry.from_file(ROOT / "config" / "jev" / "question-definitions.v1.yaml")
    if set(lock["definitions"]) != {definition.definition_id for definition in registry.all()}:
        raise ValueError("calibration lock definitions do not match Question Registry")
    if lock["dataset_hash"] != _hash_file(OBSERVATIONS_PATH):
        raise ValueError("calibration lock dataset hash is stale")
    identity = {key: value for key, value in lock.items() if key not in {"lock_id", "generated_at"}}
    expected_lock_id = "decision-lock-v1-" + hashlib.sha256(_canonical(identity).encode("utf-8")).hexdigest()[:12]
    if lock["lock_id"] != expected_lock_id:
        raise ValueError("calibration lock identity is not reproducible")
    for definition in registry.all():
        metadata = lock["definitions"][definition.definition_id]
        if metadata["definition_version"] != definition.version:
            raise ValueError(f"calibration lock version is stale: {definition.definition_id}")
        if metadata["heldout_count"] < 1 or not math.isfinite(float(metadata["threshold"])):
            raise ValueError(f"calibration lock is unusable: {definition.definition_id}")


def _read_observations() -> list[dict[str, object]]:
    return [json.loads(line) for line in OBSERVATIONS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def _select_threshold(rows: list[dict[str, object]]) -> float:
    candidates = sorted({float(row["probability"]) for row in rows} | {1.0})
    valid = [threshold for threshold in candidates if _accuracy([row for row in rows if float(row["probability"]) >= threshold]) >= 0.8]
    return valid[0] if valid else 1.0


def _accuracy(rows: list[dict[str, object]]) -> float:
    return 0.0 if not rows else sum(bool(row["correct"]) for row in rows) / len(rows)


def _ece(rows: list[dict[str, object]]) -> float:
    if not rows:
        return 0.0
    buckets: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        bucket = min(9, int(float(row["probability"]) * 10))
        buckets.setdefault(bucket, []).append(row)
    return sum(
        len(bucket_rows)
        / len(rows)
        * abs(
            sum(float(row["probability"]) for row in bucket_rows) / len(bucket_rows)
            - _accuracy(bucket_rows)
        )
        for bucket_rows in buckets.values()
    )


def _hash_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    raise SystemExit(main())
