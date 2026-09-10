"""Shared scalar constraints used by every tracer boundary."""

from decimal import Decimal
from typing import Annotated, TypeAlias

from pydantic import Field, HttpUrl, StringConstraints, TypeAdapter

NonEmptyText: TypeAlias = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=512),
]
ShortText: TypeAlias = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=256),
]
UniversityId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^university:[a-z0-9][a-z0-9-]{0,62}$"),
]
DirectionId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^direction:[0-9]{2}\.[0-9]{2}\.[0-9]{2}$"),
]
ProgramId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^program:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}$"),
]
CurriculumItemId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^curriculum-item:program:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}:discipline:[a-f0-9]{16}:(?:unassigned|[1-9]|1[0-2])$"),
]
CurriculumId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^curriculum:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}-20[0-9]{2}$"),
]
DisciplineId: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^discipline:[a-f0-9]{16}$"),
]
DirectionCode: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{2}\.[0-9]{2}\.[0-9]{2}$"),
]
ProgramCode: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}$"),
]
Sha256: TypeAlias = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
Credits: TypeAlias = Annotated[Decimal, Field(strict=True, ge=0, le=60, decimal_places=2)]
EducationYear: TypeAlias = Annotated[int, Field(strict=True, ge=2000, le=2100)]
Semester: TypeAlias = Annotated[int, Field(strict=True, ge=1, le=12)]
HourCount: TypeAlias = Annotated[int, Field(strict=True, ge=0, le=2_000)]
SourcePosition: TypeAlias = Annotated[int, Field(strict=True, ge=1, le=10_000)]

HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


def http_url(value: str) -> HttpUrl:
    return HTTP_URL_ADAPTER.validate_python(value)

MIN_YEAR = 2000
MAX_YEAR = 2100
MIN_SEMESTER = 1
MAX_SEMESTER = 12
MAX_HOURS = 2_000
MAX_POSITION = 10_000
