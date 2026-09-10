from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class IngestRunModel(Base):
    __tablename__ = "ingest_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class SourceSnapshotModel(Base):
    __tablename__ = "source_snapshots"

    content_sha256: Mapped[str] = mapped_column(String(64), primary_key=True)
    ingest_run_id: Mapped[str] = mapped_column(ForeignKey("ingest_runs.id"), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(128), nullable=False)
    requested_url: Mapped[str] = mapped_column(Text, nullable=False)
    final_url: Mapped[str] = mapped_column(Text, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(256), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    body: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    __table_args__ = (
        CheckConstraint("length(content_sha256) = 64", name="ck_source_snapshot_sha256_length"),
        CheckConstraint("status_code >= 200 AND status_code <= 599", name="ck_source_snapshot_status"),
    )


class RawSourceRecordModel(Base):
    __tablename__ = "raw_source_records"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    snapshot_sha256: Mapped[str] = mapped_column(ForeignKey("source_snapshots.content_sha256"), nullable=False)
    record_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class EducationLevelModel(Base):
    __tablename__ = "education_levels"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)


class AssessmentTypeModel(Base):
    __tablename__ = "assessment_types"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)


class UniversityModel(Base):
    __tablename__ = "universities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    city: Mapped[str] = mapped_column(String(256), nullable=False)
    official_site: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)

    __table_args__ = (
        CheckConstraint("length(name) > 0", name="ck_university_name_non_empty"),
        CheckConstraint("length(city) > 0", name="ck_university_city_non_empty"),
        CheckConstraint("length(address) > 0", name="ck_university_address_non_empty"),
        CheckConstraint("id LIKE 'university:%'", name="ck_university_id_shape"),
    )


class DirectionModel(Base):
    __tablename__ = "directions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    education_level: Mapped[str] = mapped_column(ForeignKey("education_levels.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("university_id", "code", name="uq_direction_university_code"),
        CheckConstraint("length(code) = 8 AND substr(code, 3, 1) = '.' AND substr(code, 6, 1) = '.'", name="ck_direction_code_shape"),
        CheckConstraint("id = 'direction:' || code", name="ck_direction_id_matches_code"),
        CheckConstraint("length(name) > 0", name="ck_direction_name_non_empty"),
    )


class EducationalProgramModel(Base):
    __tablename__ = "educational_programs"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    direction_id: Mapped[str] = mapped_column(ForeignKey("directions.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    education_year: Mapped[int] = mapped_column(Integer, nullable=False)
    study_plan_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("direction_id", "code", name="uq_program_direction_code"),
        CheckConstraint("id = 'program:' || code", name="ck_program_id_matches_code"),
        CheckConstraint("code LIKE '__.__.__-%'", name="ck_program_code_shape"),
        CheckConstraint("education_year >= 2000 AND education_year <= 2100", name="ck_program_education_year"),
        CheckConstraint("length(name) > 0", name="ck_program_name_non_empty"),
    )


class DisciplineModel(Base):
    __tablename__ = "disciplines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)

    __table_args__ = (
        CheckConstraint("length(name) > 0", name="ck_discipline_name_non_empty"),
        CheckConstraint("length(normalized_name) > 0", name="ck_discipline_normalized_non_empty"),
    )


class CurriculumModel(Base):
    __tablename__ = "curricula"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    program_id: Mapped[str] = mapped_column(ForeignKey("educational_programs.id"), nullable=False)
    education_year: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("program_id", "education_year", name="uq_curriculum_program_year"),
        CheckConstraint("education_year >= 2000 AND education_year <= 2100", name="ck_curriculum_education_year"),
        CheckConstraint("id LIKE 'curriculum:%'", name="ck_curriculum_id_shape"),
    )


class CurriculumItemModel(Base):
    __tablename__ = "curriculum_items"

    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    curriculum_id: Mapped[str] = mapped_column(ForeignKey("curricula.id"), nullable=False)
    discipline_id: Mapped[str] = mapped_column(ForeignKey("disciplines.id"), nullable=False)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hours: Mapped[int] = mapped_column(Integer, nullable=False)
    credits: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    subject_group: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("curriculum_id", "discipline_id", "semester", name="uq_curriculum_item_identity"),
        CheckConstraint("semester IS NULL OR (semester >= 1 AND semester <= 12)", name="ck_item_semester"),
        CheckConstraint("hours >= 0 AND hours <= 2000", name="ck_item_hours"),
        CheckConstraint("credits IS NULL OR (credits >= 0 AND credits <= 60)", name="ck_item_credits"),
        CheckConstraint("source_position IS NULL OR source_position >= 1", name="ck_item_source_position"),
    )


class CurriculumItemAssessmentModel(Base):
    __tablename__ = "curriculum_item_assessments"

    curriculum_item_id: Mapped[str] = mapped_column(ForeignKey("curriculum_items.id", ondelete="CASCADE"), primary_key=True)
    assessment_type_id: Mapped[str] = mapped_column(ForeignKey("assessment_types.id"), primary_key=True)
