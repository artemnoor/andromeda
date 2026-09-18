from __future__ import annotations

import pytest

from andromeda_telegram.parsing.admission_input import parse_exam_scores


def test_admission_input_is_bounded_and_does_not_invent_missing_subjects() -> None:
    assert parse_exam_scores("математика=90, русский=85") == [
        {"subject": "математика", "score": 90},
        {"subject": "русский", "score": 85},
    ]
    with pytest.raises(ValueError):
        parse_exam_scores("математика=101")


def test_admission_input_rejects_free_form_unparseable_text() -> None:
    with pytest.raises(ValueError):
        parse_exam_scores("у меня хорошие баллы")
