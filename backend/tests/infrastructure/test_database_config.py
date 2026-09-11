from __future__ import annotations

import logging

import pytest

from andromeda.infrastructure.config import Settings, database_dialect, redact_database_url
from andromeda.infrastructure.database import create_engine_for_url


def test_settings_keep_sqlite_for_explicit_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANDROMEDA_ENV", "test")
    monkeypatch.delenv("BMSTU_DATABASE_URL", raising=False)

    settings = Settings.from_environment()

    assert settings.database_url.startswith("sqlite:///")
    assert settings.environment == "test"


def test_development_requires_postgresql(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANDROMEDA_ENV", "development")
    monkeypatch.setenv("BMSTU_DATABASE_URL", "sqlite:///./data/not-dev.db")

    with pytest.raises(ValueError, match="requires a PostgreSQL"):
        Settings.from_environment()


def test_postgresql_settings_are_redacted_and_parseable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANDROMEDA_ENV", "staging")
    database_url = "postgresql+psycopg://user:p%40ss@example.test:5432/andromeda_staging?sslmode=require"
    monkeypatch.setenv("BMSTU_DATABASE_URL", database_url)

    settings = Settings.from_environment()

    assert database_dialect(settings.database_url) == "postgresql"
    assert redact_database_url(settings.database_url) == "postgresql+psycopg://example.test:5432/andromeda_staging"
    assert "p%40ss" not in redact_database_url(settings.database_url)


def test_sqlite_engine_keeps_foreign_key_pragma(tmp_path) -> None:
    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'config.db').as_posix()}")
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    finally:
        engine.dispose()


def test_settings_emit_safe_debug_diagnostic(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setenv("ANDROMEDA_ENV", "staging")
    monkeypatch.setenv("BMSTU_DATABASE_URL", "postgresql+psycopg://user:secret@example.test/andromeda")
    with caplog.at_level(logging.DEBUG, logger="andromeda.infrastructure.config"):
        Settings.from_environment()

    assert "secret" not in caplog.text
    assert "settings_loaded" in caplog.text
