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
from andromeda.infrastructure.repositories.admission_benefits import (
    SqlAlchemyAdmissionBenefitsRepository,
)
from andromeda.infrastructure.repositories.ingestion import (
    SqlAlchemyIngestionRepository,
)
from andromeda.ingestion.contracts.raw import RawSourceSnapshot
from andromeda.ingestion.contracts.source import CapturedSources, source_fetch_gap
from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter
from andromeda.modules.admission_benefits.contracts.applicant import (
    ApplicantAdmissionFacts,
    ApplicantIndividualAchievement,
)
from andromeda.modules.admission_benefits.contracts.coverage import (
    AdmissionBenefitCoverageStatus,
)
from andromeda.modules.admission_benefits.contracts.public import (
    AchievementCombinationPolicy,
)
from andromeda.modules.admission_benefits.contracts.results import (
    IndividualAchievementStatus,
)
from andromeda.modules.admission_benefits.services.individual_achievements import (
    IndividualAchievementCalculator,
)

TRACER_FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "tracer" / "raw"
BENEFIT_FIXTURE_DIR = (
    Path(__file__).parents[1]
    / "ingestion"
    / "fixtures"
    / "bmstu"
    / "admission_benefits"
)
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


def _olympiad_profile_snapshot(file_name: str) -> RawSourceSnapshot:
    payload = json.loads((BENEFIT_FIXTURE_DIR / file_name).read_text(encoding="utf-8"))
    url = payload["source_url"]
    return RawSourceSnapshot(
        source_kind="bmstu_olympiad_profile:engineering",
        requested_url=url,
        final_url=url,
        status_code=200,
        content_type="application/json",
        captured_at=datetime(2026, 9, 22, tzinfo=UTC),
        content_sha256=payload["content_sha256"],
        body=(BENEFIT_FIXTURE_DIR / file_name).read_bytes(),
        access_mode="fixture",
    )


def test_official_bmstu_extracts_are_persisted_in_the_existing_ingestion_transaction(
    tmp_path: Path,
) -> None:
    adapter = BmstuUniversityAdapter()
    try:
        captured = adapter.capture(mode="fixture", fixture_dir=TRACER_FIXTURE_DIR)
        captured = CapturedSources(
            snapshots=(
                *captured.snapshots,
                _benefit_snapshot("appendix-5-1-extract.json", "appendix_5_1"),
                _benefit_snapshot("appendix-5-3-extract.json", "appendix_5_3"),
                _benefit_snapshot("appendix-6-extract.json", "appendix_6"),
                _benefit_snapshot("rules-2026.extract.json", "rules"),
                _olympiad_profile_snapshot("shag-engineering.html.extract.json"),
            ),
            source_gaps=(
                *captured.source_gaps,
                source_fetch_gap(
                    "bmstu_admission_document:appendix_5_2",
                    "https://api.www.bmstu.ru/file/122143/download",
                    "document_unavailable",
                ),
            ),
        )
        raw, canonical = adapter.parse(
            captured, source_run_id=RUN_ID, admission_year=2026
        )
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
            select(RawSourceRecordModel.id)
            .where(RawSourceRecordModel.record_type == "AdmissionBenefit")
            .limit(1)
        )
        assert benefit_raw_count is not None
        catalog = SqlAlchemyAdmissionBenefitsRepository(session).get_catalog(
            "university:bmstu", 2026
        )
        assert catalog is not None
        assert catalog.coverage.status is AdmissionBenefitCoverageStatus.PARTIAL
        assert any(gap.code == "document_unavailable" for gap in catalog.source_gaps)
        step_in_future = next(
            item for item in catalog.olympiads if "Шаг в будущее" in item.official_name
        )
        step_rules = [
            rule
            for rule in catalog.benefit_rules
            if rule.olympiad_id == step_in_future.id
        ]
        assert step_rules
        assert any(rule.validity.max_age_years == 4 for rule in step_rules)
        assert any(
            subject.minimum_score == 65
            and subject.applicant_category.value == "territorial_exception"
            for rule in step_rules
            for subject in rule.confirmation_subjects
        )
        conditions = [condition for rule in step_rules for condition in rule.conditions]
        confirmation_evidence = next(
            condition.provenance
            for condition in conditions
            if condition.kind.value == "confirmation_score"
            and condition.provenance is not None
        )
        validity_evidence = next(
            condition.provenance
            for condition in conditions
            if condition.kind.value == "validity" and condition.provenance is not None
        )
        assert confirmation_evidence is not None
        assert "page=12;section=1.12" in confirmation_evidence.source.locator
        assert validity_evidence is not None
        assert "page=12;section=1.11" in validity_evidence.source.locator

        achievement_policy = catalog.individual_achievement_policy
        assert achievement_policy is not None
        assert len(achievement_policy.rules) == 82
        assert {rule.provenance.row for rule in achievement_policy.rules} == set(
            range(1, 47)
        )
        assert achievement_policy.global_max_points == 10
        assert achievement_policy.default_combination_policy is AchievementCombinationPolicy.ADDITIVE
        assert achievement_policy.provenance.page == 7
        assert achievement_policy.provenance.source.content_sha256 == "5ae90e108dc8940b37fe3b07f211664b7871791792abdc6ddc0dd365fb948bb9"
        honor_certificate = next(
            rule
            for rule in achievement_policy.rules
            if rule.provenance.row == 1 and rule.points == 10
        )
        gto_rules = [
            rule
            for rule in achievement_policy.rules
            if rule.provenance.row == 5
        ]
        assert {rule.points for rule in gto_rules} == {5, 4, 3}
        gto_policy_evidence = next(
            condition.provenance
            for rule in gto_rules
            for condition in rule.conditions
            if condition.normalized_value == "appendix_6_note:4"
        )
        assert gto_policy_evidence is not None
        assert gto_policy_evidence.page == 8
        assert "document_note=4" in (gto_policy_evidence.source.locator or "")
        applicant = ApplicantAdmissionFacts(
            individual_achievements=(
                ApplicantIndividualAchievement(
                    achievement_code=honor_certificate.achievement_code,
                    year=2026,
                    evidence_reference="document-present:honors-certificate",
                ),
                *(
                    ApplicantIndividualAchievement(
                        achievement_code=rule.achievement_code,
                        year=2026,
                        evidence_reference="document-present:gto-certificate",
                    )
                    for rule in gto_rules
                ),
            )
        )
        achievement_result = IndividualAchievementCalculator().calculate(
            achievement_policy,
            applicant,
        )
        assert achievement_result.global_cap == 10
        assert achievement_result.uncapped_points == 15
        assert achievement_result.total_points == 10
        gold_gto = next(
            item
            for item in achievement_result.evaluations
            if item.rule_points == 5
        )
        assert gold_gto.status is IndividualAchievementStatus.CAPPED
        assert gold_gto.awarded_points == 0
        assert sum(
            item.status is IndividualAchievementStatus.DEDUPLICATED
            for item in achievement_result.evaluations
        ) == 2
        reversed_result = IndividualAchievementCalculator().calculate(
            achievement_policy,
            ApplicantAdmissionFacts(
                individual_achievements=tuple(
                    reversed(applicant.individual_achievements)
                )
            ),
        )
        assert {
            item.achievement_code: (item.status, item.awarded_points)
            for item in achievement_result.evaluations
        } == {
            item.achievement_code: (item.status, item.awarded_points)
            for item in reversed_result.evaluations
        }
    engine.dispose()
