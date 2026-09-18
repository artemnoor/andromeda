from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from andromeda_telegram.clients.backend import BackendResult
from andromeda_telegram.clients.models import DecisionSuggestions, Program, ProgramList
from andromeda_telegram.config import Settings
from andromeda_telegram.flows.telegram import TelegramFlows
from andromeda_telegram.parsing.program_resolver import ProgramResolver
from andromeda_telegram.render.client import RendererClient
from andromeda_telegram.state.callbacks import CallbackStore
from andromeda_telegram.state.repository import SessionRepository


class Backend:
    def __init__(self) -> None:
        self.programs = [
            Program(id="program:01", directionId="direction:01", code="01", name="ПМИ МГУ", educationYear=2026, studyPlanUrl="https://example.test/a", sourceUrl="https://example.test/a"),
            Program(id="program:02", directionId="direction:01", code="02", name="ПМИ ВШЭ", educationYear=2026, studyPlanUrl="https://example.test/b", sourceUrl="https://example.test/b"),
        ]

    async def list_programs(self, *, session_cookie=None):
        return BackendResult(ProgramList(items=self.programs), None)

    async def get_suggestions(self, *, session_cookie=None):
        return BackendResult(DecisionSuggestions(decisionId="decision:" + "a" * 32, contextRevision=1), None)


class Renderer:
    async def render(self, template, params, *, session_cookie=None, revision="0"):
        assert template == "compare"
        return b"\x89PNG\r\n\x1a\ncompare"


class User:
    id = 42


class Message:
    from_user = User()

    def __init__(self) -> None:
        self.photos = []
        self.texts = []

    async def answer_photo(self, photo, caption, reply_markup=None):
        self.photos.append((photo, caption, reply_markup))

    async def answer(self, value, reply_markup=None):
        self.texts.append(value)


@pytest.mark.asyncio
async def test_compare_flow_resolves_live_programs_and_sends_png(tmp_path) -> None:
    backend = Backend()
    settings = Settings("token", "http://backend", "http://frontend", "secret", Fernet.generate_key().decode(), "http://app", tmp_path / "state.sqlite3")
    message = Message()
    flows = TelegramFlows(settings, backend, Renderer(), SessionRepository(settings.session_db, settings.session_encryption_key), ProgramResolver(backend), CallbackStore())

    await flows.compare(message, "сравни ПМИ МГУ и ПМИ ВШЭ")

    assert len(message.photos) == 1
    assert message.photos[0][0].data.startswith(b"\x89PNG")
