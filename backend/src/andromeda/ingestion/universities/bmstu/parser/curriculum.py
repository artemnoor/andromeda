from __future__ import annotations

from ....contracts.raw import RawCurriculumRow


def validate_curriculum_rows(rows: tuple[RawCurriculumRow, ...]) -> tuple[RawCurriculumRow, ...]:
    if not rows:
        raise ValueError("curriculum must contain at least one row")
    return rows
