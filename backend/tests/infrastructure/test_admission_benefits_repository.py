from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from andromeda.infrastructure.database import Base, create_engine_for_url
from andromeda.infrastructure.database.models import (
    AdmissionBenefitRuleModel,
    DirectionModel,
    EducationalProgramModel,
    EducationLevelModel,
    IngestRunModel,
    SourceSnapshotModel,
    UniversityModel,
)
from andromeda.infrastructure.repositories.admission_benefits import (
    SqlAlchemyAdmissionBenefitsRepository,
)
from andromeda.modules.admission_benefits.contracts.coverage import (
    AdmissionBenefitCoverage,
)
from andromeda.modules.admission_benefits.contracts.policy import (
    BenefitScope,
    BenefitScopeMode,
    BenefitTarget,
    BenefitTargetKind,
)
from andromeda.modules.admission_benefits.contracts.provenance import BenefitProvenance
from andromeda.modules.admission_benefits.contracts.public import (
    AchievementCombinationPolicy,
    AdmissionBenefitRule,
    AdmissionRoute,
    BenefitType,
    ConfirmationExamKind,
    ConfirmationRequirement,
    ConfirmationSubjectRule,
    IndividualAchievementPolicy,
    IndividualAchievementRule,
    Olympiad,
    OlympiadProfile,
    OlympiadProfileSubject,
    OlympiadResultType,
    ValidityPolicy,
)
from andromeda.modules.admission_benefits.contracts.snapshot import (
    AdmissionBenefitsSnapshot,
)
from andromeda.modules.admission_benefits.contracts.status import (
    BenefitPolicyVersion,
    RuleDataStatus,
    TargetResolutionStatus,
)
from andromeda.shared.contracts.enums import EducationLevel, SourceKind
from andromeda.shared.contracts.provenance import SourceAttribution

RUN_ID = "ingest:" + "a" * 32
SOURCE_URL = "https://api.www.bmstu.ru/file/122150/download"
SOURCE_HASH = "b" * 64
PROGRAM_ID = "program:bmstu:09.03.03-01"
UNIVERSITY_ID = "university:bmstu"


def _provenance(*, row: int = 1, source_hash: str = SOURCE_HASH) -> BenefitProvenance:
    source = SourceAttribution(
        kind=SourceKind.BMSTU_ADMISSION_BENEFITS,
        url=SOURCE_URL,
        captured_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
        content_sha256=source_hash,
        locator=f"appendix=5.3;row={row}",
        university_id=UNIVERSITY_ID,
        run_id=RUN_ID,
    )
    return BenefitProvenance(
        source=source,
        source_snapshot_hash=source_hash,
        source_run_id=RUN_ID,
        admission_year=2026,
        document_title="Приложение 5.3",
        document_kind="appendix_5_3",
        appendix_number="5.3",
        page=1,
        table="benefits",
        row=row,
        parser_version="admission-benefits-parser.v1",
    )


def _policy_version() -> BenefitPolicyVersion:
    return BenefitPolicyVersion(
        schema_version="admission-benefits-schema.v1",
        parser_version="admission-benefits-parser.v1",
        policy_version="admission-benefits-policy.v1",
    )


