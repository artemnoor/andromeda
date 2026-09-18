from __future__ import annotations

from andromeda_telegram.handlers.router import create_router


class Flow:
    async def start(self, message): pass
    async def catalog(self, message): pass
    async def compare(self, message, query): pass
    async def shortlist(self, message): pass
    async def admission(self, message): pass
    async def digest(self, message): pass
    async def callback(self, callback, data): pass


def test_router_is_composed_from_flow_boundary() -> None:
    router = create_router(Flow())
    assert router.name == "andromeda-telegram"
