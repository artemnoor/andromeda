"""Compatibility import surface for shared contract primitives.

The aliases remain defined once in ``constraints.py``; this module only gives
future domain extensions a stable primitives namespace.
"""

from .constraints import (
    Credits,
    CurriculumId,
    CurriculumItemId,
    DirectionCode,
    DirectionId,
    DisciplineId,
    EducationYear,
    HourCount,
    NonEmptyText,
    ProgramCode,
    ProgramId,
    Sha256,
    Semester,
    SourcePosition,
    ShortText,
    UniversityId,
    http_url,
)

__all__ = [
    "Credits",
    "CurriculumId",
    "CurriculumItemId",
    "DirectionCode",
    "DirectionId",
    "DisciplineId",
    "EducationYear",
    "HourCount",
    "NonEmptyText",
    "ProgramCode",
    "ProgramId",
    "Sha256",
    "Semester",
    "SourcePosition",
    "ShortText",
    "UniversityId",
    "http_url",
]