def _snapshot(*, source_hash: str = SOURCE_HASH) -> AdmissionBenefitsSnapshot:
    olympiad = Olympiad(
        id="olympiad:step-in-future",
        official_name="Шаг в будущее",
        organizer="МГТУ им. Н.Э. Баумана",
        rsosh_level=2,
        admission_year=2026,
        provenance=(_provenance(source_hash=source_hash),),
    )
    profile = OlympiadProfile(
        id="olympiad-profile:step-physics",
        olympiad_id=olympiad.id,
        profile_name="Физика",
        corresponding_subjects=(OlympiadProfileSubject(subject="физика", source_text="Физика"),),
        admission_year=2026,
        provenance=(_provenance(source_hash=source_hash),),
    )
    bvi = AdmissionBenefitRule(
        id="admission-benefit:step-bvi",
        university_id=UNIVERSITY_ID,
        admission_year=2026,
        education_level=EducationLevel.BACHELOR,
        route=AdmissionRoute.OLYMPIAD,
        benefit_type=BenefitType.BVI,
        olympiad_id=olympiad.id,
        olympiad_profile_id=profile.id,
        result_type=OlympiadResultType.WINNER,
        scope=BenefitScope(
            mode=BenefitScopeMode.ALL_EXCEPT,
            targets=(
                BenefitTarget(
                    kind=BenefitTargetKind.DIRECTION,
                    value="01.03.02",
                    original_text="кроме 01.03.02",
                ),
            ),
            original_text="все направления, кроме 01.03.02",
        ),
        confirmation_requirement=ConfirmationRequirement.REQUIRED,
        confirmation_subjects=(
            ConfirmationSubjectRule(
                subject="физика",
                minimum_score=Decimal("75"),
                exam_kind=ConfirmationExamKind.EGE,
                source_text="не менее 75 баллов ЕГЭ",
            ),
        ),
        validity=ValidityPolicy(max_age_years=4, source_text="результат действует четыре года"),
        source_text="Победитель получает БВИ",
        provenance=_provenance(source_hash=source_hash),
        policy_version=_policy_version(),
    )
    one_hundred = bvi.model_copy(
        update={
            "id": "admission-benefit:step-100",
            "benefit_type": BenefitType.ONE_HUNDRED_POINTS,
            "result_type": OlympiadResultType.PRIZE_WINNER,
            "scope": BenefitScope(
                mode=BenefitScopeMode.ONLY,
                targets=(
                    BenefitTarget(
                        kind=BenefitTargetKind.DIRECTION,
                        value="09.03.03",
                        original_text="09.03.03",
                    ),
                ),
                original_text="только 09.03.03",
            ),
            "target_subject": "физика",
            "points": Decimal("100"),
            "source_text": "Призёр получает 100 баллов по физике",
            "provenance": _provenance(row=2, source_hash=source_hash),
        }
    )
    achievement = IndividualAchievementRule(
        id="individual-achievement:honors-certificate",
        university_id=UNIVERSITY_ID,
        admission_year=2026,
        education_level=EducationLevel.BACHELOR,
        achievement_code="honors_certificate",
        category="образование",
        official_name="Аттестат с отличием",
        points=Decimal("10"),
        combination_group="all",
        combination_policy=AchievementCombinationPolicy.ADDITIVE,
        source_text="Аттестат с отличием — 10 баллов",
        provenance=_provenance(row=3, source_hash=source_hash),
        policy_version=_policy_version(),
    )
    policy = IndividualAchievementPolicy(
        university_id=UNIVERSITY_ID,
        admission_year=2026,
        education_level=EducationLevel.BACHELOR,
        global_max_points=Decimal("10"),
        default_combination_policy=AchievementCombinationPolicy.ADDITIVE,
        rules=(achievement,),
        source_text="Суммарно не более 10 баллов",
        provenance=_provenance(row=4, source_hash=source_hash),
        policy_version=_policy_version(),
    )
    source = SourceAttribution(
        kind=SourceKind.BMSTU_ADMISSION_BENEFITS,
        url=SOURCE_URL,
        captured_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
        content_sha256=source_hash,
        locator="appendix=5.3",
        university_id=UNIVERSITY_ID,
        run_id=RUN_ID,
    )
    return AdmissionBenefitsSnapshot(
        admission_year=2026,
        sources=(source,),
        olympiads=(olympiad,),
        olympiad_profiles=(profile,),
        benefit_rules=(bvi, one_hundred),
        individual_achievement_policy=policy,
        coverage=AdmissionBenefitCoverage(source_hashes=(source_hash,)),
    )


def _database(tmp_path: Path):
    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'benefits.db').as_posix()}")
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        session.add(UniversityModel(id=UNIVERSITY_ID, name="МГТУ", city="Москва", official_site="https://bmstu.ru", address="Москва"))
        session.add(EducationLevelModel(id=EducationLevel.BACHELOR.value))
        session.add(IngestRunModel(id=RUN_ID, started_at=datetime(2026, 9, 22, tzinfo=timezone.utc), status="running"))
        session.add(
            SourceSnapshotModel(
                content_sha256=SOURCE_HASH,
                ingest_run_id=RUN_ID,
                source_kind=SourceKind.BMSTU_ADMISSION_BENEFITS.value,
                requested_url=SOURCE_URL,
                final_url=SOURCE_URL,
                status_code=200,
                content_type="application/pdf",
                captured_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
                body=b"official fixture",
            )
        )
        session.flush()
        session.add(DirectionModel(id="direction:bmstu:09.03.03", university_id=UNIVERSITY_ID, code="09.03.03", name="Прикладная информатика", education_level="bachelor"))
        session.flush()
        session.add(EducationalProgramModel(id=PROGRAM_ID, direction_id="direction:bmstu:09.03.03", code="09.03.03-01", name="Профиль", education_year=2026, study_plan_url="https://bmstu.ru/plan", source_url="https://bmstu.ru/program"))
    return engine


