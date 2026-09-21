from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import jevcal_calibrate, jevcal_export


def test_committed_calibration_lock_is_reproducible() -> None:
    jevcal_calibrate._validate_lock(jevcal_calibrate.LOCK_PATH)
    lock = json.loads(jevcal_calibrate.LOCK_PATH.read_text(encoding="utf-8"))
    assert lock["status"] == "validated"
    assert lock["model"]["source"] == "shadow_only"
    assert all(value["heldout_count"] > 0 for value in lock["definitions"].values())


def test_calibration_generation_rejects_missing_heldout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    observations = tmp_path / "observations.jsonl"
    observations.write_text(
        json.dumps(
            {
                "case_id": "intent-train-001",
                "definition_id": "intent.v1",
                "split": "train",
                "probability": 0.9,
                "correct": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(jevcal_calibrate, "OBSERVATIONS_PATH", observations)

    with pytest.raises(ValueError, match="heldout observations"):
        jevcal_calibrate._build_lock()


def test_export_hash_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "one.jsonl"
    second = tmp_path / "two.jsonl"
    assert jevcal_export.main(["--output", str(first)]) == 0
    assert jevcal_export.main(["--output", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
    first_meta = json.loads(first.with_suffix(".jsonl.meta.json").read_text(encoding="utf-8"))
    second_meta = json.loads(second.with_suffix(".jsonl.meta.json").read_text(encoding="utf-8"))
    assert first_meta["dataset_hash"] == second_meta["dataset_hash"]
