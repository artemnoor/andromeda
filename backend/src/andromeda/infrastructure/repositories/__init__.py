from .curricula import SqlAlchemyCurriculumRepository
from .disciplines import SqlAlchemyDisciplineRepository
from .ingestion import SqlAlchemyIngestionRepository
from .programs import SqlAlchemyProgramRepository
from .universities import SqlAlchemyUniversityRepository
from .user_profiles import SqlAlchemyUserProfileRepository

__all__ = [
    "SqlAlchemyCurriculumRepository",
    "SqlAlchemyDisciplineRepository",
    "SqlAlchemyIngestionRepository",
    "SqlAlchemyProgramRepository",
    "SqlAlchemyUniversityRepository",
    "SqlAlchemyUserProfileRepository",
]
