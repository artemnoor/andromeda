from __future__ import annotations

from andromeda.modules.admission_fit.contracts.public import BatchAdmissionFitRequest
from andromeda.modules.admission_fit.repository.ports import AdmissionFitProgramData
from andromeda.modules.admission_fit.services.admission_fit import AdmissionFitService
from andromeda.modules.admission_fit.contracts.public import AdmissionFitStatus
from andromeda.modules.admissions.contracts.public import FundingType

from .conftest import applicant, offering, program


class Reader:
    def __init__(self, snapshots: dict[str, AdmissionFitProgramData]) -> None:
        self.snapshots = snapshots

    def read(self, program_id: str) -> AdmissionFitProgramData | None:
        return self.snapshots.get(program_id)


def _snapshot(program_id: str = "program:09.03.01-02") -> AdmissionFitProgramData:
    selected = offering(program_id=program_id)
    return AdmissionFitProgramData(
        program=program(program_id),
        admissions={"program_id": program_id, "offerings": (selected,)},
    )


def test_batch_evaluation_returns_one_outcome_per_program_and_preserves_missing_source() -> None:
    present = "program:09.03.01-02"
    missing = "program:09.03.01-03"
    service = AdmissionFitService(Reader({present: _snapshot(present)}))
    result = service.evaluate_batch(
        BatchAdmissionFitRequest(
            program_ids=(present, missing),
            applicant=applicant(("Математика", "90"), ("Русский язык", "80"), ("Физика", "70")),
            funding_type=FundingType.BUDGET,
        )
    )

    assert tuple(result.by_program_id) == (present, missing)
    assert result.by_program_id[present].result is not None
    assert result.by_program_id[missing].status is AdmissionFitStatus.INSUFFICIENT_DATA
    assert result.by_program_id[missing].result is None
    assert result.by_program_id[missing].data_gaps


def test_batch_evaluation_reports_ambiguous_offerings_instead_of_picking_one() -> None:
    program_id = "program:09.03.01-02"
    first = offering(program_id=program_id)
    second = offering(program_id=program_id, funding_type=FundingType.PAID)
    snapshot = AdmissionFitProgramData(
        program=program(program_id),
        admissions={"program_id": program_id, "offerings": (first, second)},
    )
    service = AdmissionFitService(Reader({program_id: snapshot}))

    result = service.evaluate_batch(
        BatchAdmissionFitRequest(
            program_ids=(program_id,),
            applicant=applicant(("Математика", "90")),
        )
    )

    outcome = result.by_program_id[program_id]
    assert outcome.status is AdmissionFitStatus.INSUFFICIENT_DATA
    assert outcome.result is None
    assert "несколько" in outcome.data_gaps[0].message


def test_existing_one_program_evaluation_remains_available() -> None:
    from andromeda.modules.admission_fit.contracts.public import AdmissionFitRequest

    program_id = "program:09.03.01-02"
    selected = offering(program_id=program_id)
    service = AdmissionFitService(Reader({program_id: _snapshot(program_id)}))

    result = service.evaluate(
        program_id,
        AdmissionFitRequest(offering_id=selected.id, applicant=applicant(("Математика", "90"))),
    )

    assert result.program_id == program_id
    assert result.offering_id == selected.id