def test_repository_syncs_and_reads_both_query_directions(tmp_path: Path) -> None:
    engine = _database(tmp_path)
    snapshot = _snapshot()
    with Session(engine) as session, session.begin():
        stats = SqlAlchemyAdmissionBenefitsRepository(session).sync_snapshot(snapshot, source_run_id=RUN_ID)
        assert stats.olympiads_inserted == 1
        assert stats.rules_inserted == 2

    with Session(engine) as session:
        repository = SqlAlchemyAdmissionBenefitsRepository(session)
        statements: list[str] = []

        def capture_statement(_connection, _cursor, statement, _parameters, _context, _executemany) -> None:
            statements.append(statement)

        event.listen(engine, "before_cursor_execute", capture_statement)
        rules = repository.get_rules_for_program(PROGRAM_ID, 2026)
        event.remove(engine, "before_cursor_execute", capture_statement)
        assert {rule.benefit_type for rule in rules} == {BenefitType.BVI, BenefitType.ONE_HUNDRED_POINTS}
        assert len(statements) <= 5
        assert repository.get_programs_for_olympiad("olympiad:step-in-future", UNIVERSITY_ID, 2026)
        policy = repository.get_individual_achievement_policy(UNIVERSITY_ID, 2026, EducationLevel.BACHELOR)
        assert policy is not None
        assert policy.rules[0].points == Decimal("10.00")


def test_repository_same_snapshot_is_idempotent_and_changed_source_stales_old_rows(tmp_path: Path) -> None:
    engine = _database(tmp_path)
    snapshot = _snapshot()
    with Session(engine) as session, session.begin():
        repository = SqlAlchemyAdmissionBenefitsRepository(session)
        first = repository.sync_snapshot(snapshot, source_run_id=RUN_ID)
        second = repository.sync_snapshot(snapshot, source_run_id=RUN_ID)
        assert first.rules_inserted == 2
        assert second.unchanged_rows >= 2

    changed_hash = "c" * 64
    with Session(engine) as session, session.begin():
        session.add(
            SourceSnapshotModel(
                content_sha256=changed_hash,
                ingest_run_id=RUN_ID,
                source_kind=SourceKind.BMSTU_ADMISSION_BENEFITS.value,
                requested_url=SOURCE_URL,
                final_url=SOURCE_URL,
                status_code=200,
                content_type="application/pdf",
                captured_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
                body=b"changed official fixture",
            )
        )
        repository = SqlAlchemyAdmissionBenefitsRepository(session)
        repository.sync_snapshot(_snapshot(source_hash=changed_hash), source_run_id=RUN_ID)

    with Session(engine) as session:
        stale = session.scalar(
            select(func.count()).select_from(AdmissionBenefitRuleModel).where(
                AdmissionBenefitRuleModel.source_snapshot_hash == SOURCE_HASH,
                AdmissionBenefitRuleModel.status == RuleDataStatus.STALE.value,
            )
        )
        assert stale == 2


def test_repository_keeps_unresolved_scope_round_trippable(tmp_path: Path) -> None:
    engine = _database(tmp_path)
    snapshot = _snapshot()
    unresolved_rule = snapshot.benefit_rules[0].model_copy(
        update={
            "id": "admission-benefit:unresolved",
            "scope": BenefitScope(
                mode=BenefitScopeMode.ONLY,
                targets=(
                    BenefitTarget(
                        kind=BenefitTargetKind.DIRECTION,
                        value="неизвестный код",
                        original_text="неизвестное направление",
                        resolution=TargetResolutionStatus.UNRESOLVED,
                    ),
                ),
                original_text="неизвестное направление",
            ),
            "status": RuleDataStatus.UNRESOLVED,
        }
    )
    updated = snapshot.model_copy(update={"benefit_rules": (*snapshot.benefit_rules, unresolved_rule)})
    with Session(engine) as session, session.begin():
        SqlAlchemyAdmissionBenefitsRepository(session).sync_snapshot(updated, source_run_id=RUN_ID)
    with Session(engine) as session:
        catalog = SqlAlchemyAdmissionBenefitsRepository(session).get_catalog(UNIVERSITY_ID, 2026)
        assert catalog is not None
        unresolved = next(rule for rule in catalog.benefit_rules if rule.id == "admission-benefit:unresolved")
        assert unresolved.scope.unresolved_targets[0].value == "неизвестный код"
