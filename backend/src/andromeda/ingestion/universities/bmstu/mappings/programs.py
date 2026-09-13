from __future__ import annotations

from ..selectors import select_program_codes


def target_program_codes(values: tuple[str, ...] | None = None) -> tuple[str, ...]:
    return select_program_codes(values)
