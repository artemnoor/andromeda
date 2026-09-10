from __future__ import annotations

from ....shared.contracts.base import ContractModel
from ....shared.contracts.enums import AssessmentType
from ....shared.contracts.ids import Credits, HourCount, Semester, ShortText


class Workload(ContractModel):
    semester: Semester | None = None
    hours: HourCount
    credits: Credits | None = None
    assessment_types: tuple[AssessmentType, ...] | None = None
    subject_group: ShortText | None = None


__all__ = ["Workload"]
