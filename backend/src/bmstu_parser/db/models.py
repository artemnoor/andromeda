"""Legacy ORM import facade; ORM remains infrastructure-only."""

from andromeda.infrastructure.database.models import (
    AssessmentTypeModel,
    CurriculumItemAssessmentModel,
    CurriculumItemModel,
    CurriculumModel,
    DirectionModel,
    DisciplineAreaModel,
    DisciplineAreaWeightModel,
    DisciplineModel,
    EducationalProgramModel,
    EducationLevelModel,
    IngestRunModel,
    ProgramModel,
    RawSourceRecordModel,
    SourceSnapshotModel,
    UniversityModel,
)

__all__ = [
    "AssessmentTypeModel",
    "CurriculumItemAssessmentModel",
    "CurriculumItemModel",
    "CurriculumModel",
    "DirectionModel",
    "DisciplineAreaModel",
    "DisciplineAreaWeightModel",
    "DisciplineModel",
    "EducationalProgramModel",
    "EducationLevelModel",
    "IngestRunModel",
    "ProgramModel",
    "RawSourceRecordModel",
    "SourceSnapshotModel",
    "UniversityModel",
]
