"""Application result for the generic assistant transport seam."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from andromeda.modules.admission_fit.contracts.public import (
    BatchAdmissionFitRequest,
    BatchAdmissionFitResult,
)
from andromeda.modules.analytics.contracts.query import QuerySpec
from andromeda.modules.presentation.contracts.envelope import ResponseEnvelope
from andromeda.shared.contracts.base import ContractModel

from .public import ConversationSlot, QuerySessionId


class AssistantState(StrEnum):
    NEEDS_CLARIFICATION = "needs_clarification"
    COMPLETE = "complete"
    AMBIGUOUS = "ambiguous"


class AssistantResult(ContractModel):
    state: AssistantState
    session_id: QuerySessionId
    revision: int = Field(strict=True, ge=1)
    question: str | None = Field(default=None, max_length=512)
    options: tuple[str, ...] = Field(default=(), max_length=20)
    missing_slots: tuple[ConversationSlot, ...] = Field(default=(), max_length=8)
    response: ResponseEnvelope | None = None
    query: QuerySpec | None = None
    admission_request: BatchAdmissionFitRequest | None = None
    admission_requests: tuple[BatchAdmissionFitRequest, ...] = Field(default=(), max_length=100)
    admission_result: BatchAdmissionFitResult | None = None


__all__ = ["AssistantResult", "AssistantState"]
