"""Policy seams for future Jev adapters."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import Field

from andromeda.modules.analytics.contracts.results import AnalyticsResult
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.versions import DECISION_POLICY_VERSION

from .public import QuerySession


class DecisionAction(StrEnum):
    ASK_CLARIFICATION = "ask_clarification"
    EXECUTE_QUERY = "execute_query"
    SHOW_RESULT = "show_result"
    COMPARE = "compare"
    BUILD_REPORT = "build_report"
    OPEN_MINI_APP = "open_mini_app"


class DataCapabilities(ContractModel):
    metrics: tuple[str, ...] = Field(default=(), max_length=100)
    has_materialized_projections: bool = True
    supports_admission_fit: bool = True
    supports_evidence: bool = True


class DecisionPolicyResult(ContractModel):
    action: DecisionAction
    question: str | None = Field(default=None, max_length=512)
    options: tuple[str, ...] = Field(default=(), max_length=20)
    reason: str = Field(min_length=1, max_length=512)
    policy_version: str = DECISION_POLICY_VERSION


class DecisionPolicyPort(Protocol):
    def decide(
        self,
        session: QuerySession,
        *,
        available_actions: tuple[DecisionAction, ...] = tuple(DecisionAction),
        capabilities: DataCapabilities | None = None,
        last_result: AnalyticsResult | None = None,
    ) -> DecisionPolicyResult: ...


__all__ = [
    "DataCapabilities",
    "DecisionAction",
    "DecisionPolicyPort",
    "DecisionPolicyResult",
]
