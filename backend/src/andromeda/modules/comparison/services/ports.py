from __future__ import annotations

from typing import Protocol

from ..contracts.public import ComparisonRequest, ComparisonResult, ComparisonSummaryRequest, ComparisonSummaryResult


class ComparisonService(Protocol):
    def compare(self, request: ComparisonRequest) -> ComparisonResult: ...


class ComparisonSummaryServicePort(Protocol):
    def summarize(self, request: ComparisonSummaryRequest) -> ComparisonSummaryResult: ...


__all__ = ["ComparisonService", "ComparisonSummaryServicePort"]
