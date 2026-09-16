from __future__ import annotations

from pathlib import Path


def test_spike_read_contract_lists_current_andromeda_fields_without_importing_main_backend() -> None:
    source_root = Path(__file__).resolve().parents[2] / "proftest-spike" / "backend" / "src" / "proftest_spike"
    contract_source = source_root / "api_client" / "contracts.py"
    text = contract_source.read_text(encoding="utf-8")
    for field in ("source_name", "semester", "hours", "credits", "assessment_types", "subject_group", "area_weights"):
        assert field in text
    assert "andromeda.infrastructure" not in text
