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
