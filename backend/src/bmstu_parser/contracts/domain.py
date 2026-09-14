"""Legacy import facade for canonical Andromeda domain contracts.

New code must import subject contracts from ``andromeda.modules``. Keeping
these aliases avoids a second schema copy while old tracer entrypoints are
migrated.
"""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from andromeda.modules.comparison.domain.entities import Workload as CompareWorkload
from andromeda.modules.curricula.contracts.public import Curriculum, CurriculumItem
from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.programs.contracts.public import Program
from andromeda.modules.universities.contracts.public import Direction, University
from andromeda.shared.contracts.base import ContractModel
from andromeda.shared.contracts.provenance import SourceAttribution
from bmstu_parser.contracts.raw import RawSourceGap


EducationalProgram = Program


class NormalizedTracerSnapshot(ContractModel):
    """Temporary legacy aggregate composed from canonical module contracts."""

    university: University
    direction: Direction
    programs: tuple[Program, ...] = Field(min_length=1)
    disciplines: tuple[Discipline, ...] = Field(min_length=1)
    curricula: tuple[Curriculum, ...] = ()
    sources: tuple[SourceAttribution, ...] = Field(min_length=1)
    directions: tuple[Direction, ...] = ()
    source_gaps: tuple[RawSourceGap, ...] = ()

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        all_directions = self.directions or (self.direction,)
        if any(direction.university_id != self.university.id for direction in all_directions):
            raise ValueError("direction university foreign key does not resolve")
        if len({direction.id for direction in all_directions}) != len(all_directions):
            raise ValueError("direction ids must be unique")
        programs_by_id = {program.id: program for program in self.programs}
        if len(programs_by_id) != len(self.programs):
            raise ValueError("program ids must be unique")
        disciplines_by_id = {discipline.id: discipline for discipline in self.disciplines}
        if len(disciplines_by_id) != len(self.disciplines):
            raise ValueError("discipline ids must be unique")
        for program in self.programs:
            if program.direction_id not in {direction.id for direction in all_directions}:
                raise ValueError("program direction foreign key does not resolve")
        curriculum_programs = {curriculum.program_id for curriculum in self.curricula}
        gap_programs = {gap.entity_key for gap in self.source_gaps if gap.entity_type == "program"}
        if curriculum_programs | gap_programs != set(programs_by_id):
            raise ValueError("every selected program must have a curriculum or source gap")
        if curriculum_programs & gap_programs:
            raise ValueError("program cannot have both curriculum and source gap")
        for curriculum in self.curricula:
            for item in curriculum.items:
                if item.discipline_id not in disciplines_by_id:
                    raise ValueError("curriculum item discipline foreign key does not resolve")
        return self


__all__ = [
    "CompareWorkload",
    "Curriculum",
    "CurriculumItem",
    "Direction",
    "Discipline",
    "EducationalProgram",
    "NormalizedTracerSnapshot",
    "SourceAttribution",
    "University",
]
