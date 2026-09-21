"""Transport-neutral adapter contracts for Web, Telegram and future MAX."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import Field

from andromeda.shared.contracts.base import ContractModel

from .envelope import ResponseEnvelope
from .policy import PresentationCapabilities


class ChannelKind(StrEnum):
    WEB = "web"
    TELEGRAM = "telegram"
    MAX = "max"


class TransportInput(ContractModel):
    channel: ChannelKind
    external_session_id: str = Field(min_length=1, max_length=256)
    text: str = Field(min_length=1, max_length=2000)
    callback_data: str | None = Field(default=None, max_length=512)
    capabilities: PresentationCapabilities = PresentationCapabilities()


class TransportOutput(ContractModel):
    response: ResponseEnvelope
    external_session_id: str = Field(min_length=1, max_length=256)


class ChannelAdapterPort(Protocol):
    def handle(self, input: TransportInput) -> TransportOutput: ...


__all__ = ["ChannelAdapterPort", "ChannelKind", "TransportInput", "TransportOutput"]
