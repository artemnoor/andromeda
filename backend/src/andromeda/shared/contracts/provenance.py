from __future__ import annotations

from datetime import datetime

from pydantic import Field, HttpUrl

from .base import ContractModel
from .enums import SourceKind
from .ids import ShortText


class SourceAttribution(ContractModel):
    kind: SourceKind
    url: HttpUrl
    captured_at: datetime
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    locator: ShortText | None = None
