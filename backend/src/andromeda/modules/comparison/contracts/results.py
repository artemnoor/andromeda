from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.disciplines.contracts.public import DisciplineAreaSummary
from andromeda.modules.programs.contracts.public import Program
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.enums import CompareStatus, ComparisonScope
from andromeda.shared.contracts.ids import Semester
from ..domain.entities import Workload


class ComparisonRow(ContractModel):
    discipline: Discipline
    semester: Semester | None = None
    a: Workload | None = None
    b: Workload | None = None
    status: CompareStatus
    hours_delta: int | None = None
    credits_delta: Decimal | None = None


class ComparisonTotals(ContractModel):
    hours: int = Field(strict=True, ge=0, le=100_000)
    credits: Decimal = Field(strict=True, ge=Decimal("0"), max_digits=10, decimal_places=2)


class ComparisonResult(ContractModel):
    program_a: Program
    program_b: Program
    scope: ComparisonScope
    semester: Semester | None = None
    rows: tuple[ComparisonRow, ...]
    totals_a: ComparisonTotals
    totals_b: ComparisonTotals
    area_breakdown_a: tuple[DisciplineAreaSummary, ...] = ()
    area_breakdown_b: tuple[DisciplineAreaSummary, ...] = ()


__all__ = ["ComparisonResult", "ComparisonRow", "ComparisonTotals"]
