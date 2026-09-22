from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from andromeda.infrastructure.database import Base, create_engine_for_url
from andromeda.infrastructure.database.models import (
    AdmissionBenefitRuleModel,
    IndividualAchievementRuleModel,
    RawSourceRecordModel,
)
from andromeda.infrastructure.repositories.ingestion import (
    SqlAlchemyIngestionRepository,
)
from andromeda.ingestion.contracts.raw import RawSourceSnapshot
from andromeda.ingestion.contracts.source import CapturedSources
from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter

TRACER_FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "tracer" / "raw"
BENEFIT_FIXTURE_DIR = Path(__file__).parents[1] / "ingestion" / "fixtures" / "bmstu" / "admission_benefits"
RUN_ID = "ingest:" + "b" * 32


def _benefit_snapshot(file_name: str, document_kind: str) -> RawSourceSnapshot:
    payload = json.loads((BENEFIT_FIXTURE_DIR / file_name).read_text(encoding="utf-8"))
    url = payload["source_url"]
    return RawSourceSnapshot(
        source_kind=f"bmstu_admission_document:{document_kind}",
        requested_url=url,
        final_url=url,
        status_code=200,
        content_type="application/json",
        captured_at=datetime(2026, 9, 22, tzinfo=UTC),
        content_sha256=payload["content_sha256"],
        body=(BENEFIT_FIXTURE_DIR / file_name).read_bytes(),
        access_mode="fixture",
    )


def test_official_bmstu_extracts_are_persisted_in_the_existing_ingestion_transaction(tmp_path: Path) -> None:
    adapter = BmstuUniversityAdapter()
    try:
        captured = adapter.capture(mode="fixture", fixture_dir=TRACER_FIXTURE_DIR)
        captured = CapturedSources(
            snapshots=(
                *captured.snapshots,
                _benefit_snapshot("appendix-5-1-extract.json", "appendix_5_1"),
                _benefit_snapshot("appendix-5-3-extract.json", "appendix_5_3"),
                _benefit_snapshot("appendix-6-extract.json", "appendix_6"),
            ),
            source_gaps=captured.source_gaps,
        )
        raw, canonical = adapter.parse(captured, source_run_id=RUN_ID, admission_year=2026)
    finally:
        adapter.close()

    assert raw.admission_benefit_records
    assert canonical.admission_benefits is not None
    assert canonical.admission_benefits.admission_year == 2026
    assert canonical.admission_benefits.benefit_rules
    assert canonical.admission_benefits.individual_achievement_policy is not None

    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'benefits.db').as_posix()}")
    Base.metadata.create_all(engine)
    repository = SqlAlchemyIngestionRepository(engine)
    repository.start_run(run_id=RUN_ID, university_id=canonical.university.id)
    repository.ingest(raw, canonical, run_id=RUN_ID)

    with Session(engine) as session:
        assert session.scalar(select(AdmissionBenefitRuleModel.id)) is not None
        assert session.scalar(select(IndividualAchievementRuleModel.id)) is not None
        benefit_raw_count = session.scalar(
            select(RawSourceRecordModel.id).where(RawSourceRecordModel.record_type == "AdmissionBenefit").limit(1)
        )
        assert benefit_raw_count is not None
    engine.dispose()
