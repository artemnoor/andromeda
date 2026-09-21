from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from andromeda.infrastructure.config.settings import Settings
from andromeda.infrastructure.repositories.admin_ops import SqlAlchemyIngestionRunReader
from andromeda.infrastructure.repositories.admission_fit import (
    SqlAlchemyAdmissionFitReader,
)
from andromeda.infrastructure.repositories.admissions import (
    SqlAlchemyAdmissionRepository,
)
from andromeda.infrastructure.repositories.analytics import (
    SqlAlchemyProgramProjectionRepository,
)
from andromeda.infrastructure.repositories.auth import SqlAlchemyAccountRepository
from andromeda.infrastructure.repositories.campus import SqlAlchemyCampusPointRepository
from andromeda.infrastructure.repositories.curricula import (
    SqlAlchemyCurriculumRepository,
)
from andromeda.infrastructure.repositories.decision import (
    SqlAlchemyDecisionContextRepository,
)
from andromeda.infrastructure.repositories.decision_analytics import (
    SqlAlchemyDecisionAnalyticsRepository,
)
from andromeda.infrastructure.repositories.decision_candidates import (
    CatalogDecisionCandidateSource,
)
from andromeda.infrastructure.repositories.derived_refresh import (
    SqlAlchemyDerivedRefreshAdapter,
)
from andromeda.infrastructure.repositories.entity_resolution import (
    SqlAlchemyEntityResolutionRepository,
)
from andromeda.infrastructure.repositories.disciplines import (
    SqlAlchemyDisciplineRepository,
)
from andromeda.infrastructure.repositories.events import SqlAlchemyEventRepository
from andromeda.infrastructure.repositories.ingestion import (
    SqlAlchemyIngestionRepository,
)
from andromeda.infrastructure.repositories.ingestion_recovery import (
    SqlAlchemyIngestionRunRecovery,
)
from andromeda.infrastructure.repositories.ingestion_retry import (
    SqlAlchemyIngestionRetryExecutor,
)
from andromeda.infrastructure.repositories.proftest import (
    SqlAlchemyProftestCatalogRepository,
)
from andromeda.infrastructure.repositories.proftest_sessions import (
    SqlAlchemyProftestSessionRepository,
)
from andromeda.infrastructure.repositories.programs import SqlAlchemyProgramRepository
from andromeda.infrastructure.repositories.query_sessions import (
    SqlAlchemyQuerySessionRepository,
)
from andromeda.infrastructure.repositories.recommendations import (
    CatalogRecommendationRepository,
)
from andromeda.infrastructure.repositories.semantic_enrichment import (
    SqlAlchemySemanticEnrichmentRepository,
)
from andromeda.infrastructure.repositories.universities import (
    SqlAlchemyUniversityRepository,
)
from andromeda.infrastructure.repositories.university_admin import (
    SqlAlchemyUniversityAdminMembershipRepository,
)
from andromeda.infrastructure.repositories.university_catalog import (
    SqlAlchemyUniversityCatalogCanonicalReader,
    SqlAlchemyUniversityCatalogRepository,
)
from andromeda.infrastructure.repositories.university_events import (
    SqlAlchemyUniversityEditorialEventRepository,
)
from andromeda.infrastructure.repositories.user_profiles import (
    SqlAlchemyUserProfileRepository,
)
from andromeda.infrastructure.security.passwords import Argon2PasswordHasher
from andromeda.modules.admin_ops.services.ingestion_runs import IngestionRunService
from andromeda.modules.admission_fit.repository.ports import AdmissionFitDataReader
from andromeda.modules.admission_fit.services.admission_fit import AdmissionFitService
from andromeda.modules.admissions.services.admissions import AdmissionService
from andromeda.modules.analytics.services.cache import AnalyticsResultCache
from andromeda.modules.analytics.services.executor import AnalyticsExecutor
from andromeda.modules.analytics.services.projection_builder import (
    ProgramProjectionBuilder,
    ProgramProjectionService,
)
from andromeda.modules.auth.services.authentication import AuthenticationService
from andromeda.modules.campus.repository.ports import CampusPointReader
from andromeda.modules.campus.services.campus import CampusService
from andromeda.modules.comparison.services.compare_programs import (
    CompareProgramsService,
)
from andromeda.modules.comparison.services.compare_summary import (
    ComparisonSummaryService,
)
from andromeda.modules.conversation.services.assistant import AssistantService
from andromeda.modules.conversation.services.engine import ConversationEngine
from andromeda.modules.conversation.services.rule_decision_policy import (
    RuleBasedDecisionPolicy,
)
from andromeda.modules.curricula.repository.ports import CurriculumReader
from andromeda.modules.decision.services.analytics import DecisionAnalyticsService
from andromeda.modules.decision.services.candidates import DecisionCandidatePipeline
from andromeda.modules.decision.services.decision import DecisionService
from andromeda.modules.disciplines.repository.ports import DisciplineReader
from andromeda.modules.events.services.events import EventService
from andromeda.modules.entity_resolution.services.resolvers import (
    CachedEntityCatalog,
    EntityResolverService,
)
from andromeda.modules.personal_route.services.personal_route import (
    PersonalRouteService,
)
from andromeda.modules.presentation.services.rule_response_policy import (
    RuleBasedResponsePolicy,
)
from andromeda.modules.proftest.repository.ports import UserProfileRepository
from andromeda.modules.proftest.services.catalog import ProftestCatalogService
from andromeda.modules.proftest.services.profile_persistence import (
    UserProfilePersistenceService,
)
from andromeda.modules.proftest.services.proftest import ProftestService
from andromeda.modules.proftest.services.session import ProftestSessionService
from andromeda.modules.programs.repository.ports import ProgramReader
from andromeda.modules.recommendations.services.current import (
    CurrentRecommendationService,
)
from andromeda.modules.recommendations.services.recommendations import (
    RecommendationService,
)
from andromeda.modules.semantic.services.classifier import RuleBasedSemanticClassifier
from andromeda.modules.semantic.services.enrichment import SemanticEnrichmentService
from andromeda.modules.universities.repository.ports import UniversityReader
from andromeda.modules.university_admin.repository.catalog_ports import (
    UniversityCatalogCanonicalReader,
    UniversityCatalogReader,
    UniversityCatalogWriter,
)
from andromeda.modules.university_admin.repository.event_ports import (
    UniversityEditorialEventReader,
    UniversityEditorialEventWriter,
)
from andromeda.modules.university_admin.repository.ports import (
    UniversityAdminAccessReader,
    UniversityMembershipWriter,
)
from andromeda.modules.university_admin.services.access import (
    UniversityAdminAccessService,
)
from andromeda.modules.university_admin.services.catalog import UniversityCatalogService
from andromeda.modules.university_admin.services.events import (
    UniversityEditorialEventService,
)
from andromeda.modules.university_admin.services.membership import (
    UniversityMembershipService,
)


