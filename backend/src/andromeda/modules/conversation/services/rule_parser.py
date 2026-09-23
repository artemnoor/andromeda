"""Small deterministic parser for the acceptance corpus.

This parser produces partial typed facts. Entity IDs are resolved later by the
backend entity-resolution ports; no natural-language text becomes SQL.
"""

from __future__ import annotations

import re
from decimal import Decimal

from andromeda.modules.admissions.contracts.public import FundingType, StudyForm
from andromeda.modules.analytics.contracts.metrics import MetricAggregation
from andromeda.modules.analytics.contracts.query import QueryScope
from andromeda.shared.contracts.errors import ContractError, ErrorCode

from ..contracts.public import (
    AdmissionUniversityScope,
    ConversationIntent,
    ExamScore,
    ParsedQuery,
)

_METRIC_ALIASES = {
    "математик": "math_share",
    "математическая нагрузка": "math_share",
    "математике": "math_share",
    "математики": "math_share",
    "матан": "math_share",
    "программирован": "programming_share",
    "кодинг": "programming_share",
    "искусственн интеллект": "ai_share",
    "машинн обучен": "ai_share",
    "искусственный интеллект": "ai_share",
    "машинное обучение": "ai_share",
    "ai": "ai_share",
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
    version = "conversation-parser.v3"
    max_input_length = 2000

    def parse(self, text: str) -> ParsedQuery:
        if not isinstance(text, str):
            raise ContractError(ErrorCode.INVALID_QUERY, "Query text must be a string")
        if len(text) > self.max_input_length:
            raise ContractError(ErrorCode.INVALID_QUERY, "Query text exceeds the supported size")
        if any(ord(character) < 32 and character not in "\t\n\r" for character in text):
            raise ContractError(ErrorCode.INVALID_QUERY, "Query text contains unsupported control characters")
        cleaned = " ".join(text.split())
        if not cleaned:
            return ParsedQuery(unresolved_text="")
        normalized = cleaned.casefold().replace("ё", "е")
        exam_scores = _parse_exam_scores(normalized)
        total_score = _parse_total_score(normalized)
        metric_codes = _parse_metrics(normalized)
        if exam_scores and not any(marker in normalized for marker in ("где больше", "где меньше", "сравни", "по математике")):
            metric_codes = ()
        university_queries, direction_queries, program_queries = _parse_canonical_entities(normalized)
        funding_type = _parse_funding_type(normalized)
        study_form, study_form_ambiguous = _parse_study_form(normalized)
        admission_year = _parse_admission_year(normalized)
        intent = _parse_intent(
            normalized,
            total_score,
            exam_scores,
            metric_codes,
            funding_type,
            study_form,
            admission_year,
        )
        aggregation = MetricAggregation.MEAN if "в среднем" in normalized else None
        scope = QueryScope.UNIVERSITY if "вуз" in normalized or "университет" in normalized else None
        return ParsedQuery(
            intent=intent,
            admission_university_scope=_parse_admission_university_scope(normalized),
            metric_codes=metric_codes,
            university_queries=university_queries,
            direction_queries=direction_queries,
            program_queries=program_queries,
            total_score=total_score,
            exam_scores=exam_scores,
            funding_type=funding_type,
            study_form=study_form,
            study_form_ambiguous=study_form_ambiguous,
            admission_year=admission_year,
            aggregation=aggregation,
            scope=scope,
            semester=_parse_semester(normalized),
            course_year=_parse_course_year(normalized),
            unresolved_text=cleaned[:1000],
        )


def _parse_admission_university_scope(text: str) -> AdmissionUniversityScope | None:
    any_university_phrases = (
        "любые вузы",
        "любой вуз",
        "по всем вузам",
        "все вузы",
        "в любом вузе",
        "любые университеты",
        "любой университет",
        "все университеты",
        "в любом университете",
    )
    return (
        AdmissionUniversityScope.ANY_UNIVERSITY
        if any(phrase in text for phrase in any_university_phrases)
        else None
    )


def _parse_intent(
    text: str,
    total_score: Decimal | None,
    exam_scores: tuple[ExamScore, ...],
    metrics: tuple[str, ...],
    funding_type: FundingType | None,
    study_form: StudyForm | None,
    admission_year: int | None,
) -> ConversationIntent:
    admission_words = ("куда", "прохожу", "поступ", "егэ", "бюджет", "платн", "проходной")
    compare_words = ("сравни", "сравнить", "между", " vs ", "versus")
    if (
        total_score is not None
        or exam_scores
        or funding_type is not None
        or study_form is not None
        or admission_year is not None
        or any(word in text for word in admission_words)
    ):
        return ConversationIntent.ADMISSION_SEARCH
    if any(word in text for word in compare_words):
        return ConversationIntent.COMPARE_PROGRAMS
    if metrics or any(word in text for word in ("где больше", "где меньше", "топ", "покажи программы")):
        return ConversationIntent.ANALYTICS_QUERY
    return ConversationIntent.UNKNOWN


def _parse_funding_type(text: str) -> FundingType | None:
    budget = bool(re.search(r"\bбюджет\w*\b", text))
    paid = bool(re.search(r"\b(?:платн\w*|коммерческ\w*|за деньги)\b", text))
    if budget == paid:
        return None
    return FundingType.BUDGET if budget else FundingType.PAID


def _parse_study_form(text: str) -> tuple[StudyForm | None, bool]:
    matches: set[StudyForm] = set()
    if re.search(r"\b(?:очн\w*|дневн\w*)\b", text):
        matches.add(StudyForm.FULL_TIME)
    if re.search(r"\bзаочн\w*\b", text):
        matches.add(StudyForm.PART_TIME)
    if re.search(r"\bвечерн\w*\b", text):
        matches.add(StudyForm.EVENING)
    if re.search(r"\b(?:дистанционн\w*|онлайн)\b", text):
        matches.add(StudyForm.ONLINE)
    if len(matches) > 1:
        return None, True
    return (next(iter(matches)), False) if matches else (None, False)


def _parse_admission_year(text: str) -> int | None:
    patterns = (
        r"(?:при[её]м\w*|поступлен\w*|кампан\w*|набор\w*)\s*(?:на|в)?\s*(20\d{2})",
        r"\b(?:на|в)\s*(20\d{2})\s*(?:году|год|г\.)",
    )
    years = {int(match) for pattern in patterns for match in re.findall(pattern, text)}
    return next(iter(years)) if len(years) == 1 else None


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
    universities = list(re.findall(r"\buniversity:[a-z0-9-]+\b", text))
    if "бауман" in text:
        universities.append("бауманка")
    universities.extend(alias for alias in ("мгту", "вшэ", "hse", "мифи") if alias in text)
    universities = list(dict.fromkeys(universities))
    directions = list(re.findall(r"\bdirection:[a-z0-9-]+:[0-9]{2}\.[0-9]{2}\.[0-9]{2}\b", text))
    directions.extend(code for code in re.findall(r"\b[0-9]{2}\.[0-9]{2}\.[0-9]{2}\b", text))
    if "прикладн" in text and "информат" in text:
        directions.append("прикладная информатика")
    if "вычислительн" in text and "техник" in text:
        directions.append("информатика и вычислительная техника")
    directions = list(dict.fromkeys(directions))
    programs = tuple(dict.fromkeys(re.findall(r"\bprogram:[a-z0-9-]+:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}\b", text)))
    return tuple(universities), tuple(directions), programs


def _parse_semester(text: str) -> int | None:
    match = re.search(r"\b(?:семестр|семестре|семестра)\s*(?:№\s*)?(1[0-2]|[1-9])\b", text)
    return int(match.group(1)) if match else None


def _parse_course_year(text: str) -> int | None:
    match = re.search(r"\b(?:курс|курсе|курса)\s*(1[0-2]|[1-9])\b|\b(1[0-2]|[1-9])\s*(?:курс|курсе|курса)\b", text)
    if not match:
        return None
    value = match.group(1) or match.group(2)
    return int(value)


__all__ = ["RuleBasedQueryParser"]
