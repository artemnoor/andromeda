"""Public contracts and ports for entity resolution."""

from .ports import (
    DirectionResolver,
    DisciplineResolver,
    MetricResolver,
    ProgramResolver,
    UniversityResolver,
)
from .public import (
    CandidateMatchReason,
    EntityResolutionCandidate,
    EntityResolutionResult,
    ResolutionContext,
    ResolutionEntityType,
    ResolutionStatus,
)

__all__ = [
    "CandidateMatchReason",
    "DirectionResolver",
    "DisciplineResolver",
    "EntityResolutionCandidate",
    "EntityResolutionResult",
    "MetricResolver",
    "ProgramResolver",
    "ResolutionContext",
    "ResolutionEntityType",
    "ResolutionStatus",
    "UniversityResolver",
]
