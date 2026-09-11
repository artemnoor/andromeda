from __future__ import annotations

from pydantic import Field

from ...modules.curricula.contracts.public import Curriculum
from ...modules.disciplines.contracts.public import Discipline
from ...modules.programs.contracts.public import Program
from ...modules.admissions.contracts.public import ProgramAdmissions
from ...modules.universities.contracts.public import Direction, University
from ...shared.contracts.base import ContractModel
from ...shared.contracts.provenance import SourceAttribution


class CanonicalSnapshot(ContractModel):
    """Canonical graph emitted by an ingestion adapter."""

    university: University
    direction: Direction
    programs: tuple[Program, ...] = Field(min_length=1)
    disciplines: tuple[Discipline, ...] = Field(min_length=1)
    curricula: tuple[Curriculum, ...] = Field(min_length=1)
    sources: tuple[SourceAttribution, ...] = Field(min_length=1)
    admissions: tuple[ProgramAdmissions, ...] = ()
