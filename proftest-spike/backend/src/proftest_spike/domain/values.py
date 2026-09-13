"""Small numeric helpers shared by Spike domain modules."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


ZERO = Decimal("0")
ONE = Decimal("1")


def quantize_ratio(value: Decimal) -> Decimal:
    """Keep ratios stable and human-safe without introducing float drift."""

    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def clamp(value: Decimal, lower: Decimal = ZERO, upper: Decimal = ONE) -> Decimal:
    """Clamp a Decimal to an inclusive interval."""

    return max(lower, min(upper, value))


__all__ = ["ONE", "ZERO", "clamp", "quantize_ratio"]
