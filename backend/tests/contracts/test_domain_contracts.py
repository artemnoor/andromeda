from __future__ import annotations

import pytest
from pydantic import ValidationError

from bmstu_parser.contracts.domain import CurriculumItem, Discipline, EducationalProgram


def test_domain_rejects_invalid_identity_and_numeric_ranges() -> None:
    with pytest.raises(ValidationError):
        Discipline(id="discipline:0000000000000000", name="Math", normalized_name="math")
    with pytest.raises(ValidationError):
        EducationalProgram(
            id="program:09.03.01-02",
            direction_id="direction:09.03.02",
            code="09.03.01-02",
            name="Program",
            education_year=2026,
            study_plan_url="https://example.com/plan.pdf",
            source_url="https://example.com/program",
        )
    with pytest.raises(ValidationError):
        CurriculumItem(id="item", discipline_id="discipline:0000000000000000", semester=1, hours=1, credits=61)
