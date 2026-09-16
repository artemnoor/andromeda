from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from andromeda.infrastructure.repositories.admission_fit import SqlAlchemyAdmissionFitReader
from andromeda.infrastructure.repositories.curricula import SqlAlchemyCurriculumRepository
from andromeda.infrastructure.repositories.disciplines import SqlAlchemyDisciplineRepository
from andromeda.infrastructure.repositories.admissions import SqlAlchemyAdmissionRepository
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository
from andromeda.infrastructure.repositories.programs import SqlAlchemyProgramRepository
from andromeda.infrastructure.repositories.proftest import SqlAlchemyProftestCatalogRepository
from andromeda.infrastructure.repositories.proftest_sessions import SqlAlchemyProftestSessionRepository
from andromeda.infrastructure.repositories.recommendations import CatalogRecommendationRepository
from andromeda.infrastructure.repositories.universities import SqlAlchemyUniversityRepository
from andromeda.infrastructure.repositories.user_profiles import SqlAlchemyUserProfileRepository
from andromeda.infrastructure.repositories.events import SqlAlchemyEventRepository
from andromeda.infrastructure.repositories.campus import SqlAlchemyCampusPointRepository
from andromeda.infrastructure.repositories.admin_ops import SqlAlchemyIngestionRunReader
from andromeda.infrastructure.repositories.auth import SqlAlchemyAccountRepository
from andromeda.infrastructure.security.passwords import Argon2PasswordHasher
from andromeda.modules.proftest.services.catalog import ProftestCatalogService
from andromeda.modules.admissions.repository.ports import AdmissionReader
from andromeda.modules.admission_fit.repository.ports import AdmissionFitDataReader
from andromeda.modules.events.services.events import EventService
from andromeda.modules.campus.repository.ports import CampusPointReader
from andromeda.modules.campus.services.campus import CampusService
from andromeda.modules.personal_route.services.personal_route import PersonalRouteService
from andromeda.modules.recommendations.services.current import CurrentRecommendationService
from andromeda.modules.recommendations.services.recommendations import RecommendationService
from andromeda.modules.admin_ops.services.ingestion_runs import IngestionRunService
from andromeda.modules.auth.services.authentication import AuthenticationService


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

    def admission_fit_reader(self, session: Session) -> AdmissionFitDataReader:
        return SqlAlchemyAdmissionFitReader(self.program_reader(session), self.admission_reader(session))

    def university_reader(self, session: Session) -> SqlAlchemyUniversityRepository:
        return SqlAlchemyUniversityRepository(session)

    def event_reader(self, session: Session) -> SqlAlchemyEventRepository:
        return SqlAlchemyEventRepository(session)

    def event_service(self, session: Session) -> EventService:
        return EventService(self.event_reader(session))

    def campus_point_reader(self, session: Session) -> CampusPointReader:
        return SqlAlchemyCampusPointRepository(session)

    def campus_service(self, session: Session) -> CampusService:
        return CampusService(self.campus_point_reader(session))

    def current_recommendation_service(self, session: Session) -> CurrentRecommendationService:
        return CurrentRecommendationService(
            self.user_profile_repository(session),
            RecommendationService(self.recommendation_catalog_reader(session)),
        )

    def personal_route_service(self, session: Session) -> PersonalRouteService:
        return PersonalRouteService(
            self.current_recommendation_service(session),
            self.event_service(session),
            self.campus_service(session),
        )

    def proftest_catalog_reader(self, session: Session) -> SqlAlchemyProftestCatalogRepository:
        return SqlAlchemyProftestCatalogRepository(self.program_reader(session), self.curriculum_reader(session), self.discipline_reader(session))

    def user_profile_repository(self, session: Session) -> SqlAlchemyUserProfileRepository:
        return SqlAlchemyUserProfileRepository(session)

    def account_repository(self, session: Session) -> SqlAlchemyAccountRepository:
        return SqlAlchemyAccountRepository(session)

    def auth_service(self, session: Session) -> AuthenticationService:
        return AuthenticationService(
            self.account_repository(session),
            Argon2PasswordHasher(),
            self.user_profile_repository(session),
            SqlAlchemyProftestSessionRepository(session),
        )

    def recommendation_catalog_reader(self, session: Session) -> CatalogRecommendationRepository:
        return CatalogRecommendationRepository(ProftestCatalogService(self.proftest_catalog_reader(session)))

    def ingestion_run_service(self, session: Session) -> IngestionRunService:
        return IngestionRunService(SqlAlchemyIngestionRunReader(session))

    @property
    def ingestion(self) -> SqlAlchemyIngestionRepository:
        return SqlAlchemyIngestionRepository(self.engine)


def build_container(engine: Engine) -> AndromedaContainer:
    return AndromedaContainer(engine=engine)
