from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


BACKEND_ROOT = Path(__file__).parents[2]


def _alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def test_empty_sqlite_database_reaches_head_and_preserves_constraints(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'migrations.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)

    command.upgrade(_alembic_config("sqlite:///ignored-by-environment.db"), "head")

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert "educational_programs" in inspector.get_table_names()
        assert "discipline_areas" in inspector.get_table_names()
        assert "user_profiles" in inspector.get_table_names()
        assert "decision_contexts" in inspector.get_table_names()
        assert "decision_analytics_events" in inspector.get_table_names()
        assert "venue_university_links" in inspector.get_table_names()
        assert "venue_department_links" in inspector.get_table_names()
        assert "venue_program_links" in inspector.get_table_names()
        assert "university_admin_memberships" in inspector.get_table_names()
        assert {
            "university_units",
            "university_categories",
            "university_program_editorials",
            "university_discipline_editorials",
            "university_category_program_links",
            "university_category_discipline_links",
            "university_unit_program_links",
            "university_unit_discipline_links",
            "university_editorial_events",
            "university_editorial_agenda_items",
            "university_editorial_event_unit_links",
            "university_editorial_event_program_links",
            "university_editorial_event_category_links",
        }.issubset(set(inspector.get_table_names()))
        membership_columns = {column["name"] for column in inspector.get_columns("university_admin_memberships")}
        assert {
            "membership_id",
            "account_id",
            "university_id",
            "role",
            "status",
            "revision",
            "created_at",
            "updated_at",
            "granted_by_account_id",
            "revoked_at",
        }.issubset(membership_columns)
        assert "ix_university_admin_memberships_university_status" in {
            index["name"] for index in inspector.get_indexes("university_admin_memberships")
        }
        profile_columns = {column["name"] for column in inspector.get_columns("user_profiles")}
        assert {"profile_id", "session_key_hash", "profile_json", "revision", "expires_at"}.issubset(profile_columns)
        decision_columns = {column["name"] for column in inspector.get_columns("decision_contexts")}
        assert {"decision_id", "owner_key", "state_json", "revision", "expires_at"}.issubset(decision_columns)
        columns = {column["name"] for column in inspector.get_columns("curriculum_items")}
        assert {"source_name", "semester_identity"}.issubset(columns)
        assert "subject_group" not in columns
        venue_columns = {column["name"] for column in inspector.get_columns("venues")}
        assert "point_type" in venue_columns
        unique_names = {constraint["name"] for constraint in inspector.get_unique_constraints("curriculum_items")}
        assert "uq_curriculum_item_identity" in unique_names
        passing_columns = {column["name"] for column in inspector.get_columns("admission_passing_scores")}
        assert {"competition_type", "status", "score"}.issubset(passing_columns)
        passing_unique = next(
            constraint for constraint in inspector.get_unique_constraints("admission_passing_scores")
            if constraint["name"] == "uq_admission_passing_score_identity"
        )
        assert passing_unique["column_names"] == ["offering_id", "competition_type", "status", "score_type"]
        program_columns = {column["name"] for column in inspector.get_columns("educational_programs")}
        assert {"provenance_json", "source_gaps_json"}.issubset(program_columns)
        curriculum_columns = {column["name"] for column in inspector.get_columns("curricula")}
        assert {"provenance_json", "source_gaps_json"}.issubset(curriculum_columns)
        admission_columns = {column["name"] for column in inspector.get_columns("admission_offerings")}
        assert {"university_id", "run_id", "field", "record_key", "inferred"}.issubset(admission_columns)
        ingest_columns = {column["name"] for column in inspector.get_columns("ingest_runs")}
        assert {"projection_target", "heartbeat_at", "projection_status", "recovery_reason"}.issubset(ingest_columns)
        ingest_indexes = {index["name"] for index in inspector.get_indexes("ingest_runs")}
        assert ingest_indexes >= {"ix_ingest_runs_status_started_at", "uq_ingest_runs_active_identity"}
        active_index = next(index for index in inspector.get_indexes("ingest_runs") if index["name"] == "uq_ingest_runs_active_identity")
        assert active_index["column_names"] == ["university_id", "source_profile", "projection_target"]
        assert {index["name"] for index in inspector.get_indexes("source_snapshots")} >= {"ix_source_snapshots_ingest_run_id"}
    finally:
        engine.dispose()


def test_current_0016_database_reaches_current_head(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'from-0016.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)
    config = _alembic_config(database_url)
    command.upgrade(config, "0016_ingestion_source_health")
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert "provenance_json" in {column["name"] for column in inspector.get_columns("educational_programs")}
        assert "university_id" in {column["name"] for column in inspector.get_columns("admission_offerings")}
        assert "uq_ingest_runs_active_identity" in {
            index["name"] for index in inspector.get_indexes("ingest_runs")
        }
    finally:
        engine.dispose()


def test_neutral_curriculum_migration_removes_legacy_category_column(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'neutral-curriculum.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)
    config = _alembic_config(database_url)

    command.upgrade(config, "0011_proftest_sessions")
    engine = create_engine(database_url)
    try:
        assert "subject_group" in {column["name"] for column in inspect(engine).get_columns("curriculum_items")}
    finally:
        engine.dispose()


def test_decision_context_migration_round_trip_is_reversible(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'decision-migration.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)
    config = _alembic_config(database_url)

    command.upgrade(config, "0012_neutral_curriculum_items")
    command.upgrade(config, "0013_decision_context")
    engine = create_engine(database_url)
    try:
        assert "decision_contexts" in inspect(engine).get_table_names()
    finally:
        engine.dispose()

    command.downgrade(config, "0012_neutral_curriculum_items")
    engine = create_engine(database_url)
    try:
        assert "decision_contexts" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        assert "decision_contexts" in inspect(engine).get_table_names()
    finally:
        engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        assert "subject_group" not in {column["name"] for column in inspect(engine).get_columns("curriculum_items")}
    finally:
        engine.dispose()


def test_decision_analytics_migration_round_trip_is_reversible(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'decision-analytics-migration.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)
    config = _alembic_config(database_url)

    command.upgrade(config, "0013_decision_context")
    command.upgrade(config, "0014_decision_analytics")
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert "decision_analytics_events" in inspector.get_table_names()
        primary_key = inspector.get_pk_constraint("decision_analytics_events")
        assert primary_key["constrained_columns"] == ["owner_key", "event_id"]
    finally:
        engine.dispose()

    command.downgrade(config, "0013_decision_context")
    engine = create_engine(database_url)
    try:
        assert "decision_analytics_events" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        assert "decision_analytics_events" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_auth_downgrade_refuses_account_owned_profile(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'auth-downgrade.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)
    config = _alembic_config(database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO user_profiles (profile_id, session_key_hash, account_id, profile_json, revision, created_at, updated_at, expires_at) "
                    "VALUES (:profile_id, NULL, :account_id, :profile_json, 1, :created_at, :updated_at, :expires_at)"
                ),
                {
                    "profile_id": "profile:" + "a" * 32,
                    "account_id": "account:" + "b" * 32,
                    "profile_json": "{}",
                    "created_at": "2026-01-01 00:00:00",
                    "updated_at": "2026-01-01 00:00:00",
                    "expires_at": "2027-01-01 00:00:00",
                },
            )
        with pytest.raises(RuntimeError, match="account-owned profiles"):
            command.downgrade(config, "0008_admin_ops_ingest_audit")
    finally:
        engine.dispose()


def test_sqlite_migration_chain_can_downgrade_to_base(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'migration-round-trip.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)

    config = _alembic_config("sqlite:///ignored-by-environment.db")
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(database_url)
    try:
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        engine.dispose()


def test_route_migration_backfills_existing_numeric_scores(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'route-backfill.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)
    config = _alembic_config(database_url)
    command.upgrade(config, "0009_auth_profile_binding")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO education_levels (id) VALUES ('bachelor')"))
            connection.execute(
                text("INSERT INTO universities (id, name, city, official_site, address) VALUES ('university:bmstu', 'BMSTU', 'Москва', 'https://bmstu.ru/', 'Москва')")
            )
            connection.execute(
                text("INSERT INTO directions (id, university_id, code, name, education_level) VALUES ('direction:09.03.01', 'university:bmstu', '09.03.01', 'Информатика', 'bachelor')")
            )
            connection.execute(
                text("INSERT INTO educational_programs (id, direction_id, code, name, education_year, study_plan_url, source_url) VALUES ('program:09.03.01-02', 'direction:09.03.01', '09.03.01-02', 'Профиль', 2026, 'https://bmstu.ru/plan.pdf', 'https://bmstu.ru/program')")
            )
            connection.execute(
                text("INSERT INTO admission_offerings (id, program_id, admission_year, study_form, funding_type, scope, source_kind, source_url, captured_at, content_sha256) VALUES ('admission-offering:legacy', 'program:09.03.01-02', 2026, 'full_time', 'budget', 'direction', 'detail', 'https://bmstu.ru/admissions', '2026-01-01 00:00:00', :digest)"),
                {"digest": "a" * 64},
            )
            connection.execute(
                text("INSERT INTO admission_passing_scores (id, offering_id, score_type, score, source_kind, source_url, captured_at, content_sha256) VALUES ('passing:legacy', 'admission-offering:legacy', 'budget', 231, 'detail', 'https://bmstu.ru/admissions', '2026-01-01 00:00:00', :digest)"),
                {"digest": "b" * 64},
            )
        command.upgrade(config, "head")
        row = engine.connect().execute(
            text("SELECT competition_type, status, score FROM admission_passing_scores WHERE id = 'passing:legacy'")
        ).one()
        assert tuple(row) == ("general", "numeric", 231)
    finally:
        engine.dispose()


def test_university_scoped_identity_migrates_bmstu_and_allows_hse_collision_free(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'scoped-identity.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)
    config = _alembic_config(database_url)
    command.upgrade(config, "0014_decision_analytics")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO education_levels (id) VALUES ('bachelor')"))
            connection.execute(
                text("INSERT INTO universities (id, name, city, official_site, address) VALUES ('university:bmstu', 'BMSTU', 'Москва', 'https://bmstu.ru/', 'Москва')")
            )
            connection.execute(
                text("INSERT INTO universities (id, name, city, official_site, address) VALUES ('university:hse', 'HSE', 'Москва', 'https://hse.ru/', 'Москва')")
            )
            connection.execute(
                text("INSERT INTO directions (id, university_id, code, name, education_level) VALUES ('direction:09.03.01', 'university:bmstu', '09.03.01', 'Информатика', 'bachelor')")
            )
            connection.execute(
                text("INSERT INTO educational_programs (id, direction_id, code, name, education_year, study_plan_url, source_url) VALUES ('program:09.03.01-02', 'direction:09.03.01', '09.03.01-02', 'Профиль', 2026, 'https://bmstu.ru/plan.pdf', 'https://bmstu.ru/program')")
            )

        command.upgrade(config, "head")
        with engine.begin() as connection:
            assert connection.execute(text("SELECT id FROM directions WHERE university_id = 'university:bmstu'")).scalar_one() == "direction:bmstu:09.03.01"
            assert connection.execute(text("SELECT id FROM educational_programs WHERE direction_id = 'direction:bmstu:09.03.01'")).scalar_one() == "program:bmstu:09.03.01-02"
            connection.execute(
                text("INSERT INTO directions (id, university_id, code, name, education_level) VALUES ('direction:hse:09.03.01', 'university:hse', '09.03.01', 'Информатика', 'bachelor')")
            )
            connection.execute(
                text("INSERT INTO educational_programs (id, direction_id, code, name, education_year, study_plan_url, source_url) VALUES ('program:hse:09.03.01-02', 'direction:hse:09.03.01', '09.03.01-02', 'Профиль HSE', 2026, 'https://hse.ru/plan.pdf', 'https://hse.ru/program')")
            )
            rows = connection.execute(text("SELECT id FROM educational_programs ORDER BY id")).scalars().all()
            assert rows == ["program:bmstu:09.03.01-02", "program:hse:09.03.01-02"]
    finally:
        engine.dispose()


def test_environment_url_is_used_for_alembic_even_when_ini_differs(tmp_path: Path, monkeypatch) -> None:
    target_url = f"sqlite:///{(tmp_path / 'environment-target.db').as_posix()}"
    ignored_url = f"sqlite:///{(tmp_path / 'ini-target.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.setenv("BMSTU_DATABASE_URL", target_url)

    command.upgrade(_alembic_config(ignored_url), "head")

    target_engine = create_engine(target_url)
    ignored_engine = create_engine(ignored_url)
    try:
        assert "alembic_version" in inspect(target_engine).get_table_names()
        assert "alembic_version" not in inspect(ignored_engine).get_table_names()
    finally:
        target_engine.dispose()
        ignored_engine.dispose()


def test_alembic_uses_config_url_when_environment_url_is_unset(tmp_path: Path, monkeypatch) -> None:
    configured_url = f"sqlite:///{(tmp_path / 'configured-target.db').as_posix()}"
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.delenv("BMSTU_DATABASE_URL", raising=False)

    command.upgrade(_alembic_config(configured_url), "head")

    engine = create_engine(configured_url)
    try:
        assert "alembic_version" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
