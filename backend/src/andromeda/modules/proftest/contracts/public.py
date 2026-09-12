"""Stable public contracts of the proftest module."""

from ..domain.entities import (
    ActivityCode,
    AdaptiveAnswer,
    Answer,
    AnswerSet,
    AntiInterest,
    Confidence,
    CurriculumEvidence,
    DistinctiveSubject,
    ProgramFingerprint,
    Question,
    QuestionBlock,
    QuestionOption,
    UserProfile,
)
from ..domain.profile import ProfileScope, UserProfileSnapshot
from ..domain.adaptive import AdaptiveDimension, AdaptiveSelection, AdaptiveStatus
from ..domain.questions import Questionnaire
from ..domain.results import MatchReason, MatchScore, MetricStatus, OptionalMetric, PreviewCandidate, ProftestPreview, ProftestResults, ReasonKind, Recommendation, ScoreBreakdown
from ..repository.ports import CurrentUserProfileReader

__all__ = [
    "ActivityCode",
    "AdaptiveDimension",
    "AdaptiveAnswer",
    "AdaptiveSelection",
    "AdaptiveStatus",
    "Answer",
    "AnswerSet",
    "AntiInterest",
    "Confidence",
    "CurriculumEvidence",
    "DistinctiveSubject",
    "MatchReason",
    "MatchScore",
    "MetricStatus",
    "OptionalMetric",
    "PreviewCandidate",
    "ProgramFingerprint",
    "ProftestPreview",
    "ProftestResults",
    "Question",
    "QuestionBlock",
    "QuestionOption",
    "Questionnaire",
    "ReasonKind",
    "Recommendation",
    "CurrentUserProfileReader",
    "ProfileScope",
    "ScoreBreakdown",
    "UserProfile",
    "UserProfileSnapshot",
]