@dataclass(frozen=True, slots=True)
class AndromedaContainer:
    """The single outer composition root for API and script-owned services.

    The container is deliberately infrastructure-aware. It is an outer-layer
    object: subject modules still receive typed ports and never import this
    class, SQLAlchemy models, or FastAPI dependencies.
    """

    engine: Engine
    settings: Settings
    analytics_cache: AnalyticsResultCache = field(default_factory=AnalyticsResultCache)

    def program_reader(self, session: Session) -> ProgramReader:
        return SqlAlchemyProgramRepository(session)

    def university_reader(self, session: Session) -> UniversityReader:
        return SqlAlchemyUniversityRepository(session)

    def university_admin_membership_repository(
        self, session: Session
    ) -> SqlAlchemyUniversityAdminMembershipRepository:
        return SqlAlchemyUniversityAdminMembershipRepository(session)

    def university_admin_access_reader(self, session: Session) -> UniversityAdminAccessReader:
        return self.university_admin_membership_repository(session)

    def university_admin_membership_writer(self, session: Session) -> UniversityMembershipWriter:
        return self.university_admin_membership_repository(session)

    def university_admin_access_service(self, session: Session) -> UniversityAdminAccessService:
        return UniversityAdminAccessService(self.university_admin_access_reader(session))

    def university_membership_service(self, session: Session) -> UniversityMembershipService:
        repository = self.university_admin_membership_repository(session)
        return UniversityMembershipService(repository, repository)

    def university_catalog_reader(self, session: Session) -> UniversityCatalogReader:
        return SqlAlchemyUniversityCatalogRepository(session)

    def university_catalog_writer(self, session: Session) -> UniversityCatalogWriter:
        return SqlAlchemyUniversityCatalogRepository(session)

    def university_catalog_canonical_reader(self, session: Session) -> UniversityCatalogCanonicalReader:
        return SqlAlchemyUniversityCatalogCanonicalReader(session)

    def university_catalog_service(self, session: Session) -> UniversityCatalogService:
        repository = SqlAlchemyUniversityCatalogRepository(session)
        return UniversityCatalogService(repository, repository, self.university_catalog_canonical_reader(session))

    def university_editorial_event_reader(self, session: Session) -> UniversityEditorialEventReader:
        return SqlAlchemyUniversityEditorialEventRepository(session)

    def university_editorial_event_writer(self, session: Session) -> UniversityEditorialEventWriter:
        return SqlAlchemyUniversityEditorialEventRepository(session)

    def university_editorial_event_service(self, session: Session) -> UniversityEditorialEventService:
        repository = SqlAlchemyUniversityEditorialEventRepository(session)
        return UniversityEditorialEventService(
            repository,
            repository,
            self.university_catalog_reader(session),
            self.university_catalog_canonical_reader(session),
        )

    def curriculum_reader(self, session: Session) -> CurriculumReader:
        return SqlAlchemyCurriculumRepository(session)

    def discipline_reader(self, session: Session) -> DisciplineReader:
        return SqlAlchemyDisciplineRepository(session)

    def admission_reader(self, session: Session) -> SqlAlchemyAdmissionRepository:
        return SqlAlchemyAdmissionRepository(session)

    def admission_service(self, session: Session) -> AdmissionService:
        return AdmissionService(self.program_reader(session), self.admission_reader(session))

    def admission_fit_reader(self, session: Session) -> AdmissionFitDataReader:
        return SqlAlchemyAdmissionFitReader(self.program_reader(session), self.admission_reader(session))

    def admission_fit_service(self, session: Session) -> AdmissionFitService:
        return AdmissionFitService(self.admission_fit_reader(session))

    def comparison_service(self, session: Session) -> CompareProgramsService:
        return CompareProgramsService(
            self.program_reader(session),
            self.curriculum_reader(session),
            self.discipline_reader(session),
        )

    def comparison_summary_service(self, session: Session) -> ComparisonSummaryService:
        return ComparisonSummaryService(
            self.comparison_service(session),
            self.program_reader(session),
            self.curriculum_reader(session),
        )

    def proftest_catalog_reader(self, session: Session) -> SqlAlchemyProftestCatalogRepository:
        return SqlAlchemyProftestCatalogRepository(
            self.program_reader(session),
            self.curriculum_reader(session),
            self.discipline_reader(session),
            session=session,
        )

    def proftest_catalog_service(self, session: Session) -> ProftestCatalogService:
        return ProftestCatalogService(
            self.proftest_catalog_reader(session),
            projection_reader=SqlAlchemyProgramProjectionRepository(self.engine),
        )

    def user_profile_repository(self, session: Session) -> SqlAlchemyUserProfileRepository:
        return SqlAlchemyUserProfileRepository(session)

    def profile_persistence_service(self, session: Session) -> UserProfilePersistenceService:
        return UserProfilePersistenceService(
            self.user_profile_repository(session),
            ttl_seconds=self.settings.profile_ttl_seconds,
        )

    def current_user_profile_reader(self, session: Session) -> UserProfileRepository:
        return self.user_profile_repository(session)

    def recommendation_catalog_reader(self, session: Session) -> CatalogRecommendationRepository:
        return CatalogRecommendationRepository(self.proftest_catalog_service(session))

    def recommendation_service(self, session: Session) -> RecommendationService:
        return RecommendationService(self.recommendation_catalog_reader(session))

    def decision_context_repository(self, session: Session) -> SqlAlchemyDecisionContextRepository:
        return SqlAlchemyDecisionContextRepository(session)

    def decision_analytics_writer(self, session: Session) -> SqlAlchemyDecisionAnalyticsRepository:
        return SqlAlchemyDecisionAnalyticsRepository(session)

    def decision_analytics_reader(self, session: Session) -> SqlAlchemyDecisionAnalyticsRepository:
        return SqlAlchemyDecisionAnalyticsRepository(session)

    def decision_analytics_service(self, session: Session) -> DecisionAnalyticsService:
        return DecisionAnalyticsService(self.decision_analytics_writer(session))

    def decision_candidate_source(self, session: Session) -> CatalogDecisionCandidateSource:
        return CatalogDecisionCandidateSource(
            self.program_reader(session),
            self.recommendation_catalog_reader(session),
            self.admission_reader(session),
            self.university_reader(session),
        )

    def decision_candidate_pipeline(self, session: Session) -> DecisionCandidatePipeline:
        return DecisionCandidatePipeline(
            self.decision_candidate_source(session),
            self.recommendation_service(session),
            self.admission_fit_service(session),
        )

    def decision_service(self, session: Session) -> DecisionService:
        return DecisionService(
            self.decision_context_repository(session),
            self.program_reader(session),
            self.current_user_profile_reader(session),
            self.decision_candidate_pipeline(session),
            ttl_seconds=self.settings.profile_ttl_seconds,
            analytics=self.decision_analytics_service(session),
            profile_writer=self.profile_persistence_service(session),
        )

    def proftest_service(self, session: Session) -> ProftestService:
        return ProftestService(
            self.proftest_catalog_service(session),
            self.recommendation_service(session),
            profile_persistence=self.profile_persistence_service(session),
        )

    def proftest_session_repository(self, session: Session) -> SqlAlchemyProftestSessionRepository:
        return SqlAlchemyProftestSessionRepository(session)

    def proftest_session_service(self, session: Session) -> ProftestSessionService:
        session_repository = self.proftest_session_repository(session)
        return ProftestSessionService(
            self.proftest_catalog_service(session),
            self.recommendation_service(session),
            session_repository,
            session_repository,
            profile_reader=self.current_user_profile_reader(session),
            ttl_seconds=self.settings.profile_ttl_seconds,
        )

    def current_recommendation_service(self, session: Session) -> CurrentRecommendationService:
        return CurrentRecommendationService(
            self.current_user_profile_reader(session),
            self.recommendation_service(session),
        )

    def event_reader(self, session: Session) -> SqlAlchemyEventRepository:
        return SqlAlchemyEventRepository(session)

    def event_service(self, session: Session) -> EventService:
        return EventService(self.event_reader(session))

    def campus_point_reader(self, session: Session) -> CampusPointReader:
        return SqlAlchemyCampusPointRepository(session)

    def campus_service(self, session: Session) -> CampusService:
        return CampusService(self.campus_point_reader(session))

    def personal_route_service(self, session: Session) -> PersonalRouteService:
        return PersonalRouteService(
            self.current_recommendation_service(session),
            self.event_service(session),
            self.campus_service(session),
        )

    def account_repository(self, session: Session) -> SqlAlchemyAccountRepository:
        return SqlAlchemyAccountRepository(session)

    def auth_service(self, session: Session) -> AuthenticationService:
        return AuthenticationService(
            self.account_repository(session),
            Argon2PasswordHasher(),
            self.user_profile_repository(session),
            self.proftest_session_repository(session),
            self.decision_context_repository(session),
            password_min_length=self.settings.auth_password_min_length,
            session_ttl_seconds=self.settings.auth_session_ttl_seconds,
        )

    def ingestion_run_reader(self, session: Session) -> SqlAlchemyIngestionRunReader:
        return SqlAlchemyIngestionRunReader(session)

    def ingestion_retry_executor(self) -> SqlAlchemyIngestionRetryExecutor:
        return SqlAlchemyIngestionRetryExecutor(self.engine, self.settings.environment)

    def ingestion_run_recovery(self) -> SqlAlchemyIngestionRunRecovery:
        return SqlAlchemyIngestionRunRecovery(self.engine)

    def ingestion_run_service(self, session: Session) -> IngestionRunService:
        return IngestionRunService(
            self.ingestion_run_reader(session),
            self.ingestion_retry_executor(),
            self.ingestion_run_recovery(),
            stale_timeout_seconds=self.settings.ingestion_run_timeout_seconds,
        )

    @property
    def semantic_enrichment(self) -> SemanticEnrichmentService:
        return SemanticEnrichmentService(
            RuleBasedSemanticClassifier(),
            SqlAlchemySemanticEnrichmentRepository(self.engine),
        )

    @property
    def ingestion(self) -> SqlAlchemyIngestionRepository:
        return SqlAlchemyIngestionRepository(
            self.engine,
            derived_refresh=self.derived_refresh,
        )

    @property
    def derived_refresh(self) -> SqlAlchemyDerivedRefreshAdapter:
        return SqlAlchemyDerivedRefreshAdapter(
            self.semantic_enrichment,
            self.program_projection_service,
        )

    @property
    def program_projection_service(self) -> ProgramProjectionService:
        semantic_store = SqlAlchemySemanticEnrichmentRepository(self.engine)
        return ProgramProjectionService(
            ProgramProjectionBuilder(),
            semantic_store,
            SqlAlchemyProgramProjectionRepository(self.engine),
            cache=self.analytics_cache,
        )

    def analytics_executor(self) -> AnalyticsExecutor:
        return AnalyticsExecutor(
            SqlAlchemyProgramProjectionRepository(self.engine),
            cache=self.analytics_cache,
        )

    def entity_resolver(self) -> EntityResolverService:
        return EntityResolverService(CachedEntityCatalog(SqlAlchemyEntityResolutionRepository(self.engine)))

    def assistant_service(self, session: Session) -> AssistantService:
        return AssistantService(
            SqlAlchemyQuerySessionRepository(session),
            ConversationEngine(),
            RuleBasedDecisionPolicy(),
            RuleBasedResponsePolicy(),
            self.analytics_executor(),
            self.admission_fit_service(session),
            self.program_reader(session),
            entity_resolver=self.entity_resolver(),
            ttl_seconds=self.settings.profile_ttl_seconds,
        )


def build_container(engine: Engine, settings: Settings | None = None) -> AndromedaContainer:
    """Build the only active service graph for an application process."""

    return AndromedaContainer(engine=engine, settings=settings or Settings.from_environment())


__all__ = ["AndromedaContainer", "build_container"]
