from __future__ import annotations

import json
from pathlib import Path

from andromeda.infrastructure.jev.question_registry import QuestionRegistry
from evals.jev.exporters import build_jevcal_bundle


ROOT = Path(__file__).resolve().parents[2]


def _registry() -> QuestionRegistry:
    return QuestionRegistry.from_file(ROOT / "config" / "jev" / "question-definitions.v1.yaml")


def _rows() -> tuple[dict[str, object], ...]:
    path = ROOT / "evals" / "jev" / "corpus" / "decision-cases.v1.jsonl"
    return tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line)


def test_export_matches_upstream_jevcal_input_contract() -> None:
    bundle = build_jevcal_bundle(_registry(), _rows())

    assert set(bundle.questions) == {
        "intent.v1",
        "metric.v1",
        "next-action.v1",
        "presentation.v1",
        "semantic-feature.v1",
    }
    assert all(question["type"] == "choice" for question in bundle.questions.values())
    assert all("state" in row and "labels" in row for row in bundle.rows)
    assert all("thresholds" not in question for question in bundle.questions.values())


def test_export_is_rejected_for_duplicate_case_id() -> None:
    rows = _rows()
    duplicate = rows + (rows[0],)

    try:
        build_jevcal_bundle(_registry(), duplicate)
    except ValueError as exc:
        assert "duplicate case ID" in str(exc)
    else:  # pragma: no cover - assertion keeps the failure explicit
        raise AssertionError("duplicate case ID was accepted")
