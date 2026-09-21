"""Presentation contracts for Telegram, MAX, Web and reports."""

from .envelope import (
    EvidenceSummary,
    ResponseAction,
    ResponseActionItem,
    ResponseEnvelope,
)
from .policy import (
    ALLOWED_RESPONSE_TEMPLATES,
    PresentationCapabilities,
    ResponseFormat,
    ResponsePlan,
    ResponsePolicyPort,
    ResponsePolicyResult,
    ResponseRequest,
)
from .report import RenderedReport, ReportFormat, ReportRendererPort, ReportSpec
from .transport import ChannelAdapterPort, ChannelKind, TransportInput, TransportOutput

__all__ = [
    "ALLOWED_RESPONSE_TEMPLATES",
    "EvidenceSummary",
    "PresentationCapabilities",
    "RenderedReport",
    "ReportFormat",
    "ReportRendererPort",
    "ReportSpec",
    "ResponseAction",
    "ResponseActionItem",
    "ResponseEnvelope",
    "ResponseFormat",
    "ResponsePlan",
    "ResponsePolicyPort",
    "ResponsePolicyResult",
    "ResponseRequest",
    "ChannelAdapterPort",
    "ChannelKind",
    "TransportInput",
    "TransportOutput",
]
