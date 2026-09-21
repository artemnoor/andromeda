"""Concrete aiogram flows backed only by the public HTTP API and OG routes."""

from __future__ import annotations

import logging

from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
)

from ..clients.backend import BackendHttpClient
from ..clients.errors import BackendError, BackendTransportError, RenderError
from ..config import Settings
from ..handlers import keyboards, texts
from ..parsing.admission_input import parse_exam_scores
from ..parsing.program_resolver import ProgramResolver
from ..render.client import RendererClient
from ..state.callbacks import CallbackPayload, CallbackStore
from ..state.repository import SessionRepository

logger = logging.getLogger("andromeda_telegram.flows")


class TelegramFlows:
    def __init__(self, settings: Settings, backend: BackendHttpClient, renderer: RendererClient, sessions: SessionRepository, resolver: ProgramResolver, callbacks: CallbackStore) -> None:
        self._settings = settings
        self._backend = backend
        self._renderer = renderer
        self._sessions = sessions
        self._resolver = resolver
        self._callbacks = callbacks

    async def start(self, message: Message) -> None:
        await message.answer(texts.START)

    async def assistant(self, message: Message) -> None:
        """Forward free-form questions to the channel-neutral assistant seam."""

        owner = _owner_key(message)
        state = self._sessions.get_assistant_state(owner)
        try:
            result = await self._backend.assistant_query(
                (message.text or "").strip(),
                session_id=state.session_id if state is not None else None,
                expected_revision=state.revision if state is not None else None,
                session_cookie=self._sessions.get_cookie(owner),
            )
            self._remember(owner, result.session_cookie)
            self._sessions.save_assistant_state(owner, result.value.session_id, result.value.revision)
            if result.value.state in {"needs_clarification", "ambiguous"}:
                await message.answer(_assistant_question(result.value))
                return
            envelope = result.value.response
            if envelope is None:
                await message.answer("Ответ получен, но в нём нет отображаемого представления.")
                return
            if envelope.response_type == "text":
                await message.answer(envelope.text or "Готово.")
                return
            image = await self._render_assistant_envelope(envelope, owner)
            if image is None:
                await message.answer(envelope.text or "Результат готов. Откройте его в приложении.")
                return
            await _photo(message, image, envelope.text or "Результат запроса.")
        except (BackendError, BackendTransportError, RenderError):
            await message.answer(texts.SOURCE_GAP)

    async def catalog(self, message: Message) -> None:
        owner = _owner_key(message)
        cookie = self._sessions.get_cookie(owner)
        try:
            result = await self._backend.list_programs(session_cookie=cookie)
            self._remember(owner, result.session_cookie)
            image = await self._renderer.render("catalog", {}, revision="0")
            ids = tuple(item.id for item in result.value.items[:3])
            markup = keyboards.image_actions(owner, ids, self._callbacks, self._settings.web_app_url) if ids else None
            await _photo(message, image, "Актуальный каталог программ.", markup)
        except (BackendError, BackendTransportError, RenderError):
            await message.answer(texts.CATALOG_EMPTY)

    async def compare(self, message: Message, query: str) -> None:
        owner = _owner_key(message)
        cookie = self._sessions.get_cookie(owner)
        try:
            results = await self._resolver.resolve_many(query, session_cookie=cookie)
            for result in results:
                self._remember(owner, result.session_cookie)
            if any(not result.found for result in results):
                await message.answer(texts.NOT_FOUND)
                return
            ambiguous = next((result for result in results if not result.exact), None)
            if ambiguous is not None:
                choices = tuple((item.id, f"{item.code} · {item.name}") for item in ambiguous.matches)
                await message.answer(texts.AMBIGUOUS, reply_markup=keyboards.resolver_choices(owner, choices, self._callbacks))
                return
            ids = tuple(dict.fromkeys(item.id for result in results for item in result.matches))[:3]
            if len(ids) < 2:
                await message.answer("Укажите две разные программы: например, «сравни … и …».")
                return
            suggestions = await self._backend.get_suggestions(session_cookie=self._sessions.get_cookie(owner))
            self._remember(owner, suggestions.session_cookie)
            image = await self._renderer.render("compare", {"ids": ",".join(ids), "theme": "light"}, revision=str(suggestions.value.context_revision), session_cookie=self._sessions.get_cookie(owner))
            await _photo(message, image, "Условное сравнение по доступным данным.", keyboards.image_actions(owner, ids, self._callbacks, self._settings.web_app_url, include_third=True))
            await self._maybe_refinement(message, owner, suggestions.value)
        except (BackendError, BackendTransportError, RenderError):
            await message.answer(texts.SOURCE_GAP)

    async def shortlist(self, message: Message) -> None:
        owner = _owner_key(message)
        cookie = self._sessions.get_cookie(owner)
        try:
            suggestions = await self._backend.get_suggestions(session_cookie=cookie)
            self._remember(owner, suggestions.session_cookie)
            image = await self._renderer.render("shortlist", {"theme": "light"}, revision=str(suggestions.value.context_revision), session_cookie=self._sessions.get_cookie(owner))
            ids = tuple(item.program_id for item in suggestions.value.active_shortlist)
            await _photo(message, image, "Ваш shortlist. Решение остаётся за вами.", keyboards.image_actions(owner, ids, self._callbacks, self._settings.web_app_url))
            await self._maybe_refinement(message, owner, suggestions.value)
        except (BackendError, BackendTransportError, RenderError):
            await message.answer(texts.SOURCE_GAP)

    async def admission(self, message: Message, query: str = "") -> None:
        owner = _owner_key(message)
        cookie = self._sessions.get_cookie(owner)
        try:
            suggestions = await self._backend.get_suggestions(session_cookie=cookie)
            self._remember(owner, suggestions.session_cookie)
            if query:
                scores = parse_exam_scores(query)
                mutation = await self._backend.update_constraints(scores, suggestions.value.context_revision, session_cookie=self._sessions.get_cookie(owner))
                self._remember(owner, mutation.session_cookie)
                suggestions = await self._backend.get_suggestions(session_cookie=self._sessions.get_cookie(owner))
                self._remember(owner, suggestions.session_cookie)
            image = await self._renderer.render("chances", {"theme": "light"}, revision=str(suggestions.value.context_revision), session_cookie=self._sessions.get_cookie(owner))
            ids = tuple(item.program_id for item in (*suggestions.value.primary_candidates, *suggestions.value.alternative_candidates))[:3]
            markup = keyboards.image_actions(owner, ids, self._callbacks, self._settings.web_app_url, include_third=True) if ids else None
            await _photo(message, image, "Реалистичность — оценка риска по имеющимся данным, не гарантия поступления.", markup)
        except (BackendError, BackendTransportError, RenderError):
            await message.answer("Не удалось проверить поступление. Добавьте ограничения и баллы через приложение.")
        except ValueError as error:
            await message.answer(str(error))

    async def digest(self, message: Message) -> None:
        owner = _owner_key(message)
        cookie = self._sessions.get_cookie(owner)
        try:
            suggestions = await self._backend.get_suggestions(session_cookie=cookie)
            self._remember(owner, suggestions.session_cookie)
            image = await self._renderer.render("digest", {"theme": "light"}, revision=str(suggestions.value.context_revision), session_cookie=self._sessions.get_cookie(owner))
            ids = tuple(item.program_id for item in suggestions.value.active_shortlist)[:3]
            markup = keyboards.image_actions(owner, ids, self._callbacks, self._settings.web_app_url) if ids else None
            await _photo(message, image, "Дайджест текущего состояния выбора.", markup)
        except (BackendError, BackendTransportError, RenderError):
            await message.answer(texts.SOURCE_GAP)

    async def callback(self, callback: CallbackQuery, data: object) -> None:
        owner = _owner_key(callback)
        payload = self._callbacks.consume(owner, str(data))
        await callback.answer()
        message = callback.message
        if payload is None or not isinstance(message, Message):
            await _callback_text(callback, "Кнопка устарела. Откройте экран ещё раз.")
            return
        try:
            if payload.action == "details" and payload.program_ids:
                await self._details(message, owner, payload.program_ids[0])
            elif payload.action in {"curriculum", "radar"} and payload.program_ids:
                await self._render_template(message, owner, payload.action, payload.program_ids)
            elif payload.action == "compare":
                await self.compare(message, " и ".join(payload.program_ids))
            elif payload.action == "shortlist_add" and payload.program_ids:
                await self._add_shortlist(message, owner, payload.program_ids[0])
            elif payload.action == "refinement" and payload.question_id and payload.option_id and payload.revision:
                await self._refinement(message, owner, payload)
            elif payload.action == "realism":
                await _callback_text(callback, "Реалистичность показывает риск по введённым баллам и качеству источников; исторический порог не гарантирует поступление.")
            elif payload.action == "hide_identical":
                await _callback_text(callback, "Одинаковые поля уже свернуты в summary-сравнении. В приложении можно раскрыть raw evidence.")
            elif payload.action == "add_third":
                await _callback_text(callback, "Напишите код или название третьей программы, и я добавлю её в сравнение.")
            else:
                await _callback_text(callback, "Действие пока недоступно для этого снимка данных.")
        except BackendError as error:
            if error.status_code == 409:
                await _callback_text(callback, texts.STALE)
            else:
                await _callback_text(callback, texts.SOURCE_GAP)
        except (BackendTransportError, RenderError):
            await _callback_text(callback, texts.SOURCE_GAP)

    async def _details(self, message: Message, owner: str, program_id: str) -> None:
        cookie = self._sessions.get_cookie(owner)
        program = await self._backend.get_program(program_id, session_cookie=cookie)
        self._remember(owner, program.session_cookie)
        image = await self._renderer.render("program", {"ids": program_id, "theme": "light"}, session_cookie=self._sessions.get_cookie(owner))
        await _photo(message, image, "Карточка программы.", keyboards.program_actions(owner, program_id, self._callbacks))

    async def _render_assistant_envelope(self, envelope: object, owner: str) -> bytes | None:
        data = getattr(envelope, "data", {})
        rows = data.get("rows", []) if isinstance(data, dict) else []
        ids = tuple(
            program_id
            for row in rows
            if isinstance(row, dict)
            for program_id in (row.get("entity_id"), *row.get("program_ids", ()))
            if isinstance(program_id, str)
        )[:3]
        template = getattr(envelope, "template", "")
        analytics_templates = {"metric-comparison", "metric-cards", "analytics-report", "analytics-explorer"}
        if template in analytics_templates:
            if not ids:
                return None
            metric = next(
                (
                    str(code)
                    for row in rows
                    if isinstance(row, dict)
                    for metrics in (row.get("metrics", {}),)
                    if isinstance(metrics, dict)
                    for code in metrics
                ),
                "math_share",
            )
            return await self._renderer.render(
                "analytics",
                {"ids": ",".join(dict.fromkeys(ids)), "metric": metric, "theme": "light"},
                session_cookie=self._sessions.get_cookie(owner),
            )
        if len(ids) < 2:
            return None
        return await self._renderer.render(
            "compare",
            {"ids": ",".join(dict.fromkeys(ids)), "theme": "light"},
            session_cookie=self._sessions.get_cookie(owner),
        )

    async def _render_template(self, message: Message, owner: str, action: str, program_ids: tuple[str, ...]) -> None:
        template = "curriculum" if action == "curriculum" else "radar"
        image = await self._renderer.render(template, {"ids": ",".join(program_ids), "theme": "light"}, session_cookie=self._sessions.get_cookie(owner))
        await _photo(message, image, "Визуализация evidence учебных планов.", keyboards.image_actions(owner, program_ids, self._callbacks, self._settings.web_app_url))

    async def _add_shortlist(self, message: Message, owner: str, program_id: str) -> None:
        cookie = self._sessions.get_cookie(owner)
        suggestions = await self._backend.get_suggestions(session_cookie=cookie)
        self._remember(owner, suggestions.session_cookie)
        mutation = await self._backend.add_shortlist(program_id, suggestions.value.context_revision, session_cookie=self._sessions.get_cookie(owner))
        self._remember(owner, mutation.session_cookie)
        await message.answer("Программа добавлена в shortlist. Я не удаляю сохранённые варианты автоматически.")

    async def _refinement(self, message: Message, owner: str, payload: CallbackPayload) -> None:
        result = await self._backend.answer_refinement(payload.question_id or "", payload.option_id or "", payload.revision or 0, session_cookie=self._sessions.get_cookie(owner))
        self._remember(owner, result.session_cookie)
        await message.answer("Профиль уточнён; shortlist сохранён, пересчитаны только предложения.")
        await self._maybe_refinement(message, owner, result.value.suggestions)

    async def _maybe_refinement(self, message: Message, owner: str, suggestions: object) -> None:
        question = getattr(suggestions, "refinement_question", None)
        if question is None:
            return
        context = await self._backend.get_context(session_cookie=self._sessions.get_cookie(owner))
        self._remember(owner, context.session_cookie)
        revision = context.value.profile_revision
        if revision is None:
            return
        options = tuple((item.id, item.label) for item in question.options)
        await message.answer(
            question.prompt,
            reply_markup=keyboards.refinement_choices(owner, question.id, revision, options, self._callbacks),
        )

    def _remember(self, owner: str, cookie: str | None) -> None:
        if cookie:
            self._sessions.save_cookie(owner, cookie)


async def _photo(message: Message, content: bytes, caption: str, markup: InlineKeyboardMarkup | None = None) -> None:
    await message.answer_photo(BufferedInputFile(content, filename="andromeda.png"), caption=caption, reply_markup=markup)


async def _callback_text(callback: CallbackQuery, value: str) -> None:
    if callback.message is not None:
        await callback.message.answer(value)


def _owner_key(value: Message | CallbackQuery) -> str:
    user = value.from_user
    if user is None:
        raise ValueError("Telegram update has no sender")
    return f"telegram:{user.id}"


def _assistant_question(value: object) -> str:
    question = getattr(value, "question", None) or "Уточните запрос."
    options = tuple(getattr(value, "options", ()))
    if not options:
        return question
    return f"{question}\n\n" + "\n".join(f"• {option}" for option in options)


__all__ = ["TelegramFlows"]
