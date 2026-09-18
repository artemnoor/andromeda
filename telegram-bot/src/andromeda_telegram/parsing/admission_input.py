"""Bounded parsing for an explicit Telegram admission command."""

from __future__ import annotations

import re


def parse_exam_scores(value: str) -> list[dict[str, str | int]]:
    pairs = re.findall(r"([^,;=]+?)\s*=\s*(\d{1,3})", value)
    if not pairs or len(pairs) > 12:
        raise ValueError("Укажите предметы в формате математика=90, русский=85")
    scores: list[dict[str, str | int]] = []
    for subject, raw_score in pairs:
        clean_subject = " ".join(subject.split())[:128]
        score = int(raw_score)
        if not clean_subject or not 0 <= score <= 100:
            raise ValueError("Баллы должны быть от 0 до 100")
        scores.append({"subject": clean_subject, "score": score})
    return scores


__all__ = ["parse_exam_scores"]
