from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from andromeda.infrastructure.repositories.curricula import SqlAlchemyCurriculumRepository
from andromeda.infrastructure.repositories.disciplines import SqlAlchemyDisciplineRepository
from andromeda.infrastructure.repositories.admissions import SqlAlchemyAdmissionRepository
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository
from andromeda.infrastructure.repositories.programs import SqlAlchemyProgramRepository
from andromeda.infrastructure.repositories.proftest import SqlAlchemyProftestCatalogRepository
from andromeda.infrastructure.repositories.recommendations import CatalogRecommendationRepository
from andromeda.infrastructure.repositories.universities import SqlAlchemyUniversityRepository
from andromeda.modules.proftest.services.catalog import ProftestCatalogService
from andromeda.modules.admissions.repository.ports import AdmissionReader


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

    def admission_reader(self, session: Session) -> AdmissionReader:
        return SqlAlchemyAdmissionRepository(session)

    def university_reader(self, session: Session) -> SqlAlchemyUniversityRepository:
        return SqlAlchemyUniversityRepository(session)

    def proftest_catalog_reader(self, session: Session) -> SqlAlchemyProftestCatalogRepository:
        return SqlAlchemyProftestCatalogRepository(self.program_reader(session), self.curriculum_reader(session), self.discipline_reader(session))

    def recommendation_catalog_reader(self, session: Session) -> CatalogRecommendationRepository:
        return CatalogRecommendationRepository(ProftestCatalogService(self.proftest_catalog_reader(session)))

    @property
    def ingestion(self) -> SqlAlchemyIngestionRepository:
        return SqlAlchemyIngestionRepository(self.engine)


def build_container(engine: Engine) -> AndromedaContainer:
    return AndromedaContainer(engine=engine)
