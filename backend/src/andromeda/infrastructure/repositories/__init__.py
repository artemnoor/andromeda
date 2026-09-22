from .analytics import SqlAlchemyProgramProjectionRepository
from .admission_benefits import SqlAlchemyAdmissionBenefitsRepository
from .curricula import SqlAlchemyCurriculumRepository
from .disciplines import SqlAlchemyDisciplineRepository
from .entity_resolution import SqlAlchemyEntityResolutionRepository
from .ingestion import SqlAlchemyIngestionRepository
from .programs import SqlAlchemyProgramRepository
from .query_sessions import SqlAlchemyQuerySessionRepository
from .semantic_enrichment import SqlAlchemySemanticEnrichmentRepository
from .universities import SqlAlchemyUniversityRepository
from .user_profiles import SqlAlchemyUserProfileRepository

__all__ = [
    "SqlAlchemyAdmissionBenefitsRepository",
    "SqlAlchemyCurriculumRepository",
    "SqlAlchemyDisciplineRepository",
    "SqlAlchemyEntityResolutionRepository",
    "SqlAlchemyIngestionRepository",
    "SqlAlchemySemanticEnrichmentRepository",
    "SqlAlchemyProgramProjectionRepository",
    "SqlAlchemyProgramRepository",
    "SqlAlchemyQuerySessionRepository",
    "SqlAlchemyUniversityRepository",
    "SqlAlchemyUserProfileRepository",
]
