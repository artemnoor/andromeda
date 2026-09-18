"""Aiogram router with thin command/callback dispatch."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from .protocols import BotFlow


def create_router(flow: BotFlow) -> Router:
    router = Router(name="andromeda-telegram")

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await flow.start(message)

    @router.message(Command("catalog"))
    async def catalog(message: Message) -> None:
        await flow.catalog(message)

    @router.message(Command("compare"))
    async def compare(message: Message) -> None:
        await flow.compare(message, (message.text or "").removeprefix("/compare").strip())

    @router.message(Command("shortlist"))
    async def shortlist(message: Message) -> None:
        await flow.shortlist(message)

    @router.message(Command("admission"))
    async def admission(message: Message) -> None:
        await flow.admission(message, (message.text or "").removeprefix("/admission").strip())

    @router.message(Command("digest"))
    async def digest(message: Message) -> None:
        await flow.digest(message)

    @router.message()
    async def natural_language(message: Message) -> None:
        value = (message.text or "").strip()
        if value.casefold().startswith(("сравни ", "сопоставь ")):
            await flow.compare(message, value)

    @router.callback_query()
    async def callback(query: CallbackQuery) -> None:
        if query.data:
            await flow.callback(query, query.data)

    return router


__all__ = ["create_router"]
