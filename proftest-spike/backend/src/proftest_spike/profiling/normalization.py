"""Deterministic Decimal normalization for profile axes."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import TypeVar

from proftest_spike.domain.values import ZERO, quantize_ratio

KeyT = TypeVar("KeyT")


def normalize_weights(values: Mapping[KeyT, Decimal]) -> dict[KeyT, Decimal]:
    positive = [(key, value) for key, value in values.items() if value > ZERO]
    if not positive:
        return {}
    positive.sort(key=lambda entry: str(entry[0]))
    total = sum((value for _, value in positive), ZERO)
    result = {key: quantize_ratio(value / total) for key, value in positive}
    result[positive[-1][0]] += Decimal("1") - sum(result.values(), ZERO)
    return result


__all__ = ["normalize_weights"]
