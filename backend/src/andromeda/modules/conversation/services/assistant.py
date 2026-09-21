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
from andromeda.modules.conversation.contracts.public import (
    ConversationSlot,
    NextAction,
    QuerySession,
    QuerySessionId,
)
from andromeda.modules.entity_resolution.contracts.ports import EntityResolverGateway
from andromeda.modules.entity_resolution.contracts.public import (
    ResolutionContext,
    ResolutionEntityType,
    ResolutionStatus,
)
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
        entity_resolver: EntityResolverGateway | None = None,
        ttl_seconds: int = 86_400,
    ) -> None:
        self._sessions = sessions
        self._conversation = conversation
        self._decision_policy = decision_policy
        self._response_policy = response_policy
        self._analytics = analytics
        self._admission_fit = admission_fit
        self._programs = programs
        self._entity_resolver = entity_resolver
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
        updated = self._resolve_entities(updated)
        decision = self._decision_policy.decide(updated)
        if decision.action is DecisionAction.ASK_CLARIFICATION:
            updated = updated.model_copy(update={"last_question": decision.question})
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
            envelope = build_response_envelope(
                result,
                response_policy,
                text=f"Найдено результатов: {len(result.rows)}",
                result_reference=updated.session_id,
                metadata={"resolution_evidence": updated.frame.resolution_evidence},
            )
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

    def _resolve_entities(self, session: QuerySession) -> QuerySession:
        if self._entity_resolver is None:
            return session
        resolved = {key: tuple(values) for key, values in session.entities.items()}
        resolution_cache = dict(session.resolution_cache)
        resolution_evidence = dict(session.frame.resolution_evidence)
        unresolved: list[str] = []
        for entity_type in (
            ResolutionEntityType.UNIVERSITY,
            ResolutionEntityType.DIRECTION,
            ResolutionEntityType.PROGRAM,
        ):
            queries = tuple(resolved.get(entity_type, ()))
            if not queries:
                continue
            selected: list[str] = []
            university_ids = tuple(resolved.get(ResolutionEntityType.UNIVERSITY, ()))
            context_university = (
                university_ids[0]
                if len(university_ids) == 1 and university_ids[0].startswith("university:")
                else None
            )
            context = ResolutionContext(university_id=context_university) if context_university else None
            for query in queries:
                cache_key = f"{entity_type.value}:{query}"
                cached_id = resolution_cache.get(cache_key)
                if cached_id:
                    selected.append(cached_id)
                    resolution_evidence[cache_key] = "strategy=deterministic;source=session_cache"
                    continue
                result = self._entity_resolver.resolve(entity_type, query, context=context, limit=10)
                if (
                    result.resolution_strategy == "deterministic"
                    and result.status in {ResolutionStatus.EXACT, ResolutionStatus.RESOLVED}
                    and result.selected_id
                ):
                    selected.append(result.selected_id)
                    resolution_cache[cache_key] = result.selected_id
                    resolution_evidence[cache_key] = (
                        f"strategy={result.resolution_strategy};candidate_hash={result.candidate_hash or 'none'}"
                    )
                else:
                    unresolved.append(f"{entity_type.value}:{query}")
                    resolution_evidence[cache_key] = (
                        f"strategy={result.resolution_strategy};candidate_hash={result.candidate_hash or 'none'}"
                    )
            if selected:
                resolved[entity_type] = tuple(dict.fromkeys(selected))
        if not unresolved:
            return session.model_copy(
                update={
                    "entities": resolved,
                    "resolution_cache": resolution_cache,
                    "unresolved_entities": (),
                    "frame": session.frame.model_copy(
                        update={"entities": resolved, "resolution_evidence": resolution_evidence}
                    ),
                }
            )
        university_unresolved = any(item.startswith("university:") for item in unresolved)
        next_action = NextAction.ASK_FOR_UNIVERSITY_SCOPE if university_unresolved else NextAction.ASK_FOR_ENTITY
        missing = (ConversationSlot.UNIVERSITY_SCOPE,) if university_unresolved else (ConversationSlot.ENTITY,)
        return session.model_copy(
            update={
                "entities": resolved,
                "resolution_cache": resolution_cache,
                "unresolved_entities": tuple(unresolved),
                "missing_slots": missing,
                "next_action": next_action,
                "last_action": next_action,
                "frame": session.frame.model_copy(
                    update={
                        "entities": resolved,
                        "missing_fields": missing,
                        "resolution_evidence": resolution_evidence,
                    }
                ),
            }
        )

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
