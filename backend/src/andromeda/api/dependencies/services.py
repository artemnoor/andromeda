from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from andromeda.modules.admission_fit.repository.ports import AdmissionFitDataReader
from andromeda.modules.admission_fit.services.admission_fit import AdmissionFitService
from andromeda.modules.comparison.services.compare_programs import CompareProgramsService
from andromeda.modules.admissions.repository.ports import AdmissionReader
from andromeda.modules.admissions.services.admissions import AdmissionService
from andromeda.modules.curricula.repository.ports import CurriculumReader
from andromeda.modules.disciplines.repository.ports import DisciplineReader
from andromeda.modules.programs.repository.ports import ProgramReader
from andromeda.modules.proftest.repository.ports import ProftestCatalogReader, UserProfileRepository
from andromeda.modules.proftest.contracts.public import CurrentUserProfileReader
from andromeda.modules.proftest.services.catalog import ProftestCatalogService
from andromeda.modules.proftest.services.profile_persistence import UserProfilePersistenceService
from andromeda.modules.proftest.services.proftest import ProftestService
from andromeda.modules.recommendations.services.recommendations import RecommendationService
from andromeda.modules.recommendations.services.current import CurrentRecommendationService

from andromeda.infrastructure.repositories.curricula import SqlAlchemyCurriculumRepository
from andromeda.infrastructure.repositories.disciplines import SqlAlchemyDisciplineRepository
from andromeda.infrastructure.repositories.admissions import SqlAlchemyAdmissionRepository
from andromeda.infrastructure.repositories.admission_fit import SqlAlchemyAdmissionFitReader
from andromeda.infrastructure.repositories.programs import SqlAlchemyProgramRepository
from andromeda.infrastructure.repositories.proftest import SqlAlchemyProftestCatalogRepository
from andromeda.infrastructure.repositories.recommendations import CatalogRecommendationRepository
from andromeda.infrastructure.repositories.user_profiles import SqlAlchemyUserProfileRepository
from .request_context import get_session


def get_program_reader(session: Session = Depends(get_session)) -> ProgramReader:
    return SqlAlchemyProgramRepository(session)


def get_curriculum_reader(session: Session = Depends(get_session)) -> CurriculumReader:
    return SqlAlchemyCurriculumRepository(session)


def get_discipline_reader(session: Session = Depends(get_session)) -> DisciplineReader:
    return SqlAlchemyDisciplineRepository(session)


def get_admission_reader(session: Session = Depends(get_session)) -> AdmissionReader:
    return SqlAlchemyAdmissionRepository(session)


def get_admission_service(
    programs: ProgramReader = Depends(get_program_reader),
    admissions: AdmissionReader = Depends(get_admission_reader),
) -> AdmissionService:
    return AdmissionService(programs, admissions)


def get_admission_fit_reader(
    programs: ProgramReader = Depends(get_program_reader),
    admissions: AdmissionReader = Depends(get_admission_reader),
) -> AdmissionFitDataReader:
    return SqlAlchemyAdmissionFitReader(programs, admissions)


def get_admission_fit_service(
    reader: AdmissionFitDataReader = Depends(get_admission_fit_reader),
) -> AdmissionFitService:
    return AdmissionFitService(reader)


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


def get_user_profile_repository(session: Session = Depends(get_session)) -> UserProfileRepository:
    return SqlAlchemyUserProfileRepository(session)


def get_profile_persistence_service(
    request: Request,
    repository: UserProfileRepository = Depends(get_user_profile_repository),
) -> UserProfilePersistenceService:
    return UserProfilePersistenceService(repository, ttl_seconds=request.app.state.settings.profile_ttl_seconds)


def get_current_user_profile_reader(
    repository: UserProfileRepository = Depends(get_user_profile_repository),
) -> CurrentUserProfileReader:
    return repository


def get_recommendation_service(
    catalog: ProftestCatalogService = Depends(get_proftest_catalog_service),
) -> RecommendationService:
    return RecommendationService(CatalogRecommendationRepository(catalog))


def get_proftest_service(
    catalog: ProftestCatalogService = Depends(get_proftest_catalog_service),
    recommendations: RecommendationService = Depends(get_recommendation_service),
    profile_persistence: UserProfilePersistenceService = Depends(get_profile_persistence_service),
) -> ProftestService:
    return ProftestService(catalog, recommendations=recommendations, profile_persistence=profile_persistence)


def get_current_recommendation_service(
    profile_reader: CurrentUserProfileReader = Depends(get_current_user_profile_reader),
    recommendations: RecommendationService = Depends(get_recommendation_service),
) -> CurrentRecommendationService:
    return CurrentRecommendationService(profile_reader, recommendations)
