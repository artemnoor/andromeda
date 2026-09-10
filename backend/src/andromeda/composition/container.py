from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from andromeda.infrastructure.repositories.curricula import SqlAlchemyCurriculumRepository
from andromeda.infrastructure.repositories.disciplines import SqlAlchemyDisciplineRepository
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository
from andromeda.infrastructure.repositories.programs import SqlAlchemyProgramRepository
from andromeda.infrastructure.repositories.universities import SqlAlchemyUniversityRepository


@dataclass(frozen=True, slots=True)
class AndromedaContainer:
    """Composition root; modules receive ports, never construct ORM objects."""

    engine: Engine

    def program_reader(self, session: Session) -> SqlAlchemyProgramRepository:
        return SqlAlchemyProgramRepository(session)

    def curriculum_reader(self, session: Session) -> SqlAlchemyCurriculumRepository:
        return SqlAlchemyCurriculumRepository(session)

    def discipline_reader(self, session: Session) -> SqlAlchemyDisciplineRepository:
        return SqlAlchemyDisciplineRepository(session)

    def university_reader(self, session: Session) -> SqlAlchemyUniversityRepository:
        return SqlAlchemyUniversityRepository(session)

    @property
    def ingestion(self) -> SqlAlchemyIngestionRepository:
        return SqlAlchemyIngestionRepository(self.engine)


def build_container(engine: Engine) -> AndromedaContainer:
    return AndromedaContainer(engine=engine)
