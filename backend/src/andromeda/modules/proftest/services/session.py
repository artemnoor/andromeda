"""Application orchestration for the adaptive proftest session API."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging

from andromeda.modules.recommendations.contracts.public import RankedFingerprint, RecommendationRequest, RecommendationServicePort
from andromeda.shared.contracts.errors import ConflictError, NotFoundError, ValidationError

from ..contracts.public import (
    AdaptiveAnswer,
    AdaptiveSelection,
    AnswerSet,
    AnswerStatus,
    AnalyticsEventType,
    ProfileScope,
    ProftestAnalyticsEvent,
    ProftestAnswerSession,
    ProftestResults,
    ProftestSessionView,
    Question,
    QuestionStage,
    SessionAnswer,
    SessionProgress,
    SessionStatus,
    UserProfile,
)
from ..repository.ports import ProftestAnalyticsWriter, ProftestAnswerSessionRepository
from .adaptive import AdaptiveCandidate, AdaptiveQuestionFactory, AdaptiveQuestionSelector
from .catalog import ProftestCatalogService
from .profile_builder import UserProfileBuilder
from .questionnaire import build_session_questionnaire


logger = logging.getLogger("andromeda.proftest.session")
MAX_ADAPTIVE_QUESTIONS = 10


class ProftestSessionService:
    """Keep session transitions typed and outside FastAPI/ORM boundaries."""

    def __init__(
        self,
        catalog: ProftestCatalogService,
        recommendations: RecommendationServicePort,
        sessions: ProftestAnswerSessionRepository,
        analytics: ProftestAnalyticsWriter | None = None,
        *,
        ttl_seconds: int = 60 * 60 * 24 * 30,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        self._catalog = catalog
        self._recommendations = recommendations
        self._sessions = sessions
        self._analytics = analytics
        self._ttl_seconds = ttl_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._profile_builder = UserProfileBuilder()
        self._selector = AdaptiveQuestionSelector()
        self._factory = AdaptiveQuestionFactory()

    def start(self, scope: ProfileScope) -> ProftestSessionView:
        questionnaire = build_session_questionnaire()
        session = self._sessions.start(
            scope,
            question_set_version=questionnaire.question_set_version,
            current_question_id=questionnaire.questions[0].id,
            expires_at=self._expires_at(),
        )
        view = self._view(session)
        self._track(scope, session, AnalyticsEventType.TEST_STARTED)
        logger.info("proftest_session_start_complete status=%s revision=%d", session.status.value, session.revision)
        return view

    def current(self, scope: ProfileScope) -> ProftestSessionView:
        session = self._sessions.get_current(scope)
        if session is None:
            raise NotFoundError("Current proftest session was not found")
        return self._view(session)

    def save(self, scope: ProfileScope, answers: tuple[SessionAnswer, ...], *, expected_revision: int) -> ProftestSessionView:
        session = self._require_draft(scope)
        updated = self._apply_answers(session, answers, advance=False)
        saved = self._sessions.save(scope, updated, expected_revision=expected_revision)
        return self._view(saved)

    def next(self, scope: ProfileScope, answer: SessionAnswer, *, expected_revision: int) -> ProftestSessionView:
        session = self._require_draft(scope)
        updated = self._apply_answers(session, (answer,), advance=True)
        saved = self._sessions.save(scope, updated, expected_revision=expected_revision)
        self._track(scope, saved, AnalyticsEventType.ANSWER_SELECTED, payload={"questionId": answer.question_id})
        return self._view(saved)

    def complete(self, scope: ProfileScope) -> ProftestSessionView:
        session = self._sessions.get_current(scope)
        if session is None:
            raise NotFoundError("Current proftest session was not found")
        questionnaire = build_session_questionnaire()
        if session.status is SessionStatus.COMPLETED:
            profile = self._profile_builder.build(session.answer_set, questionnaire.questions, self._adaptive_questions(session))
            results = self._results(profile)
            return ProftestSessionView(session=session, progress=self._progress(session, None), results=results)
        self._validate_required(session.answer_set, questionnaire.questions)
        profile = self._profile_builder.build(session.answer_set, questionnaire.questions, self._adaptive_questions(session))
        results = self._results(profile)
        completed, _snapshot = self._sessions.complete(scope, session, profile, expires_at=self._expires_at())
        self._track(scope, completed, AnalyticsEventType.TEST_COMPLETED)
        logger.info("proftest_session_complete recommendations=%d", len(results.recommendations))
        return ProftestSessionView(session=completed, progress=self._progress(completed, None), results=results)

    def append_analytics(self, scope: ProfileScope, events: tuple[ProftestAnalyticsEvent, ...]) -> int:
        if self._analytics is None:
            raise ValidationError("Proftest analytics is not configured")
        if len(events) > 50:
            raise ValidationError("Analytics batch is limited to 50 events")
        accepted = self._analytics.append(scope, events)
        logger.info("proftest_analytics_complete accepted=%d requested=%d", accepted, len(events))
        return accepted

    def _require_draft(self, scope: ProfileScope) -> ProftestAnswerSession:
        session = self._sessions.get_current(scope)
        if session is None:
            raise NotFoundError("Current proftest session was not found")
        if session.status is not SessionStatus.DRAFT:
            raise ConflictError("Proftest session is not editable")
        return session

    def _apply_answers(self, session: ProftestAnswerSession, inputs: tuple[SessionAnswer, ...], *, advance: bool) -> ProftestAnswerSession:
        if not inputs:
            raise ValidationError("At least one answer is required")
        questionnaire = build_session_questionnaire()
        core = questionnaire.questions
        core_map = {question.id: question for question in core}
        # Ranking the entire catalogue is only needed once the core questions
        # are complete (or when an adaptive branch is being edited). Keeping
        # core transitions cheap is important for browser UX and repeatable
        # ingestion-backed smoke tests.
        needs_selection = session.cursor >= len(core) or bool(session.answer_set.adaptive_answers) or any(item.question_id not in core_map for item in inputs)
        selection = self._selection(session, core) if needs_selection else None
        adaptive_questions = session.adaptive_questions
        if selection is not None:
            current_adaptive = self._current_question(session, core, selection)
            if current_adaptive is not None and current_adaptive.id not in {question.id for question in adaptive_questions}:
                adaptive_questions = (*adaptive_questions, current_adaptive)
        question_map = {**core_map, **{question.id: question for question in adaptive_questions}}
        answers = list(session.answer_set.answers)
        adaptive_answers = list(session.answer_set.adaptive_answers)
        changed = 0
        first_edited_index: int | None = None
        stale_ids = list(session.stale_question_ids)
        for incoming in inputs:
            question = question_map.get(incoming.question_id)
            if question is None:
                raise ValidationError("Question does not belong to the pinned question set or branch")
            if question.adaptive:
                if incoming.status.value != "answered" or len(incoming.option_ids) != 1:
                    raise ValidationError("Adaptive questions require one selected option")
                if incoming.option_ids[0] not in {option.id for option in question.options}:
                    logger.warning("[FIX:session-validation] rejected adaptive option question_id=%s", _safe_id(question.id))
                    raise ValidationError("Adaptive answer option does not belong to the selected question")
                dimension = incoming.dimension or (question.declared_dimensions[0] if question.declared_dimensions else None)
                if dimension not in question.declared_dimensions:
                    raise ValidationError("Adaptive answer dimension is not supported by the selected question")
                adaptive_answer = AdaptiveAnswer(question_id=question.id, option_id=incoming.option_ids[0], dimension=dimension)
                adaptive_old = next((item for item in adaptive_answers if item.question_id == adaptive_answer.question_id), None)
                if adaptive_old != adaptive_answer:
                    changed += 1
                adaptive_answers = [item for item in adaptive_answers if item.question_id != adaptive_answer.question_id]
                adaptive_answers.append(adaptive_answer)
                continue
            if incoming.status is AnswerStatus.SKIPPED and not question.allow_skip:
                raise ValidationError("Question does not allow skipping")
            if incoming.status is AnswerStatus.UNCERTAIN and not question.allow_uncertain:
                raise ValidationError("Question does not allow uncertain answers")
            if len(incoming.option_ids) != len(set(incoming.option_ids)):
                raise ValidationError("Answer options must be unique")
            if incoming.status is AnswerStatus.ANSWERED and not incoming.option_ids:
                raise ValidationError("Answered questions require at least one option")
            if incoming.status is AnswerStatus.SKIPPED and incoming.option_ids:
                raise ValidationError("Skipped questions cannot contain options")
            invalid_option_ids = set(incoming.option_ids) - {option.id for option in question.options}
            if invalid_option_ids:
                logger.warning("[FIX:session-validation] rejected option question_id=%s invalid_count=%d", _safe_id(question.id), len(invalid_option_ids))
                raise ValidationError("Answer option does not belong to the selected question")
            core_answer = incoming.to_answer()
            if len(core_answer.option_ids) > question.max_selected:
                raise ValidationError("Too many selected options")
            core_old = next((item for item in answers if item.question_id == core_answer.question_id), None)
            if core_old != core_answer:
                changed += 1
            answers = [item for item in answers if item.question_id != core_answer.question_id]
            answers.append(core_answer)
            answer_index = core.index(question)
            if core_old is not None and core_old != core_answer and answer_index < session.cursor:
                first_edited_index = answer_index if first_edited_index is None else min(first_edited_index, answer_index)

        if first_edited_index is not None and adaptive_answers:
            stale_ids.extend(item.question_id for item in adaptive_answers)
            adaptive_answers = []
            adaptive_questions = ()
        cursor = session.cursor
        if advance:
            last_core_index = max((core.index(core_map[item.question_id]) for item in inputs if item.question_id in core_map), default=-1)
            cursor = max(cursor, last_core_index + 1)
            if any(item.question_id not in core_map for item in inputs):
                cursor = max(cursor, len(core) + len(adaptive_answers))
        elif first_edited_index is not None:
            cursor = first_edited_index + 1
        updated = session.model_copy(
            update={
                "answer_set": AnswerSet(answers=tuple(sorted(answers, key=lambda item: item.question_id)), adaptive_answers=tuple(sorted(adaptive_answers, key=lambda item: item.question_id))),
                "adaptive_questions": adaptive_questions,
                "cursor": cursor,
                "interaction_count": min(38, session.interaction_count + changed),
                "stale_question_ids": tuple(dict.fromkeys(stale_ids)),
            }
        )
        logger.debug("proftest_session_answers_applied changed=%d cursor=%d adaptive=%d", changed, updated.cursor, len(updated.answer_set.adaptive_answers))
        return updated

    def _view(self, session: ProftestAnswerSession) -> ProftestSessionView:
        questionnaire = build_session_questionnaire()
        if session.status is SessionStatus.COMPLETED:
            profile = self._profile_builder.build(session.answer_set, questionnaire.questions, self._adaptive_questions(session))
            return ProftestSessionView(session=session, progress=self._progress(session, None), results=self._results(profile))
        if session.cursor < len(questionnaire.questions):
            core_question = questionnaire.questions[session.cursor]
            return ProftestSessionView(session=session, current_question=core_question, progress=self._progress(session, core_question))
        selection = self._selection(session, questionnaire.questions)
        question = self._current_question(session, questionnaire.questions, selection)
        return ProftestSessionView(session=session, current_question=question, progress=self._progress(session, question), adaptive=selection if question is not None and question.adaptive else None)

    def _current_question(self, session: ProftestAnswerSession, core: tuple[Question, ...], selection: AdaptiveSelection) -> Question | None:
        if session.cursor < len(core):
            return core[session.cursor]
        if len(session.answer_set.adaptive_answers) >= MAX_ADAPTIVE_QUESTIONS or selection.status.value != "ready":
            return None
        return self._factory.create(selection, sequence=len(session.answer_set.adaptive_answers))

    def _selection(self, session: ProftestAnswerSession, core: tuple[Question, ...]) -> AdaptiveSelection:
        profile = self._profile_builder.build(session.answer_set, core, session.adaptive_questions)
        fingerprints = self._catalog.list_fingerprints()
        ranked = self._recommendations.rank_fingerprints(profile, fingerprints, limit=max(1, len(fingerprints)))
        selection = self._selector.select(
            tuple(AdaptiveCandidate(fingerprint=item.fingerprint, score=Decimal(item.score.content_fit)) for item in ranked),
            profile,
            asked_question_ids=tuple(item.question_id for item in session.answer_set.adaptive_answers),
            adaptive_count=len(session.answer_set.adaptive_answers),
        )
        logger.debug("[FIX:adaptive] ranking_rebuilt adaptive_count=%d profile_dimensions=%d", len(session.answer_set.adaptive_answers), len(profile.confidence_by_dimension))
        return selection

    def _adaptive_questions(self, session: ProftestAnswerSession) -> tuple[Question, ...]:
        if session.adaptive_questions:
            return session.adaptive_questions
        if not session.answer_set.adaptive_answers:
            return ()
        # Compatibility for drafts created before adaptive question snapshots
        # were persisted. New sessions always take the snapshot path above.
        questionnaire = build_session_questionnaire()
        base_session = session.model_copy(update={"answer_set": AnswerSet(answers=session.answer_set.answers)})
        selection = self._selection(base_session, questionnaire.questions)
        logger.warning("[FIX:adaptive] rebuilding_legacy_question_snapshots adaptive_count=%d", len(session.answer_set.adaptive_answers))
        return self._adaptive_questions_for_selection(selection, len(session.answer_set.adaptive_answers))

    def _adaptive_questions_for_selection(self, selection: AdaptiveSelection | None, count: int) -> tuple[Question, ...]:
        if selection is None:
            return ()
        return tuple(question for index in range(count) if (question := self._factory.create(selection, sequence=index)) is not None)

    def _results(self, profile: UserProfile) -> ProftestResults:
        fingerprints = self._catalog.list_fingerprints()
        result = self._recommendations.recommend_from_fingerprints(RecommendationRequest(profile=profile, limit=10), fingerprints)
        return ProftestResults(profile=profile, recommendations=result.recommendations)

    @staticmethod
    def _validate_required(answer_set: AnswerSet, questions: tuple[Question, ...]) -> None:
        answers = {answer.question_id: answer for answer in answer_set.answers}
        missing = [question.id for question in questions if question.required and question.id not in answers]
        skipped = [question.id for question in questions if answers.get(question.id) is not None and answers[question.id].status.value == "skipped" and question.required]
        if missing or skipped:
            raise ValidationError("Required proftest questions are incomplete")

    @staticmethod
    def _progress(session: ProftestAnswerSession, question: Question | None) -> SessionProgress:
        stages = (QuestionStage.ABOUT.value, QuestionStage.INTERESTS.value, QuestionStage.WORK_STYLE.value, QuestionStage.ANTI_INTERESTS.value, QuestionStage.TRADE_OFFS.value, QuestionStage.CLARIFICATION.value)
        stage = question.stage.value if question is not None and question.stage is not None else QuestionStage.CLARIFICATION.value
        stage_index = stages.index(stage)
        core_remaining = max(0, 24 - session.cursor)
        adaptive_remaining = 0 if session.status is SessionStatus.COMPLETED else max(0, MAX_ADAPTIVE_QUESTIONS - len(session.answer_set.adaptive_answers))
        return SessionProgress(stage=stage, stage_index=stage_index, stage_count=len(stages), answer_count=session.interaction_count, min_remaining=core_remaining + adaptive_remaining, max_remaining=min(38, core_remaining + 10))

    def _track(self, scope: ProfileScope, session: ProftestAnswerSession, event_type: AnalyticsEventType, *, payload: dict[str, str | int | float | bool | None] | None = None) -> None:
        if self._analytics is None:
            return
        now = self._clock()
        event = ProftestAnalyticsEvent(
            event_id=f"proftest-event:{__import__('uuid').uuid4().hex}",
            session_id=session.session_id,
            question_set_version=session.question_set_version,
            event_type=event_type,
            payload=payload or {},
            occurred_at=now,
            expires_at=now + timedelta(days=180),
        )
        self._analytics.append(scope, (event,))

    def _expires_at(self) -> datetime:
        return self._clock() + timedelta(seconds=self._ttl_seconds)


def _safe_id(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ")[:128]


__all__ = ["ProftestSessionService"]
