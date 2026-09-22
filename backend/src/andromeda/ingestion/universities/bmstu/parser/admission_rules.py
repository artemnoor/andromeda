"""Deterministic extraction of cross-cutting admission-rule policies."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from andromeda.ingestion.contracts.raw import RawSourceSnapshot
from andromeda.shared.contracts.base import ContractModel

from ..pdf import extract_pdf_text, is_pdf


class BmstuAdmissionRulePolicy(ContractModel):
    """Typed facts shared by olympiad rules, with source wording preserved."""

    olympiad_result_max_age_years: int | None = None
    olympiad_result_validity_text: str | None = None
    olympiad_confirmation_min_score: Decimal | None = None
    olympiad_confirmation_text: str | None = None


def parse_admission_rule_policy(snapshot: RawSourceSnapshot) -> BmstuAdmissionRulePolicy | None:
    """Parse policy facts from the official 2026 Rules snapshot.

    Fixture extracts are accepted only when they carry explicitly extracted
    fields.  Live PDFs are read through the existing bounded PDF text policy;
    no legal defaults are applied when the source wording is absent.
    """

    payload = _json_payload(snapshot.body)
    if payload is not None:
        return _from_json(payload)
    if not is_pdf(snapshot.body, snapshot.content_type, str(snapshot.requested_url)):
        return None
    text = extract_pdf_text(snapshot.body)
    if not text:
        return None
    compact = _compact(text)
    age_match = re.search(r"втечение(?:четырех|4)лет", compact)
    score_match = re.search(r"нениже(\d{2,3})балл", compact)
    if age_match is None and score_match is None:
        return None
    score = None
    if score_match is not None:
        try:
            score = Decimal(score_match.group(1))
        except InvalidOperation:
            score = None
    return BmstuAdmissionRulePolicy(
        olympiad_result_max_age_years=4 if age_match is not None else None,
        olympiad_result_validity_text=(
            "Результаты олимпиады действительны с момента их получения и в течение четырех лет, следующих за годом проведения олимпиады."
            if age_match is not None
            else None
        ),
        olympiad_confirmation_min_score=score,
        olympiad_confirmation_text=(
            "Для особого права требуется результат ЕГЭ или внутреннего испытания по соответствующему предмету не ниже 75 баллов."
            if score is not None
            else None
        ),
    )


def _json_payload(body: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return cast(dict[str, Any], value) if isinstance(value, dict) else None


def _from_json(payload: dict[str, Any]) -> BmstuAdmissionRulePolicy | None:
    raw_age = payload.get("olympiad_result_max_age_years")
    raw_score = payload.get("olympiad_confirmation_min_score")
    age = raw_age if isinstance(raw_age, int) and raw_age >= 0 else None
    score: Decimal | None = None
    if isinstance(raw_score, (int, str)) and not isinstance(raw_score, bool):
        try:
            score = Decimal(str(raw_score))
        except InvalidOperation:
            score = None
    if age is None and score is None:
        return None
    validity_text = payload.get("olympiad_result_validity_text")
    confirmation_text = payload.get("olympiad_confirmation_text")
    return BmstuAdmissionRulePolicy(
        olympiad_result_max_age_years=age,
        olympiad_result_validity_text=validity_text if isinstance(validity_text, str) and validity_text.strip() else None,
        olympiad_confirmation_min_score=score,
        olympiad_confirmation_text=confirmation_text if isinstance(confirmation_text, str) and confirmation_text.strip() else None,
    )


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value.casefold().replace("ё", "е"))


__all__ = ["BmstuAdmissionRulePolicy", "parse_admission_rule_policy"]
