"""Infrastructure adapter composing existing canonical module readers."""

from __future__ import annotations

from andromeda.modules.curricula.contracts.public import Curriculum
from andromeda.modules.curricula.repository.ports import CurriculumReader
from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.disciplines.repository.ports import DisciplineReader
from andromeda.modules.programs.contracts.public import Program
from andromeda.modules.programs.repository.ports import ProgramReader
from andromeda.modules.proftest.repository.ports import ProftestCatalogReader
from andromeda.shared.contracts.ids import DisciplineId, ProgramId


class SqlAlchemyProftestCatalogRepository(ProftestCatalogReader):
    """Composition adapter; SQLAlchemy stays hidden by the delegated readers."""

    def __init__(self, programs: ProgramReader, curricula: CurriculumReader, disciplines: DisciplineReader) -> None:
        self._programs = programs
        self._curricula = curricula
        self._disciplines = disciplines

    def list_programs(self) -> tuple[Program, ...]:
        return self._programs.list()

    def get_curriculum(self, program_id: ProgramId) -> Curriculum | None:
        return self._curricula.get_for_program(program_id)

    def get_discipline(self, discipline_id: DisciplineId) -> Discipline | None:
        return self._disciplines.get(discipline_id)


__all__ = ["SqlAlchemyProftestCatalogRepository"]
