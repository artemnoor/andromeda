from __future__ import annotations

from typing import Annotated, Self

from fastapi import Query
from fastapi.exceptions import RequestValidationError
from pydantic import Field, StringConstraints, TypeAdapter, ValidationError, model_validator

from andromeda.modules.comparison.contracts.public import ComparisonRequest, ComparisonResult
from andromeda.shared.contracts.enums import ComparisonScope
from andromeda.shared.contracts.ids import ProgramId, Semester

from .common import ApiModel, ComparisonResponse
from .disciplines import area_summary_response, discipline_response


ProgramIdsQuery = Annotated[str, StringConstraints(min_length=1, max_length=512)]


class CompareQuery(ApiModel):
    program_ids: ProgramIdsQuery = Field(alias="programIds")
    scope: ComparisonScope = ComparisonScope.ALL
    semester: int | None = Field(default=None, ge=1, le=12)

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        self.to_request()
        return self

    def to_request(self) -> ComparisonRequest:
        parts = tuple(part.strip() for part in self.program_ids.split(","))
        if len(parts) != 2 or parts[0] == parts[1]:
            raise ValueError("programIds must contain exactly two distinct program ids")
        adapter = TypeAdapter(ProgramId)
        left, right = adapter.validate_python(parts[0]), adapter.validate_python(parts[1])
        return ComparisonRequest(program_a_id=left, program_b_id=right, scope=self.scope, semester=self.semester)


def parse_compare_query(
    program_ids: ProgramIdsQuery = Query(..., alias="programIds"),
    scope: ComparisonScope = Query(ComparisonScope.ALL),
    semester: int | None = Query(default=None, ge=1, le=12),
) -> CompareQuery:
    try:
        return CompareQuery(programIds=program_ids, scope=scope, semester=semester)
    except ValidationError as exc:
        errors = [{**error, "loc": ("query", *error.get("loc", ()))} for error in exc.errors()]
        raise RequestValidationError(errors) from exc


def comparison_response(result: ComparisonResult) -> ComparisonResponse:
    return ComparisonResponse.model_validate(
        {
            "program_a": result.program_a.model_dump(),
            "program_b": result.program_b.model_dump(),
            "scope": result.scope,
            "semester": result.semester,
            "rows": tuple(
                {
                    **row.model_dump(),
                    "discipline": discipline_response(row.discipline),
                }
                for row in result.rows
            ),
            "totals_a": result.totals_a.model_dump(),
            "totals_b": result.totals_b.model_dump(),
            "area_breakdown_a": tuple(area_summary_response(item.area, item.share) for item in result.area_breakdown_a),
            "area_breakdown_b": tuple(area_summary_response(item.area, item.share) for item in result.area_breakdown_b),
        }
    )
