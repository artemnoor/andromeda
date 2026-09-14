from __future__ import annotations

from decimal import Decimal
from typing import Annotated, TypeAlias

from pydantic import Field, StringConstraints

NonEmptyText: TypeAlias = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]
ShortText: TypeAlias = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
UniversityId: TypeAlias = Annotated[str, StringConstraints(pattern=r"^university:[a-z0-9][a-z0-9-]{0,62}$")]
DirectionId: TypeAlias = Annotated[str, StringConstraints(pattern=r"^direction:[0-9]{2}\.[0-9]{2}\.[0-9]{2}$")]
DirectionCode: TypeAlias = Annotated[str, StringConstraints(pattern=r"^[0-9]{2}\.[0-9]{2}\.[0-9]{2}$")]
ProgramId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^program:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}$"),
]
ProgramCode: TypeAlias = Annotated[str, StringConstraints(pattern=r"^[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}$")]
DepartmentId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^department:[a-z0-9][a-z0-9-]{0,62}:[a-z0-9][a-z0-9-]{0,62}$"),
]
EventId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^event:[a-z0-9][a-z0-9-]{0,62}:[a-z0-9][a-z0-9-]{0,127}$"),
]
VenueId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^venue:[a-z0-9][a-z0-9-]{0,62}:[a-z0-9][a-z0-9-]{0,62}$"),
]
CurriculumId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^curriculum:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}-20[0-9]{2}$"),
]
CurriculumItemId: TypeAlias = Annotated[
    str,
    StringConstraints(
        pattern=r"^curriculum-item:program:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}:discipline:[a-f0-9]{16}:(?:unassigned|[1-9]|1[0-2])$"
    ),
]
DisciplineId: TypeAlias = Annotated[str, StringConstraints(pattern=r"^discipline:[a-f0-9]{16}$")]
SourcePosition: TypeAlias = Annotated[int, Field(strict=True, ge=1, le=10_000)]
SourceHash: TypeAlias = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
IngestRunId: TypeAlias = Annotated[str, StringConstraints(pattern=r"^ingest:[a-f0-9]{32}$")]
EducationYear: TypeAlias = Annotated[int, Field(strict=True, ge=2000, le=2100)]
Semester: TypeAlias = Annotated[int, Field(strict=True, ge=1, le=12)]
HourCount: TypeAlias = Annotated[int, Field(strict=True, ge=0, le=2000)]
Credits: TypeAlias = Annotated[Decimal, Field(strict=True, ge=Decimal("0"), le=Decimal("60"), max_digits=6, decimal_places=2)]
