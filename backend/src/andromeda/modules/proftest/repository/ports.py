"""Ports consumed by proftest application services."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Protocol

from andromeda.modules.curricula.contracts.public import Curriculum
from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.programs.contracts.public import Program
from andromeda.shared.contracts.ids import AccountId, DisciplineId, ProgramId

from ..domain.entities import UserProfile
from ..domain.profile import ProfileScope, UserProfileSnapshot


class ProftestCatalogReader(Protocol):
    """Read canonical content without exposing storage or transport details."""

    def list_programs(self) -> tuple[Program, ...]: ...

    def get_curriculum(self, program_id: ProgramId) -> Curriculum | None: ...

    def get_discipline(self, discipline_id: DisciplineId) -> Discipline | None: ...


class CurrentUserProfileReader(Protocol):
    """Read the current profile without exposing its storage implementation."""

    def get_current(self, scope: ProfileScope) -> UserProfileSnapshot | None: ...


class UserProfileRepository(CurrentUserProfileReader, Protocol):
    """Persistence port for anonymous/session-owned profiles."""

    def create(self, scope: ProfileScope, profile: UserProfile, *, expires_at: datetime) -> UserProfileSnapshot: ...

    def update(
        self,
        scope: ProfileScope,
        profile: UserProfile,
        *,
        expected_revision: int,
        expires_at: datetime,
    ) -> UserProfileSnapshot: ...

    def save_current(self, scope: ProfileScope, profile: UserProfile, *, expires_at: datetime) -> UserProfileSnapshot: ...


class ProfileBindingPort(Protocol):
    """Transfer an anonymous profile to one account without field-level merge."""

    def bind_anonymous_to_account(self, scope: ProfileScope, account_id: AccountId) -> ProfileBindingOutcome: ...


class ProfileBindingOutcome(str, Enum):
    BOUND = "bound"
    ACCOUNT_PROFILE_KEPT = "account_profile_kept"
    NO_ANONYMOUS_PROFILE = "no_anonymous_profile"


__all__ = ["CurrentUserProfileReader", "ProfileBindingOutcome", "ProfileBindingPort", "ProftestCatalogReader", "UserProfileRepository"]
