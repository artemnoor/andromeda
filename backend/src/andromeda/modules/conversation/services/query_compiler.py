"""Compile owned conversation state into existing typed application requests."""

from __future__ import annotations

from typing import cast

from andromeda.modules.admission_fit.contracts.public import (
    ApplicantAdmissionProfile,
    ApplicantSubjectScore,
    BatchAdmissionFitRequest,
)
from andromeda.modules.analytics.contracts.metrics import (
    MetricAggregation,
    MetricEntityType,
)
from andromeda.modules.analytics.contracts.query import (
    FilterKind,
    QueryFilter,
    QueryScope,
    QuerySpec,
)
from andromeda.modules.entity_resolution.contracts.public import ResolutionEntityType
from andromeda.shared.contracts.errors import ContractError, ErrorCode
from andromeda.shared.contracts.ids import ProgramId

from ..contracts.public import (
    ConversationCompilation,
    ConversationIntent,
    ConversationSlot,
    ExamScore,
    NextAction,
    QuerySession,
)


def compile_session(session: QuerySession, *, candidate_program_ids: tuple[ProgramId, ...] = ()) -> ConversationCompilation:
    if session.next_action is not NextAction.EXECUTE_QUERY:
        return ConversationCompilation(next_action=session.next_action, missing_slots=session.missing_slots)
    if session.intent is ConversationIntent.ADMISSION_SEARCH:
        return _compile_admission(session, candidate_program_ids)
    if session.intent in {ConversationIntent.ANALYTICS_QUERY, ConversationIntent.COMPARE_PROGRAMS}:
        return ConversationCompilation(next_action=NextAction.EXECUTE_QUERY, analytics_query=_compile_analytics(session))
    raise ContractError(ErrorCode.INVALID_QUERY, "Conversation intent cannot be compiled")


def _compile_analytics(session: QuerySession) -> QuerySpec:
    programs = session.entities.get(ResolutionEntityType.PROGRAM, ())
    universities = session.entities.get(ResolutionEntityType.UNIVERSITY, ())
    directions = session.entities.get(ResolutionEntityType.DIRECTION, ())
    filters: list[QueryFilter] = []
    scope = QueryScope.ALL
    scope_ids: tuple[str, ...] = ()
    if programs:
        scope, scope_ids = QueryScope.PROGRAM, tuple(programs)
    elif universities:
        filters.append(QueryFilter(kind=FilterKind.UNIVERSITY, ids=tuple(universities)))
    elif directions:
        filters.append(QueryFilter(kind=FilterKind.DIRECTION, ids=tuple(directions)))
    else:
        raise ContractError(ErrorCode.INVALID_QUERY, "Analytics query requires a resolved program, direction, or university")
    if not session.metrics:
        raise ContractError(ErrorCode.INVALID_QUERY, "Analytics query requires at least one metric")
    aggregation = session.aggregation
    if aggregation is MetricAggregation.VALUE and len(programs) > 1:
        aggregation = MetricAggregation.VALUE
    return QuerySpec(
        entity=MetricEntityType.PROGRAM,
        metrics=session.metrics,
        scope=scope,
        scope_ids=scope_ids,
        filters=tuple(filters),
        aggregation=aggregation,
        limit=20,
    )


def _compile_admission(session: QuerySession, candidate_program_ids: tuple[ProgramId, ...]) -> ConversationCompilation:
    exam_scores = cast(tuple[ExamScore, ...], session.known_slots.get("exam_scores", ()))
    if not exam_scores:
        return ConversationCompilation(next_action=NextAction.ASK_FOR_EXAMS, missing_slots=(ConversationSlot.EXAMS,))
    applicant = ApplicantAdmissionProfile(
        scores=tuple(ApplicantSubjectScore(subject=item.subject, score=item.score) for item in exam_scores)
    )
    university_ids = tuple(session.entities.get(ResolutionEntityType.UNIVERSITY, ()))
    program_ids = tuple(candidate_program_ids or session.entities.get(ResolutionEntityType.PROGRAM, ()))
    if not program_ids:
        return ConversationCompilation(
            next_action=NextAction.EXECUTE_QUERY,
            applicant=applicant,
            university_scope_ids=tuple(university_ids),
        )
    if len(program_ids) > 50:
        raise ContractError(ErrorCode.INVALID_QUERY, "Admission candidate set is bounded to 50 programs")
    request = BatchAdmissionFitRequest(program_ids=program_ids, applicant=applicant)
    return ConversationCompilation(
        next_action=NextAction.EXECUTE_QUERY,
        admission_request=request,
        applicant=applicant,
        university_scope_ids=tuple(university_ids),
    )


__all__ = ["compile_session"]
