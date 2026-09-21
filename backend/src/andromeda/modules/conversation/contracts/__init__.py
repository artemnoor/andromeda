"""Conversation contracts and persistence ports."""

from .assistant import AssistantResult, AssistantState
from .ports import QuerySessionRepository
from .public import (
    ConversationCompilation,
    ConversationIntent,
    ConversationSlot,
    ExamScore,
    NextAction,
    ParsedQuery,
    QuerySession,
)

__all__ = [
    "AssistantResult",
    "AssistantState",
    "ConversationCompilation",
    "EvaluationCase",
    "EvaluationCaseResult",
    "EvaluationReport",
    "ConversationIntent",
    "ConversationSlot",
    "ExamScore",
    "NextAction",
    "ParsedQuery",
    "QuerySession",
    "QuerySessionRepository",
]
from .evaluation import EvaluationCase, EvaluationCaseResult, EvaluationReport
