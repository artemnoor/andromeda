"""Transport-independent entity resolution for conversational and API clients."""

from .contracts.public import (
    CandidateMatchReason,
    EntityResolutionCandidate,
    EntityResolutionResult,
    ResolutionContext,
    ResolutionEntityType,
    ResolutionStatus,
)

__all__ = [
    "CandidateMatchReason",
    "EntityResolutionCandidate",
    "EntityResolutionResult",
    "ResolutionContext",
    "ResolutionEntityType",
    "ResolutionStatus",
]
