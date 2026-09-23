"""Application service composing conversation, policies and existing engines."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from andromeda.modules.admission_fit.contracts.public import AdmissionFitSearchGateway
from andromeda.modules.admissions.contracts.public import FundingType, StudyForm
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
    AdmissionUniversityScope,
    ConversationIntent,
    ConversationSlot,
    FactOrigin,
    NextAction,
    QueryFact,
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

logger = logging.getLogger("andromeda.conversation.assistant")


class AssistantService:
    def __init__(
        self,
        sessions: QuerySessionRepository,
        conversation: ConversationEngine,
        decision_policy: DecisionPolicyPort,
        response_policy: ResponsePolicyPort,
        analytics: AnalyticsExecutor,
        admission_fit: AdmissionFitSearchGateway,
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
        if updated.intent is ConversationIntent.ADMISSION_SEARCH and candidate_program_ids:
            updated = self._apply_admission_defaults(updated, candidate_program_ids)
        compiled = compile_session(updated, candidate_program_ids=candidate_program_ids)
        if updated.intent is ConversationIntent.ADMISSION_SEARCH:
            logger.info(
                "assistant_admission_scope_resolved scope=%s candidate_count=%d batch_count=%d",
                updated.admission_university_scope.value if updated.admission_university_scope else "selected_university",
                len(candidate_program_ids),
                len(compiled.admission_requests),
            )
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
        if compiled.admission_requests:
            admission_result = self._admission_fit.evaluate_batches(compiled.admission_requests)
            updated = updated.model_copy(update={"last_query": None})
            self._save(updated, base_revision)
            selected = compiled.admission_requests[0]
            default_year = updated.inferred_parameters.get("admission_year")
            default_form = updated.inferred_parameters.get("study_form")
            year_text = (
                f"{selected.admission_year} (последний опубликованный год)"
                if default_year is not None and selected.admission_year is not None
                else str(selected.admission_year)
                if selected.admission_year is not None
                else "подходящий опубликованный год не найден"
            )
            form_text = _study_form_label(selected.study_form)
            if default_form is not None:
                form_text += " (по умолчанию)"
            funding_text = _funding_label(selected.funding_type)
            assumptions = tuple(
                assumption
                for assumption in (
                    f"Год приёма: {year_text}" if default_year is not None else None,
                    f"Форма обучения: {form_text}" if default_form is not None else None,
                )
                if assumption is not None
            )
            logger.info(
                "assistant_admission_filters_resolved candidate_count=%d admission_year=%s study_form=%s funding_type=%s defaulted_year=%s defaulted_form=%s",
                len(candidate_program_ids),
                selected.admission_year if selected.admission_year is not None else "unavailable",
                selected.study_form.value if selected.study_form is not None else "unknown",
                selected.funding_type.value if selected.funding_type is not None else "unknown",
                default_year is not None,
                default_form is not None,
            )
            envelope = ResponseEnvelope(
                response_type=ResponseFormat.TEXT,
                template="admission-fit-summary",
                text=(
                    f"Проверено программ: {len(admission_result.by_program_id)}. "
                    f"Параметры: год приёма — {year_text}; форма — {form_text}; финансирование — {funding_text}."
                ),
                data={"outcomes": admission_result.model_dump(mode="json")},
                metadata={
                    "admission_year": selected.admission_year,
                    "study_form": selected.study_form.value if selected.study_form is not None else None,
                    "funding_type": selected.funding_type.value if selected.funding_type is not None else None,
                    "assumptions": assumptions,
                },
                result_reference=updated.session_id,
            )
            return AssistantResult(
                state=AssistantState.COMPLETE,
                session_id=updated.session_id,
                revision=updated.revision,
                response=envelope,
                admission_request=compiled.admission_request,
                admission_requests=compiled.admission_requests,
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
            return programs
        university_ids = tuple(session.entities.get(ResolutionEntityType.UNIVERSITY, ()))
        direction_ids = set(session.entities.get(ResolutionEntityType.DIRECTION, ()))
        if university_ids:
            values = tuple(program for university_id in university_ids for program in self._programs.list(university_id=university_id))
            return tuple(program.id for program in values if not direction_ids or program.direction_id in direction_ids)
        if session.admission_university_scope is AdmissionUniversityScope.ANY_UNIVERSITY:
            values = self._programs.list()
            return tuple(
                program.id
                for program in values
                if not direction_ids or program.direction_id in direction_ids
            )
        if direction_ids:
            return tuple(program.id for program in self._programs.list() if program.direction_id in direction_ids)
        return ()

    def _apply_admission_defaults(
        self,
        session: QuerySession,
        candidate_program_ids: tuple[ProgramId, ...],
    ) -> QuerySession:
        funding_fact = session.confirmed_parameters.get("funding_type")
        if funding_fact is None or not isinstance(funding_fact.value, FundingType):
            return session

        inferred = dict(session.inferred_parameters)
        confirmed_form = session.confirmed_parameters.get("study_form")
        if confirmed_form is None or not isinstance(confirmed_form.value, StudyForm):
            study_form = StudyForm.FULL_TIME
            inferred["study_form"] = QueryFact(
                value=study_form,
                origin=FactOrigin.POLICY_DEFAULT,
                confirmed=False,
                source="admission_search_default",
            )
        else:
            study_form = confirmed_form.value
            inferred.pop("study_form", None)

        confirmed_year = session.confirmed_parameters.get("admission_year")
        if confirmed_year is None or not isinstance(confirmed_year.value, int):
            admission_year = self._admission_fit.latest_published_year(
                candidate_program_ids,
                study_form=study_form,
                funding_type=funding_fact.value,
            )
            inferred["admission_year"] = QueryFact(
                value=admission_year,
                origin=FactOrigin.POLICY_DEFAULT,
                confirmed=False,
                source="latest_published_admission_offering",
            )
        else:
            inferred.pop("admission_year", None)

        assumption_strings: list[str] = []
        if "admission_year" in inferred:
            year = inferred["admission_year"].value
            assumption_strings.append(
                f"Год приёма выбран по последним опубликованным данным: {year}"
                if isinstance(year, int)
                else "Подходящий опубликованный год приёма не найден"
            )
        if "study_form" in inferred:
            assumption_strings.append("Очная форма выбрана по умолчанию")
        return session.model_copy(
            update={
                "inferred_parameters": inferred,
                "assumptions": tuple(assumption_strings),
            }
        )

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


def _study_form_label(value: StudyForm | None) -> str:
    return {
        StudyForm.FULL_TIME: "очная",
        StudyForm.PART_TIME: "заочная",
        StudyForm.EVENING: "вечерняя",
        StudyForm.ONLINE: "онлайн",
        StudyForm.UNKNOWN: "неизвестная",
        None: "не указана",
    }[value]


def _funding_label(value: FundingType | None) -> str:
    return {
        FundingType.BUDGET: "бюджет",
        FundingType.PAID: "платное обучение",
        FundingType.TARGETED: "целевой набор",
        FundingType.UNKNOWN: "неизвестно",
        None: "не выбран",
    }[value]


__all__ = ["AssistantService"]
