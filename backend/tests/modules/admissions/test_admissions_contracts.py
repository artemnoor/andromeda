from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from andromeda.modules.admissions.contracts.public import (
    AdmissionOffering,
    AdmissionProvenance,
    AdmissionScope,
    ExamRequirement,
    FundingType,
    ProgramAdmissions,
    StudyForm,
)


HASH = "a" * 64


def provenance() -> AdmissionProvenance:
    return AdmissionProvenance(
        source_kind="bmstu_major_detail",
        source_url="https://bmstu.ru/bachelor/majors/example",
        captured_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
        content_sha256=HASH,
    )


def test_admission_contract_keeps_program_identity_and_source_values() -> None:
    source = provenance()
    offering = AdmissionOffering(
        id="admission-offering:program:09.03.01-02:2026:full_time:budget:direction",
        program_id="program:09.03.01-02",
        admission_year=2026,
        study_form=StudyForm.FULL_TIME,
        funding_type=FundingType.BUDGET,
        scope=AdmissionScope.DIRECTION,
        places=318,
        exams=(
            ExamRequirement(
                subject="Математика профильная",
                source_name="Математика профильная",
                minimum_score=Decimal("46"),
                provenance=source,
            ),
        ),
        provenance=(source,),
    )
    result = ProgramAdmissions(program_id="program:09.03.01-02", offerings=(offering,))
    assert result.offerings[0].places == 318
    assert result.offerings[0].exams[0].minimum_score == Decimal("46")


def test_program_admissions_rejects_offering_for_another_program() -> None:
    source = provenance()
    offering = AdmissionOffering(
        id="admission-offering:program:09.03.01-12:2026:full_time:budget:direction",
        program_id="program:09.03.01-12",
        admission_year=2026,
        scope=AdmissionScope.DIRECTION,
        provenance=(source,),
    )
    with pytest.raises(ValidationError, match="envelope program"):
        ProgramAdmissions(program_id="program:09.03.01-02", offerings=(offering,))


def test_contract_rejects_extra_fields_and_negative_values() -> None:
    source = provenance()
    with pytest.raises(ValidationError):
        AdmissionOffering(
            id="admission-offering:program:09.03.01-02:2026:full_time:budget:direction",
            program_id="program:09.03.01-02",
            admission_year=2026,
            places=-1,
            provenance=(source,),
            unexpected=True,
        )
