from __future__ import annotations

from collections.abc import Sequence

from ..selectors import select_program_codes


def select_catalog_programs(values: Sequence[str]) -> tuple[str, ...]:
    return select_program_codes(tuple(values))
