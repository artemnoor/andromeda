"""Maps generic review decisions onto policy's existing approval ledger."""

from __future__ import annotations

from andromeda.modules.knowledge.contracts.public import (
    KnowledgeReviewAction,
    KnowledgeReviewCommand,
    KnowledgeReviewPolicyDecision,
    KnowledgeReviewPolicyDecisionStatus,
    KnowledgeReviewTargetKind,
)
from andromeda.modules.policy.contracts.approval import (
    PolicyApprovalCommand,
    PolicyApprovalEventKind,
)
from andromeda.modules.policy.services.approval import PolicyApprovalCommandService
from andromeda.shared.contracts.errors import ValidationError


class PolicyApprovalReviewAdapter:
    """Preserves policy ownership while exposing a typed review receipt."""

    def __init__(self, approval_commands: PolicyApprovalCommandService) -> None:
        self._approval_commands = approval_commands

    def decide(self, command: KnowledgeReviewCommand) -> KnowledgeReviewPolicyDecision:
        if command.target.kind is not KnowledgeReviewTargetKind.POLICY_RULE:
            raise ValidationError("policy approval adapter requires a policy-rule review target")
        kind = {
            KnowledgeReviewAction.APPROVE: PolicyApprovalEventKind.APPROVED,
            KnowledgeReviewAction.REJECT: PolicyApprovalEventKind.REJECTED,
        }.get(command.action)
        if kind is None:
            raise ValidationError("policy approval supports only approve/reject review actions")
        event = self._approval_commands.decide(
            PolicyApprovalCommand(
                rule_id=command.target.object_id,
                revision=command.target.revision,
                revision_hash=command.target.revision_hash,
                kind=kind,
                actor_account_id=command.actor_account_id,
                reason=command.reason,
                recorded_at=command.recorded_at,
                preview_fingerprint=command.policy_preview_fingerprint,
            )
        )
        return KnowledgeReviewPolicyDecision(
            target=command.target,
            action=command.action,
            status=(
                KnowledgeReviewPolicyDecisionStatus.APPROVED
                if event.kind is PolicyApprovalEventKind.APPROVED
                else KnowledgeReviewPolicyDecisionStatus.REJECTED
            ),
            approval_event_id=event.event_id,
            sequence=event.sequence,
            actor_account_id=event.actor_account_id,
            reason=event.reason,
            recorded_at=event.recorded_at,
            preview_fingerprint=event.preview_fingerprint,
        )


__all__ = ["PolicyApprovalReviewAdapter"]
