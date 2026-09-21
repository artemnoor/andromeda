"""Transport-independent entity resolution for conversational and API clients."""

from .contracts.public import (
    CandidateMatchReason,
    EntityResolutionCandidate,
    EntityResolutionResult,
    ResolutionContext,
    ResolutionEntityType,
    ResolutionStatus,
)
from .services.resolvers import EntityResolverService

__all__ = [
    "CandidateMatchReason",
    "EntityResolutionCandidate",
    "EntityResolutionResult",
    "EntityResolverService",
    "ResolutionContext",
    "ResolutionEntityType",
    "ResolutionStatus",
]
