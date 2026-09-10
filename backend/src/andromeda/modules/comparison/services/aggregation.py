from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal

from ..contracts.results import ComparisonBlock, ComparisonTotals
from ..domain.alignment import AlignedWorkload
from ..domain.entities import Workload


def totals(workloads: Iterable[Workload]) -> ComparisonTotals:
    values = tuple(workloads)
    return ComparisonTotals(
        hours=sum(value.hours for value in values),
        credits=sum((value.credits or Decimal("0") for value in values), Decimal("0")),
    )


def blocks(aligned: Iterable[AlignedWorkload]) -> tuple[ComparisonBlock, ...]:
    grouped: dict[str, list[AlignedWorkload]] = defaultdict(list)
    for entry in aligned:
        workload = entry.left or entry.right
        if workload is not None:
            grouped[workload.subject_group or "Без блока"].append(entry)
    result: list[ComparisonBlock] = []
    for name in sorted(grouped):
        entries = grouped[name]
        left_total = totals(entry.left for entry in entries if entry.left is not None)
        right_total = totals(entry.right for entry in entries if entry.right is not None)
        result.append(
            ComparisonBlock(
                name=name,
                totals_a=left_total,
                totals_b=right_total,
                hours_delta=left_total.hours - right_total.hours,
                credits_delta=left_total.credits - right_total.credits,
            )
        )
    return tuple(result)
