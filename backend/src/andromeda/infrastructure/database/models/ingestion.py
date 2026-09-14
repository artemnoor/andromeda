from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class IngestRunModel(Base):
    __tablename__ = "ingest_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    program_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    curriculum_item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    campus_point_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    unchanged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    removed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    source_hashes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")
    source_kinds_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")

    __table_args__ = (
        CheckConstraint("status IN ('running', 'completed', 'failed')", name="ck_ingest_run_status"),
        CheckConstraint("source_count >= 0", name="ck_ingest_run_source_count"),
        CheckConstraint("program_count >= 0", name="ck_ingest_run_program_count"),
        CheckConstraint("curriculum_item_count >= 0", name="ck_ingest_run_curriculum_item_count"),
        CheckConstraint("event_count >= 0", name="ck_ingest_run_event_count"),
        CheckConstraint("campus_point_count >= 0", name="ck_ingest_run_campus_point_count"),
        CheckConstraint("inserted_count >= 0", name="ck_ingest_run_inserted_count"),
        CheckConstraint("updated_count >= 0", name="ck_ingest_run_updated_count"),
        CheckConstraint("unchanged_count >= 0", name="ck_ingest_run_unchanged_count"),
        CheckConstraint("removed_count >= 0", name="ck_ingest_run_removed_count"),
    )


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
