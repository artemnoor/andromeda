from __future__ import annotations

from datetime import UTC, datetime, timedelta

from andromeda.modules.conversation.contracts.policy import DecisionAction
from andromeda.modules.conversation.contracts.public import (
    ConversationIntent,
    NextAction,
    QuerySession,
)
from andromeda.modules.conversation.services.rule_decision_policy import (
    RuleBasedDecisionPolicy,
)
from andromeda.modules.proftest.contracts.public import ProfileScope


def _session(next_action: NextAction, *, intent: ConversationIntent = ConversationIntent.ANALYTICS_QUERY) -> QuerySession:
    now = datetime(2026, 9, 21, 14, 0, tzinfo=UTC)
    return QuerySession(
        session_id="query-session:" + "1" * 32,
        owner_scope=ProfileScope(session_key_hash="2" * 64),
        intent=intent,
        next_action=next_action,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(hours=1),
    )


def test_rule_policy_asks_for_missing_admission_slots() -> None:
    decision = RuleBasedDecisionPolicy().decide(_session(NextAction.ASK_FOR_EXAMS, intent=ConversationIntent.ADMISSION_SEARCH))
    assert decision.action is DecisionAction.ASK_CLARIFICATION
    assert decision.options
    assert "ЕГЭ" in decision.question


def test_rule_policy_selects_compare_and_execute_actions() -> None:
    compare = RuleBasedDecisionPolicy().decide(
        _session(NextAction.EXECUTE_QUERY, intent=ConversationIntent.COMPARE_PROGRAMS),
    )
    assert compare.action is DecisionAction.COMPARE
    execute = RuleBasedDecisionPolicy().decide(_session(NextAction.EXECUTE_QUERY))
    assert execute.action is DecisionAction.EXECUTE_QUERY
