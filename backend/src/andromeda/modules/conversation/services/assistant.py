"""Application service composing conversation, policies and existing engines."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from andromeda.modules.admission_fit.services.admission_fit import AdmissionFitService
from andromeda.modules.analytics.services.executor import AnalyticsExecutor
from andromeda.modules.conversation.contracts.assistant import (
    AssistantResult,
    AssistantState,
)
from andromeda.modules.conversation.contracts.policy import (
    DecisionAction,
    DecisionPolicyPort,
)
from andromeda.modules.conversation.contracts.ports import QuerySessionRepository
from andromeda.modules.conversation.contracts.public import QuerySession, QuerySessionId
from andromeda.modules.entity_resolution.contracts.public import ResolutionEntityType
from andromeda.modules.presentation.contracts.envelope import ResponseEnvelope
from andromeda.modules.presentation.contracts.policy import (
    ResponseFormat,
    ResponsePolicyPort,
    ResponseRequest,
)
from andromeda.modules.presentation.services.envelope_builder import (
    build_response_envelope,
)
from andromeda.modules.proftest.contracts.public import ProfileScope
from andromeda.modules.programs.repository.ports import ProgramReader
from andromeda.shared.contracts.errors import ContractError, ErrorCode, NotFoundError
from andromeda.shared.contracts.ids import ProgramId

from .engine import ConversationEngine
from .query_compiler import compile_session


class AssistantService:
    def __init__(
        self,
        sessions: QuerySessionRepository,
        conversation: ConversationEngine,
        decision_policy: DecisionPolicyPort,
        response_policy: ResponsePolicyPort,
        analytics: AnalyticsExecutor,
        admission_fit: AdmissionFitService,
        programs: ProgramReader,
        *,
        ttl_seconds: int = 86_400,
    ) -> None:
        self._sessions = sessions
        self._conversation = conversation
        self._decision_policy = decision_policy
        self._response_policy = response_policy
        self._analytics = analytics
        self._admission_fit = admission_fit
        self._programs = programs
        self._ttl_seconds = ttl_seconds

    def handle(
        self,
        text: str,
        *,
        owner_scope: ProfileScope,
        session_id: QuerySessionId | None = None,
        expected_revision: int | None = None,
        now: datetime | None = None,
    ) -> AssistantResult:
        timestamp = now or datetime.now(UTC)
        existing = self._sessions.get(session_id, owner_scope=owner_scope) if session_id is not None else None
        if session_id is not None and existing is None:
            raise NotFoundError("Query session was not found or belongs to another owner")
        session = existing or _new_session(owner_scope, timestamp, self._ttl_seconds)
        base_revision = session.revision if existing is not None else None
        updated = self._conversation.apply(session, text, expected_revision=expected_revision, now=timestamp)
        decision = self._decision_policy.decide(updated)
        if decision.action is DecisionAction.ASK_CLARIFICATION:
            self._save(updated, base_revision)
            return AssistantResult(
                state=AssistantState.NEEDS_CLARIFICATION,
                session_id=updated.session_id,
                revision=updated.revision,
                question=decision.question,
                options=decision.options,
                missing_slots=updated.missing_slots,
            )
        candidate_program_ids = self._candidate_program_ids(updated)
        compiled = compile_session(updated, candidate_program_ids=candidate_program_ids)
        if compiled.analytics_query is not None:
            result = self._analytics.execute(compiled.analytics_query)
            updated = updated.model_copy(update={"last_query": compiled.analytics_query})
            self._save(updated, base_revision)
            response_policy = self._response_policy.choose(
                ResponseRequest(result=result, comparison_requested=decision.action is DecisionAction.COMPARE)
            )
            envelope = build_response_envelope(result, response_policy, text=f"Найдено результатов: {len(result.rows)}", result_reference=updated.session_id)
            return AssistantResult(
                state=AssistantState.COMPLETE,
                session_id=updated.session_id,
                revision=updated.revision,
                response=envelope,
                query=compiled.analytics_query,
            )
        if compiled.admission_request is not None:
            admission_result = self._admission_fit.evaluate_batch(compiled.admission_request)
            updated = updated.model_copy(update={"last_query": None})
            self._save(updated, base_revision)
            envelope = ResponseEnvelope(
                response_type=ResponseFormat.TEXT,
                template="admission-fit-summary",
                text=f"Проверено программ: {len(admission_result.by_program_id)}",
                data={"outcomes": admission_result.model_dump(mode="json")},
                result_reference=updated.session_id,
            )
            return AssistantResult(
                state=AssistantState.COMPLETE,
                session_id=updated.session_id,
                revision=updated.revision,
                response=envelope,
                admission_request=compiled.admission_request,
                admission_result=admission_result,
            )
        raise ContractError(ErrorCode.INSUFFICIENT_DATA, "Admission search has no bounded candidate programs")

    def _candidate_program_ids(self, session: QuerySession) -> tuple[ProgramId, ...]:
        programs = tuple(session.entities.get(ResolutionEntityType.PROGRAM, ()))
        if programs:
            return programs[:50]
        university_ids = tuple(session.entities.get(ResolutionEntityType.UNIVERSITY, ()))
        direction_ids = set(session.entities.get(ResolutionEntityType.DIRECTION, ()))
        if university_ids:
            values = tuple(program for university_id in university_ids for program in self._programs.list(university_id=university_id))
            return tuple(program.id for program in values if not direction_ids or program.direction_id in direction_ids)[:50]
        if direction_ids:
            return tuple(program.id for program in self._programs.list() if program.direction_id in direction_ids)[:50]
        return ()

    def _save(self, session: QuerySession, base_revision: int | None) -> None:
        self._sessions.save(session, expected_revision=base_revision)


def _new_session(owner_scope: ProfileScope, now: datetime, ttl_seconds: int) -> QuerySession:
    return QuerySession(
        session_id=f"query-session:{uuid4().hex}",
        owner_scope=owner_scope,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
    )


__all__ = ["AssistantService"]
