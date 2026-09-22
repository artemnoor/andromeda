"""Orchestrate upstream jevcal calibration without reimplementing its logic."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from andromeda.infrastructure.jev.question_registry import QuestionRegistry
from evals.jev.exporters import build_jevcal_bundle


logger = logging.getLogger("andromeda.scripts.jevcal_calibrate")
LOCK_PATH = ROOT / "config" / "jev" / "locks" / "decisions.v1.lock.json"
MANIFEST_PATH = LOCK_PATH.with_suffix(LOCK_PATH.suffix + ".meta.json")
OBSERVATIONS_PATH = ROOT / "evals" / "jev" / "corpus" / "calibration-observations.v1.jsonl"
CORPUS_PATH = ROOT / "evals" / "jev" / "corpus" / "decision-cases.v1.jsonl"
REGISTRY_PATH = ROOT / "config" / "jev" / "question-definitions.v1.yaml"
TARGET_ACCURACY = 0.8
HOLDOUT = 0.5
SEED = 7
MIN_SUPPORT = 30


class CalibrationArtifactError(ValueError):
    """Raised when an upstream artifact or its Andromeda metadata is invalid."""


@dataclass(frozen=True, slots=True)
class CalibrationInputs:
    lock: dict[str, object]
    manifest: dict[str, object]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate an existing upstream lock")
    parser.add_argument("--source", choices=("fixture", "production"), default="fixture")
    parser.add_argument("--output", type=Path, default=LOCK_PATH)
    parser.add_argument("--manifest-output", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--min-support", type=int, default=MIN_SUPPORT)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    if args.min_support < 1:
        raise SystemExit("--min-support must be positive")
    if args.check:
        _validate_lock(args.output, args.manifest_output)
        print(json.dumps({"valid": True, "lock": str(args.output)}, indent=2))
        return 0
    if args.source == "production":
        raise SystemExit("production calibration requires an externally supplied labeled corpus")

    lock = _build_lock(min_support=args.min_support)
    manifest = _build_manifest(lock, source_kind=args.source, min_support=args.min_support)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.manifest_output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _validate_lock(args.output, args.manifest_output)
    question_count = len(lock["questions"]) if isinstance(lock.get("questions"), dict) else 0
    logger.info(
        "jevcal_upstream_artifact_written lock=%s manifest=%s definitions=%s source_kind=%s",
        args.output,
        args.manifest_output,
        question_count,
        args.source,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def _build_lock(*, min_support: int = MIN_SUPPORT) -> dict[str, object]:
    """Build a lock through upstream jevcal's public compile/build_lock API."""

    try:
        from jevcal.compile import build_lock, compile_question
        from jevcal.metrics import Record, confidence_measures
        from jevcal.spec import load_questions, load_rows
    except ImportError as exc:  # pragma: no cover - optional extra guard
        raise CalibrationArtifactError("install the evaluation extra for upstream jevcal") from exc

    registry = QuestionRegistry.from_file(REGISTRY_PATH)
    source_rows = _read_jsonl(OBSERVATIONS_PATH)
    decision_rows = _read_jsonl(CORPUS_PATH)
    bundle = build_jevcal_bundle(registry, tuple(decision_rows))
    with tempfile.TemporaryDirectory(prefix="andromeda-jevcal-") as directory:
        directory_path = Path(directory)
        questions_path = directory_path / "questions.yaml"
        data_path = directory_path / "data.jsonl"
        questions_path.write_text(
            _questions_yaml(bundle.questions), encoding="utf-8"
        )
        data_path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in bundle.rows),
            encoding="utf-8",
        )
        questions = load_questions(questions_path)
        rows = load_rows(data_path)

        observations_by_question: dict[str, list[dict[str, object]]] = {}
        for row in source_rows:
            definition_id = _required_string(row, "definition_id")
            observations_by_question.setdefault(definition_id, []).append(row)

        results: dict[str, dict[str, object]] = {}
        for question_id, question in questions.questions.items():
            question_observations = observations_by_question.get(question_id, [])
            if not any(row.get("split") == "heldout" for row in question_observations):
                raise CalibrationArtifactError(f"heldout observations are required: {question_id}")
            records = []
            for observation in question_observations:
                probability = _probability(observation)
                correct = bool(observation.get("correct"))
                labels = question.options()
                if len(labels) < 2:
                    raise CalibrationArtifactError(f"upstream question has fewer than two options: {question_id}")
                probabilities = {labels[0]: probability, labels[1]: 1.0 - probability}
                measures = confidence_measures(probabilities, probability)
                records.append(
                    Record(
                        row_id=_required_string(observation, "case_id"),
                        qid=question_id,
                        gold=labels[0],
                        pred=labels[0] if correct else labels[1],
                        correct=correct,
                        probabilities=probabilities,
                        gold_key=labels[0],
                        measures=measures,
                    )
                )
            if not records:
                raise CalibrationArtifactError(f"no observations for {question_id}")
            results[question_id] = compile_question(
                records,
                target=TARGET_ACCURACY,
                measure="top_prob",
                holdout=HOLDOUT,
                seed=SEED,
                min_support=min_support,
            )

        lock = build_lock(
            questions,
            rows,
            results,
            {"models": ["calibration-observations.v1"]},
            None,
            holdout=HOLDOUT,
            seed=SEED,
            provider="deterministic-fixture",
        )
    if not isinstance(lock, dict) or "questions" not in lock:
        raise CalibrationArtifactError("upstream jevcal returned an invalid lock")
    return lock


