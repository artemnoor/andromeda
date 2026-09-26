"""Capability-gated commands for immutable policy revision and approval writes."""

from __future__ import annotations

from typing import Protocol

from andromeda.modules.policy.contracts.approval import (
    PolicyApprovalCapability,
    PolicyApprovalCommand,
    PolicyApprovalEvent,
    PolicyApprovalEventKind,
    PolicyApprovalState,
    PolicyRuleSubmission,
)
from andromeda.modules.policy.domain.approval import (
    create_approval_event,
    derive_approval_state,
)
from andromeda.modules.policy.domain.field_registry import validate_selector_ast
from andromeda.modules.policy.repository.ports import (
    PolicyCapabilityAuthorizer,
    PolicyRuleRepository,
)
from andromeda.shared.contracts.errors import ConflictError, NotFoundError


class PolicyApprovalUnitOfWork(Protocol):
    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class PolicyApprovalCommandService:
    """Authorize all mutations and keep revision+pending-event writes atomic."""

    def __init__(
        self,
        *,
        repository: PolicyRuleRepository,
        authorizer: PolicyCapabilityAuthorizer,
        unit_of_work: PolicyApprovalUnitOfWork,
    ) -> None:
        self._repository = repository
        self._authorizer = authorizer
        self._unit_of_work = unit_of_work

    def submit(self, submission: PolicyRuleSubmission) -> PolicyApprovalEvent:
        self._authorizer.require_capability(
            submission.submitted_by_account_id,
            PolicyApprovalCapability.SUBMIT_REVISION,
        )
        validate_selector_ast(submission.revision.selector)
        try:
            event = self._repository.submit_revision(submission)
            self._unit_of_work.commit()
            return event
        except Exception:
            self._unit_of_work.rollback()
            raise

    def decide(self, command: PolicyApprovalCommand) -> PolicyApprovalEvent:
        self._authorizer.require_capability(
            command.actor_account_id,
            PolicyApprovalCapability.APPROVE_REVISION,
        )
        try:
            revision = self._repository.get_revision(command.rule_id, command.revision)
            if revision is None:
                raise NotFoundError("Policy rule revision does not exist")
            if revision.content_hash != command.revision_hash:
                raise ConflictError("Policy decision is bound to a stale revision hash")
            history = self._repository.list_approval_events(command.rule_id, command.revision)
            state = derive_approval_state(
                history,
                rule_id=command.rule_id,
                revision=command.revision,
                revision_hash=revision.content_hash,
            )
            if state is not PolicyApprovalState.PENDING:
                latest = history[-1] if history else None
                repeated_state = {
                    PolicyApprovalEventKind.APPROVED: PolicyApprovalState.APPROVED,
                    PolicyApprovalEventKind.REJECTED: PolicyApprovalState.REJECTED,
                    PolicyApprovalEventKind.WITHDRAWN: PolicyApprovalState.WITHDRAWN,
                }[command.kind]
                if (
                    state is repeated_state
                    and latest is not None
                    and latest.kind is command.kind
                    and latest.actor_account_id == command.actor_account_id
                    and latest.reason == command.reason
                    and latest.recorded_at == command.recorded_at
                    and latest.revision_hash == command.revision_hash
                    and latest.preview_fingerprint == command.preview_fingerprint
                ):
                    self._unit_of_work.commit()
                    return latest
                raise ConflictError("Only a valid pending policy revision can receive a decision")
            event = create_approval_event(
                rule_id=command.rule_id,
                revision=command.revision,
                revision_hash=revision.content_hash,
                sequence=len(history) + 1,
                kind=command.kind,
                actor_account_id=command.actor_account_id,
                reason=command.reason,
                recorded_at=command.recorded_at,
                preview_fingerprint=command.preview_fingerprint,
            )
            appended = self._repository.append_approval_event(event)
            self._unit_of_work.commit()
            return appended
        except Exception:
            self._unit_of_work.rollback()
            raise


__all__ = ["PolicyApprovalCommandService", "PolicyApprovalUnitOfWork"]
