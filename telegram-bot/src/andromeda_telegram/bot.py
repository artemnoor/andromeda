"""Aiogram composition root; handlers are attached in later flow modules."""

from __future__ import annotations

from aiogram import Bot, Dispatcher

from .clients.backend import BackendHttpClient
from .config import Settings
from .flows.telegram import TelegramFlows
from .handlers.router import create_router
from .parsing.program_resolver import ProgramResolver
from .render.client import RendererClient
from .state.callbacks import CallbackStore
from .state.repository import SessionRepository


def create_runtime(settings: Settings) -> tuple[Bot, Dispatcher, BackendHttpClient, RendererClient, SessionRepository]:
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    backend = BackendHttpClient(
        settings.backend_url,
        timeout_seconds=settings.request_timeout_seconds,
        retry_attempts=settings.request_retry_attempts,
        retry_backoff_seconds=settings.request_retry_backoff_seconds,
    )
    renderer = RendererClient(settings.renderer_url, settings.render_hmac_secret, timeout_seconds=settings.render_timeout_seconds)
    sessions = SessionRepository(settings.session_db, settings.session_encryption_key)
    resolver = ProgramResolver(backend)
    flow = TelegramFlows(settings, backend, renderer, sessions, resolver, CallbackStore())
    dispatcher.include_router(create_router(flow))
    return bot, dispatcher, backend, renderer, sessions


__all__ = ["create_runtime"]
