"""Contracts for candidate-spread-driven adaptive refinement."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel


class AdaptiveStatus(StrEnum):
    READY = "ready"
    SKIPPED = "skipped"


class AdaptiveDimension(ContractModel):
    code: str = Field(min_length=3, max_length=128)
    label: str = Field(min_length=1, max_length=256)
    kind: Literal["area", "activity"]
    spread: Decimal = Field(strict=True, ge=0, le=1)
    significance: Decimal = Field(strict=True, ge=0, le=1)


class AdaptiveSelection(ContractModel):
    status: AdaptiveStatus
    reason: str | None = Field(default=None, max_length=512)
    candidate_count: int = Field(strict=True, ge=0)
    top_candidate_count: int = Field(strict=True, ge=0)
    dimensions: tuple[AdaptiveDimension, ...] = Field(default=(), max_length=2)


__all__ = ["AdaptiveDimension", "AdaptiveSelection", "AdaptiveStatus"]
