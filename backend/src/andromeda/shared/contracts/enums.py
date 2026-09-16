from enum import StrEnum


class EducationLevel(StrEnum):
    BACHELOR = "bachelor"
    SPECIALIST = "specialist"
    MASTER = "master"
    POSTGRADUATE = "postgraduate"


class AssessmentType(StrEnum):
    EXAM = "exam"
    CREDIT = "credit"
    GRADED_CREDIT = "graded_credit"
    COURSEWORK = "coursework"
    COURSE_PROJECT = "course_project"
    STATE_EXAM = "state_exam"


class SourceKind(StrEnum):
    BMSTU_COMMON = "bmstu_common"
    BMSTU_MAJOR_CATALOG = "bmstu_major_catalog"
    BMSTU_MAJOR_DETAIL = "bmstu_major_detail"
    BMSTU_CURRICULUM_DOCUMENT = "bmstu_curriculum_document"
    BMSTU_CURRICULUM_METADATA = "bmstu_curriculum_metadata"
    BMSTU_ADMISSION_ORDERS_INDEX = "bmstu_admission_orders_index"
    BMSTU_ADMISSION_ORDERS_DOCUMENT = "bmstu_admission_orders_document"
    BMSTU_EVENTS = "bmstu_events"
    BMSTU_CAMPUS_POINTS = "bmstu_campus_points"


class CompareStatus(StrEnum):
    BOTH = "both"
    ONLY_A = "only_a"
    ONLY_B = "only_b"
    DIFFERENT = "different"


class ComparisonScope(StrEnum):
    ALL = "all"
    SEMESTER = "semester"
