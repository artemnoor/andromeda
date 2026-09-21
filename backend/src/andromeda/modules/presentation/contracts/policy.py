"""Response selection independent of channel rendering."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import Field

from andromeda.modules.analytics.contracts.results import AnalyticsResult
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.versions import RESPONSE_POLICY_VERSION


class ResponseFormat(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    IMAGE_COLLECTION = "image_collection"
    PDF = "pdf"
    MINI_APP = "mini_app"


class PresentationCapabilities(ContractModel):
    text: bool = True
    image: bool = True
    pdf: bool = True
    mini_app: bool = False


class ResponseRequest(ContractModel):
    result: AnalyticsResult | None = None
    comparison_requested: bool = False
    report_requested: bool = False
    interactive_requested: bool = False
    evidence_requested: bool = False


class ResponsePolicyResult(ContractModel):
    response_format: ResponseFormat
    template: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=512)
    policy_version: str = RESPONSE_POLICY_VERSION


class ResponsePolicyPort(Protocol):
    def choose(
        self,
        request: ResponseRequest,
        *,
        capabilities: PresentationCapabilities | None = None,
    ) -> ResponsePolicyResult: ...


__all__ = [
    "PresentationCapabilities",
    "ResponseFormat",
    "ResponsePolicyPort",
    "ResponsePolicyResult",
    "ResponseRequest",
]
