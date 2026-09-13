"""Input contracts for Admission Fit."""

from __future__ import annotations

from typing import Literal

from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.ids import NonEmptyText

from ..domain.entities import ApplicantAdmissionProfile
from ..domain.subject_identity import normalize_subject_name


class AdmissionFitRequest(ContractModel):
    """Application request for one explicitly selected admission offering."""

    version: Literal[1] = 1
    offering_id: NonEmptyText
    applicant: ApplicantAdmissionProfile

    @classmethod
    def from_parts(cls, offering_id: str, applicant: ApplicantAdmissionProfile) -> "AdmissionFitRequest":
        return cls(offering_id=offering_id, applicant=applicant)


def normalized_applicant_subjects(profile: ApplicantAdmissionProfile) -> tuple[str, ...]:
    """Return canonical keys for adapter/UI diagnostics without exposing internals."""

    return tuple(normalize_subject_name(item.subject) for item in profile.scores)


__all__ = ["AdmissionFitRequest", "normalized_applicant_subjects"]