def _build_manifest(lock: dict[str, object], *, source_kind: str, min_support: int) -> dict[str, object]:
    registry = QuestionRegistry.from_file(REGISTRY_PATH)
    tool = json.loads((ROOT / "evals" / "jev" / "TOOLS.lock").read_text(encoding="utf-8"))["tools"]["jevcal"]
    dataset_hash = str(lock.get("dataset_sha", ""))
    lock_hash = _hash_value(lock)
    return {
        "schema_version": "andromeda-jevcal-manifest.v1",
        "artifact_id": "jevcal-lock-" + lock_hash.split(":", 1)[1][:12],
        "source_kind": source_kind,
        "status": "fixture_only" if source_kind == "fixture" else "production_ready",
        "registry_hash": registry.content_hash(),
        "dataset_hash": dataset_hash,
        "observations_hash": _hash_file(OBSERVATIONS_PATH),
        "lock_hash": lock_hash,
        "upstream": {
            "name": "jevcal",
            "commit": tool["commit"],
            "version": lock.get("jevcal_version"),
        },
        "model_requested": lock.get("model_requested"),
        "model_observed": lock.get("model_observed"),
        "min_support": min_support,
        "samples_by_definition": _sample_counts(),
        "definition_versions": {
            definition.definition_id: definition.version for definition in registry.all()
        },
    }


def _validate_lock(lock_path: Path, manifest_path: Path = MANIFEST_PATH) -> CalibrationInputs:
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CalibrationArtifactError("calibration artifact or manifest is invalid") from exc
    if not isinstance(lock, dict) or not isinstance(manifest, dict):
        raise CalibrationArtifactError("calibration artifact and manifest must be objects")
    required_lock = {"jevcal_version", "questions", "questions_sha", "dataset_sha", "model_requested"}
    if not required_lock.issubset(lock):
        raise CalibrationArtifactError("upstream lock is missing required fields")
    if manifest.get("lock_hash") != _hash_value(lock):
        raise CalibrationArtifactError("calibration manifest lock hash is stale")
    if manifest.get("dataset_hash") != lock.get("dataset_sha"):
        raise CalibrationArtifactError("calibration manifest dataset hash is stale")
    if manifest.get("observations_hash") != _hash_file(OBSERVATIONS_PATH):
        raise CalibrationArtifactError("calibration observations hash is stale")
    registry = QuestionRegistry.from_file(REGISTRY_PATH)
    question_ids = set(lock["questions"]) if isinstance(lock["questions"], dict) else set()
    expected_ids = {definition.definition_id for definition in registry.all()}
    if question_ids != expected_ids:
        raise CalibrationArtifactError("upstream lock questions do not match Question Registry")
    if manifest.get("registry_hash") != registry.content_hash():
        raise CalibrationArtifactError("calibration manifest registry hash is stale")
    logger.info(
        "jevcal_upstream_artifact_validated lock=%s manifest=%s questions=%s status=%s",
        lock_path,
        manifest_path,
        len(question_ids),
        manifest.get("status"),
    )
    return CalibrationInputs(lock=lock, manifest=manifest)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise CalibrationArtifactError("calibration observation must be an object")
            rows.append(value)
    return rows


def _questions_yaml(questions: dict[str, dict[str, object]]) -> str:
    import yaml

    return yaml.safe_dump({"model": "jev-latest", "questions": questions}, allow_unicode=True, sort_keys=False)


def _required_string(row: dict[str, object], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise CalibrationArtifactError(f"missing string field {key}")
    return value


def _probability(row: dict[str, object]) -> float:
    value = row.get("probability")
    if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
        raise CalibrationArtifactError(f"invalid probability: {row.get('case_id')}")
    return float(value)


def _hash_file(path: Path) -> str:
    # Git may check this JSONL text file out with CRLF on Windows. Normalize
    # record separators so the same calibration corpus keeps the same hash
    # across supported operating systems.
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _hash_value(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sample_counts() -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in _read_jsonl(OBSERVATIONS_PATH):
        definition_id = _required_string(row, "definition_id")
        entry = counts.setdefault(definition_id, {"total": 0, "heldout": 0})
        entry["total"] += 1
        if row.get("split") == "heldout":
            entry["heldout"] += 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
