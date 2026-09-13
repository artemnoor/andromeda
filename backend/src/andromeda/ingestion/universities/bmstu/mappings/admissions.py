from __future__ import annotations

import re

from andromeda.modules.admissions.contracts.public import FundingType, PassingScoreType, QuotaType, StudyForm


def normalize_study_form(value: str | None) -> StudyForm | None:
    if not value:
        return None
    text = " ".join(value.casefold().replace("ё", "е").split())
    if "очно" in text:
        return StudyForm.FULL_TIME
    if "заочно" in text:
        return StudyForm.PART_TIME
    if "очно-заочно" in text or "вечер" in text:
        return StudyForm.EVENING
    if "дистан" in text or "онлайн" in text:
        return StudyForm.ONLINE
    return None


def normalize_funding(value: str | None) -> FundingType | None:
    if not value:
        return None
    text = value.casefold()
    if "бюдж" in text or "кцп" in text or text == FundingType.BUDGET.value:
        return FundingType.BUDGET
    if "плат" in text or "контракт" in text or text == FundingType.PAID.value:
        return FundingType.PAID
    if "целев" in text or text == FundingType.TARGETED.value:
        return FundingType.TARGETED
    return None


def normalize_quota(value: str) -> QuotaType:
    text = value.casefold().replace("ё", "е")
    if "отдель" in text:
        return QuotaType.SEPARATE
    if "особ" in text or "спец" in text:
        return QuotaType.SPECIAL
    if "целев" in text:
        return QuotaType.TARGETED
    return QuotaType.OTHER


def normalize_passing_score(value: str) -> PassingScoreType:
    text = value.casefold().replace("ё", "е")
    if "бюдж" in text or text == PassingScoreType.BUDGET.value:
        return PassingScoreType.BUDGET
    if "плат" in text or "контракт" in text or text == PassingScoreType.PAID.value:
        return PassingScoreType.PAID
    if "сред" in text or text == PassingScoreType.AVERAGE.value:
        return PassingScoreType.AVERAGE
    return PassingScoreType.OTHER


def normalize_currency(value: str) -> str:
    text = value.strip()
    return "RUB" if text in {"₽", "руб", "руб.", "р"} else text.upper()


def normalize_code(value: str) -> str:
    return re.sub(r"\s+", "", value.replace("–", "-").replace("—", "-"))


__all__ = [
    "normalize_code",
    "normalize_currency",
    "normalize_funding",
    "normalize_passing_score",
    "normalize_quota",
    "normalize_study_form",
]
