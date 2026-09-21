"""Small deterministic parser for the acceptance corpus.

This parser produces partial typed facts. Entity IDs are resolved later by the
backend entity-resolution ports; no natural-language text becomes SQL.
"""

from __future__ import annotations

import re
from decimal import Decimal

from andromeda.modules.analytics.contracts.metrics import MetricAggregation
from andromeda.modules.analytics.contracts.query import QueryScope

from ..contracts.public import ConversationIntent, ExamScore, ParsedQuery

_METRIC_ALIASES = {
    "математик": "math_share",
    "математике": "math_share",
    "математики": "math_share",
    "матан": "math_share",
    "программирован": "programming_share",
    "кодинг": "programming_share",
    "искусственн интеллект": "ai_share",
    "машинн обучен": "ai_share",
    "физик": "physics_share",
    "бизнес": "business_share",
    "аналитик": "analytics_share",
}
_SUBJECT_ALIASES = (
    ("русский", "русский язык"),
    ("математика", "математика"),
    ("информатика", "информатика"),
    ("физика", "физика"),
    ("обществознание", "обществознание"),
    ("английский", "английский язык"),
    ("история", "история"),
    ("химия", "химия"),
    ("биология", "биология"),
    ("литература", "литература"),
    ("география", "география"),
)


class RuleBasedQueryParser:
    version = "conversation-parser.v1"

    def parse(self, text: str) -> ParsedQuery:
        if not text or not text.strip():
            return ParsedQuery(unresolved_text="")
        normalized = text.casefold().replace("ё", "е")
        exam_scores = _parse_exam_scores(normalized)
        total_score = _parse_total_score(normalized)
        metric_codes = _parse_metrics(normalized)
        if exam_scores and not any(marker in normalized for marker in ("где больше", "где меньше", "сравни", "по математике")):
            metric_codes = ()
        university_queries, direction_queries, program_queries = _parse_canonical_entities(normalized)
        intent = _parse_intent(normalized, total_score, exam_scores, metric_codes)
        aggregation = MetricAggregation.MEAN if "в среднем" in normalized else None
        scope = QueryScope.UNIVERSITY if "вуз" in normalized or "университет" in normalized else None
        return ParsedQuery(
            intent=intent,
            metric_codes=metric_codes,
            university_queries=university_queries,
            direction_queries=direction_queries,
            program_queries=program_queries,
            total_score=total_score,
            exam_scores=exam_scores,
            aggregation=aggregation,
            scope=scope,
            unresolved_text=text.strip(),
        )


def _parse_intent(text: str, total_score: Decimal | None, exam_scores: tuple[ExamScore, ...], metrics: tuple[str, ...]) -> ConversationIntent:
    admission_words = ("куда", "прохожу", "поступить", "егэ", "бюджет", "проходной")
    compare_words = ("сравни", "сравнить", "между", " vs ", "versus")
    if total_score is not None or exam_scores or any(word in text for word in admission_words):
        return ConversationIntent.ADMISSION_SEARCH
    if any(word in text for word in compare_words):
        return ConversationIntent.COMPARE_PROGRAMS
    if metrics or any(word in text for word in ("где больше", "где меньше", "топ", "покажи программы")):
        return ConversationIntent.ANALYTICS_QUERY
    return ConversationIntent.UNKNOWN


def _parse_total_score(text: str) -> Decimal | None:
    match = re.search(r"\b(?:с|набра(?:л|ла|ли))\s*(\d{2,3})\b", text)
    return Decimal(match.group(1)) if match else None


def _parse_exam_scores(text: str) -> tuple[ExamScore, ...]:
    scores: list[ExamScore] = []
    for alias, subject in _SUBJECT_ALIASES:
        match = re.search(rf"\b{re.escape(alias)}\b\s*(?:егэ\s*)?(?:[:=-]\s*|\s+)(\d{{1,3}})\b", text)
        if match:
            score = Decimal(match.group(1))
            if score <= Decimal(100):
                scores.append(ExamScore(subject=subject, score=score))
    return tuple(scores)


def _parse_metrics(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(code for alias, code in _METRIC_ALIASES.items() if alias in text))


def _parse_canonical_entities(text: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    universities = tuple(dict.fromkeys(re.findall(r"\buniversity:[a-z0-9-]+\b", text)))
    directions = tuple(dict.fromkeys(re.findall(r"\bdirection:[a-z0-9-]+:[0-9]{2}\.[0-9]{2}\.[0-9]{2}\b", text)))
    programs = tuple(dict.fromkeys(re.findall(r"\bprogram:[a-z0-9-]+:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}\b", text)))
    return universities, directions, programs


__all__ = ["RuleBasedQueryParser"]
