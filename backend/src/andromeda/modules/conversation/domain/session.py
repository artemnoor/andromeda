"""Pure session merge and slot-derivation logic."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import cast

from ...entity_resolution.contracts.public import ResolutionEntityType
from ..contracts.public import (
    ConversationIntent,
    ConversationSlot,
    FactOrigin,
    NextAction,
    ParsedQuery,
    QueryFact,
    QueryFrame,
    QuerySession,
    ExamScore,
)


def merge_parsed_query(session: QuerySession, parsed: ParsedQuery, *, updated_at: datetime) -> QuerySession:
    if updated_at.tzinfo is None:
        raise ValueError("updated_at must be timezone-aware")
    entities = {key: tuple(values) for key, values in session.entities.items()}
    if parsed.university_queries:
        entities[ResolutionEntityType.UNIVERSITY] = tuple(
            dict.fromkeys((*entities.get(ResolutionEntityType.UNIVERSITY, ()), *parsed.university_queries))
        )
    if parsed.direction_queries:
        entities[ResolutionEntityType.DIRECTION] = tuple(
            dict.fromkeys((*entities.get(ResolutionEntityType.DIRECTION, ()), *parsed.direction_queries))
        )
    if parsed.program_queries:
        entities[ResolutionEntityType.PROGRAM] = tuple(
            dict.fromkeys((*entities.get(ResolutionEntityType.PROGRAM, ()), *parsed.program_queries))
        )
    known_slots = dict(session.known_slots)
    confirmed_parameters = dict(session.confirmed_parameters)
    inferred_parameters = dict(session.inferred_parameters)
    if parsed.total_score is not None:
        known_slots["total_score"] = parsed.total_score
        confirmed_parameters["total_score"] = QueryFact(value=parsed.total_score, origin=FactOrigin.EXPLICIT_USER, confirmed=True)
    if parsed.exam_scores:
        known_slots["exam_scores"] = tuple(parsed.exam_scores)
        confirmed_parameters["exam_scores"] = QueryFact(value=tuple(parsed.exam_scores), origin=FactOrigin.EXPLICIT_USER, confirmed=True)
    if parsed.semester is not None:
        confirmed_parameters["semester"] = QueryFact(value=parsed.semester, origin=FactOrigin.EXPLICIT_USER, confirmed=True)
    if parsed.course_year is not None:
        confirmed_parameters["course_year"] = QueryFact(value=parsed.course_year, origin=FactOrigin.EXPLICIT_USER, confirmed=True)
    if parsed.aggregation is not None:
        inferred_parameters["aggregation"] = QueryFact(
            value=parsed.aggregation,
            origin=FactOrigin.DETERMINISTIC_INFERENCE,
            confirmed=False,
        )
    metrics = tuple(dict.fromkeys((*session.metrics, *parsed.metric_codes)))
    intent = parsed.intent if parsed.intent is not ConversationIntent.UNKNOWN else session.intent
    scope = parsed.scope or session.scope
    aggregation = parsed.aggregation or session.aggregation
    stored_total_score = cast(Decimal | None, known_slots.get("total_score"))
    stored_exam_scores = cast(tuple[ExamScore, ...], known_slots.get("exam_scores", ()))
    missing_slots, next_action = _derive_slots(
        intent,
        metrics,
        parsed.total_score if parsed.total_score is not None else stored_total_score,
        parsed.exam_scores or stored_exam_scores,
        entities,
    )
    candidate = session.model_copy(
        update={
            "intent": intent,
            "frame": QueryFrame(
                intent=intent,
                entities=entities,
                metrics=metrics,
                scope=scope,
                scope_ids=session.scope_ids,
                filters=session.filters,
                aggregation=aggregation,
                semester=parsed.semester or _fact_int(confirmed_parameters, "semester"),
                course_year=parsed.course_year or _fact_int(confirmed_parameters, "course_year"),
                missing_fields=missing_slots,
            ),
            "entities": entities,
            "metrics": metrics,
            "scope": scope,
            "aggregation": aggregation,
            "known_slots": known_slots,
            "confirmed_parameters": confirmed_parameters,
            "inferred_parameters": inferred_parameters,
            "missing_slots": missing_slots,
            "next_action": next_action,
            "last_action": next_action,
            "updated_at": updated_at,
            "revision": session.revision + 1,
        }
    )
    if candidate.model_dump(exclude={"revision", "updated_at"}) == session.model_dump(exclude={"revision", "updated_at"}):
        return session
    return candidate


def _fact_int(facts: dict[str, QueryFact], key: str) -> int | None:
    fact = facts.get(key)
    return fact.value if fact is not None and isinstance(fact.value, int) else None


def _derive_slots(
    intent: ConversationIntent,
    metrics: tuple[str, ...],
    total_score: Decimal | None,
    exam_scores: tuple[ExamScore, ...],
    entities: dict[ResolutionEntityType, tuple[str, ...]],
) -> tuple[tuple[ConversationSlot, ...], NextAction]:
    if intent is ConversationIntent.ADMISSION_SEARCH:
        if total_score is None and not exam_scores:
            return (ConversationSlot.TOTAL_SCORE, ConversationSlot.EXAMS), NextAction.ASK_FOR_EXAMS
        if not exam_scores:
            return (ConversationSlot.EXAMS,), NextAction.ASK_FOR_EXAMS
        if not entities.get(ResolutionEntityType.UNIVERSITY):
            return (ConversationSlot.UNIVERSITY_SCOPE,), NextAction.ASK_FOR_UNIVERSITY_SCOPE
        return (), NextAction.EXECUTE_QUERY
    if not metrics:
        return (ConversationSlot.METRIC,), NextAction.ASK_FOR_METRIC
    if not entities.get(ResolutionEntityType.PROGRAM) and not entities.get(ResolutionEntityType.UNIVERSITY) and not entities.get(ResolutionEntityType.DIRECTION):
        return (ConversationSlot.ENTITY,), NextAction.ASK_FOR_ENTITY
    return (), NextAction.EXECUTE_QUERY


__all__ = ["merge_parsed_query"]
