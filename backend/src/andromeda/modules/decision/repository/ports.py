"""Typed persistence ports for the decision context."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Protocol

from andromeda.modules.proftest.contracts.public import ProfileScope
from andromeda.modules.proftest.contracts.public import ProgramFingerprint
from andromeda.modules.programs.contracts.public import Program
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import AccountId

from ..contracts.analytics import DecisionAnalyticsEvent
from ..domain.entities import DecisionSnapshot, DecisionState
from ..domain.values import DecisionId


class DecisionBindingOutcome(StrEnum):
    """Result of binding anonymous decision state during account registration."""

    BOUND = "bound"
    ACCOUNT_STATE_KEPT = "account_state_kept"
    NO_ANONYMOUS_STATE = "no_anonymous_state"


class DecisionBindingPort(Protocol):
    """Transfer an anonymous owner without merging two explicit choices."""

    def bind_anonymous_to_account(self, scope: ProfileScope, account_id: AccountId) -> DecisionBindingOutcome: ...


class DecisionContextRepository(DecisionBindingPort, Protocol):
    """Repository boundary; concrete storage remains in infrastructure."""

    def get_current(self, scope: ProfileScope) -> DecisionSnapshot | None: ...

    def get_or_create(self, scope: ProfileScope, *, expires_at: datetime) -> DecisionSnapshot: ...

    def save(
        self,
        scope: ProfileScope,
        state: DecisionState,
        *,
        expected_revision: int,
        expires_at: datetime,
    ) -> DecisionSnapshot: ...


class DecisionAnalyticsWriter(Protocol):
    """Owner-scoped, idempotent persistence boundary for observational events."""

    def append(self, scope: ProfileScope, events: tuple[DecisionAnalyticsEvent, ...]) -> int: ...


class ProgramCandidateSnapshot(ContractModel):
    """One canonical program with its optional curriculum fingerprint."""

    program: Program
    fingerprint: ProgramFingerprint | None = None

    def model_post_init(self, __context: object) -> None:
        if self.fingerprint is not None:
            if self.fingerprint.program_id != self.program.id:
                raise ValueError("candidate fingerprint must belong to program")
            if self.fingerprint.program_code != self.program.code:
                raise ValueError("candidate fingerprint code must match program")


class ProgramCandidateSource(Protocol):
    """Read source-backed candidate snapshots from the composition root."""

    def list_candidates(self) -> tuple[ProgramCandidateSnapshot, ...]: ...


__all__ = [
    "DecisionBindingOutcome",
    "DecisionBindingPort",
    "DecisionAnalyticsWriter",
    "DecisionContextRepository",
    "ProgramCandidateSnapshot",
    "ProgramCandidateSource",
]
