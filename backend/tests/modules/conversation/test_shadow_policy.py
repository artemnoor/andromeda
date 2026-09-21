from datetime import UTC, datetime, timedelta

from andromeda.modules.conversation.contracts.policy import (
    DecisionAction,
    DecisionModelPort,
    DecisionPolicyResult,
    NextActionDecision,
)
from andromeda.modules.conversation.contracts.public import QuerySession
from andromeda.modules.conversation.services.model_decision_policy import (
    ModelBackedDecisionPolicy,
    ShadowDecisionPolicy,
)
from andromeda.modules.proftest.contracts.public import ProfileScope


class _Model:
    def choose_next_action(self, session, **kwargs):  # type: ignore[no-untyped-def]
        del session, kwargs
        return NextActionDecision(
            decision=DecisionPolicyResult(
                action=DecisionAction.EXECUTE_QUERY,
                reason="model fixture",
            )
        )


def _session() -> QuerySession:
    now = datetime(2026, 9, 22, tzinfo=UTC)
    return QuerySession(
        session_id="query-session:" + "a" * 32,
        owner_scope=ProfileScope(session_key_hash="b" * 64),
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(hours=1),
    )


def test_model_backed_policy_uses_typed_model_answer() -> None:
    result = ModelBackedDecisionPolicy(_Model()).decide(_session())

    assert result.action is DecisionAction.EXECUTE_QUERY


def test_shadow_policy_always_returns_deterministic_result() -> None:
    result = ShadowDecisionPolicy(_Model()).decide(_session())

    assert result.action is DecisionAction.ASK_CLARIFICATION
