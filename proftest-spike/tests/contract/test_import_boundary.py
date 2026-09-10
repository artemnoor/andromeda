from __future__ import annotations

from pathlib import Path


def test_spike_production_does_not_import_storage_or_main_infrastructure() -> None:
    source_root = Path(__file__).resolve().parents[2] / "backend" / "src" / "proftest_spike"
    forbidden = ("import sqlite3", "from sqlalchemy", "import sqlalchemy", "andromeda.infrastructure", "bmstu_parser.db")
    for source_file in source_root.rglob("*.py"):
        text = source_file.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), source_file
