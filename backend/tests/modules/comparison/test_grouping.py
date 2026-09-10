from __future__ import annotations

from decimal import Decimal

from andromeda.modules.comparison.domain.alignment import AlignedWorkload
from andromeda.modules.comparison.domain.entities import Workload
from andromeda.modules.comparison.services.aggregation import blocks, totals
from andromeda.shared.contracts.enums import CompareStatus


def test_aggregation_returns_decimal_totals_per_subject_block() -> None:
    left = Workload(hours=12, credits=Decimal("1.50"), subject_group="Базовая часть")
    right = Workload(hours=10, credits=Decimal("1.00"), subject_group="Базовая часть")
    aligned = (AlignedWorkload(("math", 1), left, right, CompareStatus.DIFFERENT),)
    result = blocks(aligned)
    assert result[0].name == "Базовая часть"
    assert result[0].hours_delta == 2
    assert result[0].credits_delta == Decimal("0.50")
    assert totals((left,)).credits == Decimal("1.50")
