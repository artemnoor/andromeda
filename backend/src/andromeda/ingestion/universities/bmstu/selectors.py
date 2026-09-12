from __future__ import annotations

from pathlib import Path

TARGET_DIRECTION_CODE = "09.03.01"
TARGET_PROGRAM_CODES = ("09.03.01-02", "09.03.01-12")
DEFAULT_FIXTURE_DIR = Path(__file__).resolve().parents[5] / "tests" / "fixtures" / "tracer" / "raw"
DEFAULT_EVENT_FIXTURE_DIR = Path(__file__).resolve().parents[5] / "tests" / "fixtures" / "events" / "raw"


def select_program_codes(values: tuple[str, ...] | None = None) -> tuple[str, ...]:
    selected = values or TARGET_PROGRAM_CODES
    result = tuple(value.strip().removeprefix("program:") for value in selected)
    if not result or len(result) != len(set(result)) or any(not value for value in result):
        raise ValueError("program codes must be non-empty and unique")
    return result
