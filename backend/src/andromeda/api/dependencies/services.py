from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from andromeda.modules.comparison.services.compare_programs import CompareProgramsService
from andromeda.modules.curricula.repository.ports import CurriculumReader
from andromeda.modules.disciplines.repository.ports import DisciplineReader
from andromeda.modules.programs.repository.ports import ProgramReader
from andromeda.modules.proftest.repository.ports import ProftestCatalogReader
from andromeda.modules.proftest.services.catalog import ProftestCatalogService
from andromeda.modules.proftest.services.proftest import ProftestService
from andromeda.modules.recommendations.services.recommendations import RecommendationService

from andromeda.infrastructure.repositories.curricula import SqlAlchemyCurriculumRepository
from andromeda.infrastructure.repositories.disciplines import SqlAlchemyDisciplineRepository
from andromeda.infrastructure.repositories.programs import SqlAlchemyProgramRepository
from andromeda.infrastructure.repositories.proftest import SqlAlchemyProftestCatalogRepository
from andromeda.infrastructure.repositories.recommendations import CatalogRecommendationRepository
from .request_context import get_session


def get_program_reader(session: Session = Depends(get_session)) -> ProgramReader:
    return SqlAlchemyProgramRepository(session)


def get_curriculum_reader(session: Session = Depends(get_session)) -> CurriculumReader:
    return SqlAlchemyCurriculumRepository(session)


def get_discipline_reader(session: Session = Depends(get_session)) -> DisciplineReader:
    return SqlAlchemyDisciplineRepository(session)


def get_compare_service(
    programs: ProgramReader = Depends(get_program_reader),
    curricula: CurriculumReader = Depends(get_curriculum_reader),
    disciplines: DisciplineReader = Depends(get_discipline_reader),
) -> CompareProgramsService:
    return CompareProgramsService(programs, curricula, disciplines)


def get_proftest_catalog_reader(
    programs: ProgramReader = Depends(get_program_reader),
    curricula: CurriculumReader = Depends(get_curriculum_reader),
    disciplines: DisciplineReader = Depends(get_discipline_reader),
) -> ProftestCatalogReader:
    return SqlAlchemyProftestCatalogRepository(programs, curricula, disciplines)


def get_proftest_catalog_service(
    catalog_reader: ProftestCatalogReader = Depends(get_proftest_catalog_reader),
) -> ProftestCatalogService:
    return ProftestCatalogService(catalog_reader)


def get_recommendation_service(
    catalog: ProftestCatalogService = Depends(get_proftest_catalog_service),
) -> RecommendationService:
    return RecommendationService(CatalogRecommendationRepository(catalog))


def get_proftest_service(
    catalog: ProftestCatalogService = Depends(get_proftest_catalog_service),
    recommendations: RecommendationService = Depends(get_recommendation_service),
) -> ProftestService:
    return ProftestService(catalog, recommendations=recommendations)
