from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from andromeda.modules.admissions.contracts.public import FundingType, StudyForm
from andromeda.modules.conversation.contracts.public import (
    AdmissionUniversityScope,
    ConversationIntent,
    ConversationSlot,
    FactOrigin,
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
    assert first.total_score == Decimal(270)

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
    assert completed.known_slots["total_score"] == Decimal(270)
    assert completed.confirmed_parameters["total_score"].origin is FactOrigin.EXPLICIT_USER
    assert completed.frame.intent is ConversationIntent.ADMISSION_SEARCH
    assert completed.frame.missing_fields == (ConversationSlot.UNIVERSITY_SCOPE,)


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


def test_query_frame_keeps_inference_separate_from_user_facts() -> None:
    parsed = RuleBasedQueryParser().parse(
        "В каком вузе в среднем больше математики: university:bmstu или university:hse"
    )
    session = merge_parsed_query(_session(), parsed, updated_at=NOW + timedelta(seconds=1))

    assert session.frame.aggregation.value == "mean"
    assert session.inferred_parameters["aggregation"].origin is FactOrigin.DETERMINISTIC_INFERENCE
    assert "aggregation" not in session.confirmed_parameters


def test_all_in_one_admission_request_with_funding_does_not_ask_redundant_questions() -> None:
    parsed = RuleBasedQueryParser().parse(
        "Куда я прохожу с 270: русский 90, математика 90, информатика 90, university:bmstu, бюджет"
    )
    session = merge_parsed_query(_session(), parsed, updated_at=NOW + timedelta(seconds=1))

    assert session.next_action is NextAction.EXECUTE_QUERY
    assert session.missing_slots == ()
    assert session.known_slots["funding_type"] is FundingType.BUDGET
    assert session.confirmed_parameters["funding_type"].origin is FactOrigin.EXPLICIT_USER


def test_explicit_any_university_scope_completes_admission_clarification() -> None:
    parser = RuleBasedQueryParser()
    session = merge_parsed_query(
        _session(),
        parser.parse("Куда я прохожу с 270?"),
        updated_at=NOW + timedelta(seconds=1),
    )
    session = merge_parsed_query(
        session,
        parser.parse("русский 90, математика 90, информатика 90"),
        updated_at=NOW + timedelta(seconds=2),
    )
    completed = merge_parsed_query(
        session,
        parser.parse("Любые вузы"),
        updated_at=NOW + timedelta(seconds=3),
    )

    assert completed.next_action is NextAction.ASK_FOR_FUNDING
    assert completed.missing_slots == (ConversationSlot.FUNDING,)
    assert completed.parser_version == "conversation-parser.v3"
    assert completed.admission_university_scope is AdmissionUniversityScope.ANY_UNIVERSITY
    assert completed.confirmed_parameters["admission_university_scope"].confirmed is True

    selected_funding = merge_parsed_query(
        completed,
        parser.parse("бюджет"),
        updated_at=NOW + timedelta(seconds=4),
    )
    assert selected_funding.next_action is NextAction.EXECUTE_QUERY
    assert selected_funding.missing_slots == ()
    assert selected_funding.confirmed_parameters["funding_type"].value is FundingType.BUDGET

    selected = merge_parsed_query(
        selected_funding,
        parser.parse("university:bmstu"),
        updated_at=NOW + timedelta(seconds=5),
    )
    assert selected.admission_university_scope is None
    assert selected.entities[ResolutionEntityType.UNIVERSITY] == ("university:bmstu",)


def test_parser_recognizes_funding_and_admission_preferences() -> None:
    parser = RuleBasedQueryParser()

    budget = parser.parse("Куда поступить, бюджет")
    assert budget.intent is ConversationIntent.ADMISSION_SEARCH
    assert budget.funding_type is FundingType.BUDGET

    paid = parser.parse("Смотрю платное обучение, очно в 2027 году")
    assert paid.intent is ConversationIntent.ADMISSION_SEARCH
    assert paid.funding_type is FundingType.PAID
    assert paid.study_form is StudyForm.FULL_TIME
    assert paid.admission_year == 2027
