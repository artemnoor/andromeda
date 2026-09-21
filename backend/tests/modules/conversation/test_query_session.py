from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from andromeda.modules.conversation.contracts.public import (
    ConversationIntent,
    ConversationSlot,
    NextAction,
    QuerySession,
)
from andromeda.modules.conversation.domain.session import merge_parsed_query
from andromeda.modules.conversation.services.rule_parser import RuleBasedQueryParser
from andromeda.modules.entity_resolution.contracts.public import ResolutionEntityType
from andromeda.modules.proftest.contracts.public import ProfileScope

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


def _session() -> QuerySession:
    return QuerySession(
        session_id="query-session:" + "a" * 32,
        owner_scope=ProfileScope(session_key_hash="b" * 64),
        created_at=NOW,
        updated_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


def test_parser_and_session_fill_admission_slots_in_two_turns() -> None:
    parser = RuleBasedQueryParser()
    first = parser.parse("Куда я прохожу с 270?")
    assert first.intent is ConversationIntent.ADMISSION_SEARCH
    assert first.total_score == Decimal("270")

    session = merge_parsed_query(_session(), first, updated_at=NOW + timedelta(seconds=1))
    assert session.missing_slots == (ConversationSlot.EXAMS,)
    assert session.next_action is NextAction.ASK_FOR_EXAMS
    assert session.revision == 2

    second = parser.parse("русский 90, математика 88, информатика 92")
    assert second.exam_scores
    assert second.metric_codes == ()
    completed = merge_parsed_query(session, second, updated_at=NOW + timedelta(seconds=2))
    assert completed.missing_slots == (ConversationSlot.UNIVERSITY_SCOPE,)
    assert completed.next_action is NextAction.ASK_FOR_UNIVERSITY_SCOPE
    assert completed.known_slots["total_score"] == Decimal("270")


def test_parser_supports_metric_comparison_and_canonical_entity_slots() -> None:
    parsed = RuleBasedQueryParser().parse(
        "Сравни program:bmstu:09.03.01-02 и program:bmstu:09.03.01-12 по математике и программированию"
    )
    assert parsed.intent is ConversationIntent.COMPARE_PROGRAMS
    assert parsed.metric_codes == ("math_share", "programming_share")
    assert parsed.program_queries == (
        "program:bmstu:09.03.01-02",
        "program:bmstu:09.03.01-12",
    )

    session = merge_parsed_query(_session(), parsed, updated_at=NOW + timedelta(seconds=1))
    assert session.entities[ResolutionEntityType.PROGRAM] == parsed.program_queries
    assert session.next_action is NextAction.EXECUTE_QUERY


def test_repeating_same_follow_up_is_idempotent_and_unknown_text_is_safe() -> None:
    parser = RuleBasedQueryParser()
    parsed = parser.parse("Куда я прохожу с 270?")
    session = merge_parsed_query(_session(), parsed, updated_at=NOW + timedelta(seconds=1))
    repeated = merge_parsed_query(session, parsed, updated_at=NOW + timedelta(seconds=2))
    assert repeated.revision == session.revision
    assert repeated.updated_at == session.updated_at

    unsupported = parser.parse("Расскажи что-нибудь необычное")
    assert unsupported.intent is ConversationIntent.UNKNOWN
    assert unsupported.metric_codes == ()
