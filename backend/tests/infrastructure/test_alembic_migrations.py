from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


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
        venue_columns = {column["name"] for column in inspector.get_columns("venues")}
        assert "point_type" in venue_columns
        unique_names = {constraint["name"] for constraint in inspector.get_unique_constraints("curriculum_items")}
        assert "uq_curriculum_item_identity" in unique_names
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
