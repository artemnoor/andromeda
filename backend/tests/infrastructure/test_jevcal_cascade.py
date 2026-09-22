from __future__ import annotations

from pathlib import Path

import pytest

from andromeda.infrastructure.jev.calibration import (
    CalibrationArtifactError,
    CascadeCalibrationAdapter,
)
from andromeda.infrastructure.jev.contracts import JevAnswerEvidence
from andromeda.infrastructure.jev.question_registry import QuestionRegistry


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = QuestionRegistry.from_file(ROOT / "config/jev/question-definitions.v1.yaml")
LOCK = ROOT / "config/jev/locks/decisions.v1.lock.json"
MANIFEST = ROOT / "config/jev/locks/decisions.v1.lock.json.meta.json"


def test_adapter_delegates_acceptance_to_upstream_cascade() -> None:
    adapter = CascadeCalibrationAdapter(
        lock_path=LOCK,
        manifest_path=MANIFEST,
        registry=REGISTRY,
        model="jev-latest",
    )
    result = adapter.evaluate(
        "intent.v1",
        JevAnswerEvidence(
            answer_kind="ChoiceAnswer",
            answer_value="catalog_search",
            confidence=0.99,
            probabilities={"catalog_search": 0.99, "unknown": 0.01},
            has_probability_evidence=True,
        ),
    )

    assert result.accepted is False
    assert result.reason == "calibration_rejected"
    assert result.threshold is None


def test_production_adapter_rejects_fixture_artifact() -> None:
    with pytest.raises(CalibrationArtifactError, match="not production-ready"):
        CascadeCalibrationAdapter(
            lock_path=LOCK,
            manifest_path=MANIFEST,
            registry=REGISTRY,
            model="jev-latest",
            production=True,
        )


def test_production_adapter_rejects_insufficient_support(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    data = __import__("json").loads(MANIFEST.read_text(encoding="utf-8"))
    data["status"] = "production_ready"
    manifest.write_text(__import__("json").dumps(data), encoding="utf-8")
    with pytest.raises(CalibrationArtifactError, match="support is insufficient"):
        CascadeCalibrationAdapter(
            lock_path=LOCK,
            manifest_path=manifest,
            registry=REGISTRY,
            model="jev-latest",
            production=True,
        )
