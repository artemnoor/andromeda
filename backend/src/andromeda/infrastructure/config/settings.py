from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit

import logging


DEFAULT_DATABASE_URL = "sqlite:///./data/tracer.db"
DEFAULT_FRONTEND_ORIGIN = "http://localhost:5173"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENVIRONMENT = "test"
VALID_ENVIRONMENTS = frozenset(("test", "development", "staging"))

logger = logging.getLogger("andromeda.infrastructure.config")


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    frontend_origin: str = DEFAULT_FRONTEND_ORIGIN
    log_level: str = DEFAULT_LOG_LEVEL
    environment: str = DEFAULT_ENVIRONMENT
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800

    @classmethod
    def from_environment(cls, database_url: str | None = None) -> Settings:
        environment = os.environ.get("ANDROMEDA_ENV", DEFAULT_ENVIRONMENT).strip().lower()
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("ANDROMEDA_ENV must be one of: test, development, staging")
        selected_database_url = database_url or os.environ.get("BMSTU_DATABASE_URL", DEFAULT_DATABASE_URL)
        if environment in {"development", "staging"} and not is_postgresql_url(selected_database_url):
            raise ValueError(f"ANDROMEDA_ENV={environment} requires a PostgreSQL BMSTU_DATABASE_URL")

        settings = cls(
            database_url=selected_database_url,
            frontend_origin=os.environ.get("VITE_FRONTEND_ORIGIN", DEFAULT_FRONTEND_ORIGIN),
            log_level=os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            environment=environment,
            pool_size=_int_from_environment("BMSTU_DB_POOL_SIZE", 5),
            max_overflow=_int_from_environment("BMSTU_DB_MAX_OVERFLOW", 10),
            pool_timeout=_int_from_environment("BMSTU_DB_POOL_TIMEOUT", 30),
            pool_recycle=_int_from_environment("BMSTU_DB_POOL_RECYCLE", 1800),
        )
        logger.debug(
            "settings_loaded environment=%s dialect=%s database_target=%s log_level=%s",
            settings.environment,
            database_dialect(settings.database_url),
            redact_database_url(settings.database_url),
            settings.log_level,
        )
        return settings

    @property
    def engine_options(self) -> dict[str, int]:
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
        }


def _int_from_environment(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def database_dialect(database_url: str) -> str:
    return urlsplit(database_url).scheme.split("+", 1)[0].lower()


def is_postgresql_url(database_url: str) -> bool:
    return database_dialect(database_url) == "postgresql"


def redact_database_url(database_url: str) -> str:
    """Return a diagnostic target without credentials, query parameters, or SQLite paths."""
    parsed = urlsplit(database_url)
    dialect = database_dialect(database_url)
    if dialect == "sqlite":
        return "sqlite:///"
    if parsed.hostname is None:
        return f"{parsed.scheme}://<invalid-target>"
    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    port = f":{parsed.port}" if parsed.port is not None else ""
    database = unquote(parsed.path.removeprefix("/") or "<default>")
    return f"{parsed.scheme}://{host}{port}/{database}"
