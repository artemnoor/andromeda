"""Pure session merge and slot-derivation logic."""

from __future__ import annotations

from datetime import datetime

from ...entity_resolution.contracts.public import ResolutionEntityType
from ..contracts.public import (
    ConversationIntent,
    ConversationSlot,
    NextAction,
    ParsedQuery,
    QuerySession,
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
    if parsed.total_score is not None:
        known_slots["total_score"] = parsed.total_score
    if parsed.exam_scores:
        known_slots["exam_scores"] = tuple(parsed.exam_scores)
    metrics = tuple(dict.fromkeys((*session.metrics, *parsed.metric_codes)))
    intent = parsed.intent if parsed.intent is not ConversationIntent.UNKNOWN else session.intent
    scope = parsed.scope or session.scope
    aggregation = parsed.aggregation or session.aggregation
    missing_slots, next_action = _derive_slots(intent, metrics, parsed.total_score or known_slots.get("total_score"), parsed.exam_scores or known_slots.get("exam_scores", ()), entities)
    candidate = session.model_copy(
        update={
            "intent": intent,
            "entities": entities,
            "metrics": metrics,
            "scope": scope,
            "aggregation": aggregation,
            "known_slots": known_slots,
            "missing_slots": missing_slots,
            "next_action": next_action,
            "updated_at": updated_at,
            "revision": session.revision + 1,
        }
    )
    if candidate.model_dump(exclude={"revision", "updated_at"}) == session.model_dump(exclude={"revision", "updated_at"}):
        return session
    return candidate


def _derive_slots(intent, metrics, total_score, exam_scores, entities):
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
