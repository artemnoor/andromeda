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
        assert "venue_university_links" in inspector.get_table_names()
        assert "venue_department_links" in inspector.get_table_names()
        assert "venue_program_links" in inspector.get_table_names()
        profile_columns = {column["name"] for column in inspector.get_columns("user_profiles")}
        assert {"profile_id", "session_key_hash", "profile_json", "revision", "expires_at"}.issubset(profile_columns)
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

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        assert "subject_group" not in {column["name"] for column in inspect(engine).get_columns("curriculum_items")}
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
