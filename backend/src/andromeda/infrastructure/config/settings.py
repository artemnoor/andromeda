from __future__ import annotations

import os
from dataclasses import dataclass
import re
from urllib.parse import unquote, urlsplit

import logging


DEFAULT_DATABASE_URL = "sqlite:///./data/andromeda.db"
DEFAULT_FRONTEND_ORIGIN = "http://localhost:3000,http://127.0.0.1:3000"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENVIRONMENT = "test"
DEFAULT_PROFILE_COOKIE_NAME = "andromeda_profile_session"
DEFAULT_PROFILE_COOKIE_MAX_AGE = 60 * 60 * 24 * 30
DEFAULT_PROFILE_TTL_SECONDS = 60 * 60 * 24 * 30
DEFAULT_AUTH_COOKIE_NAME = "andromeda_auth_session"
DEFAULT_AUTH_COOKIE_MAX_AGE = 60 * 60 * 24 * 30
DEFAULT_AUTH_SESSION_TTL_SECONDS = 60 * 60 * 24 * 30
DEFAULT_AUTH_PASSWORD_MIN_LENGTH = 12
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_AUTH_RATE_LIMIT_MAX = 10
DEFAULT_SENSITIVE_RATE_LIMIT_MAX = 120
DEFAULT_OPS_RATE_LIMIT_MAX = 10
VALID_ENVIRONMENTS = frozenset(("test", "development", "staging", "production"))
VALID_SAMESITE_VALUES = frozenset(("lax", "strict", "none"))

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
    profile_cookie_name: str = DEFAULT_PROFILE_COOKIE_NAME
    profile_cookie_max_age: int = DEFAULT_PROFILE_COOKIE_MAX_AGE
    profile_cookie_secure: bool = False
    profile_cookie_samesite: str = "lax"
    profile_ttl_seconds: int = DEFAULT_PROFILE_TTL_SECONDS
    auth_cookie_name: str = DEFAULT_AUTH_COOKIE_NAME
    auth_cookie_max_age: int = DEFAULT_AUTH_COOKIE_MAX_AGE
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    auth_session_ttl_seconds: int = DEFAULT_AUTH_SESSION_TTL_SECONDS
    auth_password_min_length: int = DEFAULT_AUTH_PASSWORD_MIN_LENGTH
    rate_limit_window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW_SECONDS
    auth_rate_limit_max: int = DEFAULT_AUTH_RATE_LIMIT_MAX
    sensitive_rate_limit_max: int = DEFAULT_SENSITIVE_RATE_LIMIT_MAX
    ops_rate_limit_max: int = DEFAULT_OPS_RATE_LIMIT_MAX
    ops_api_key: str | None = None
    ingestion_min_relative_count: float = 0.25
    ingestion_run_timeout_seconds: int = 30 * 60

    @classmethod
    def from_environment(cls, database_url: str | None = None) -> Settings:
        environment = os.environ.get("ANDROMEDA_ENV", DEFAULT_ENVIRONMENT).strip().lower()
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("ANDROMEDA_ENV must be one of: test, development, staging, production")
        selected_database_url = database_url or _environment_with_legacy_fallback(
            "ANDROMEDA_DATABASE_URL",
            "BMSTU_DATABASE_URL",
            DEFAULT_DATABASE_URL,
        )
        if environment in {"development", "staging"} and not is_postgresql_url(selected_database_url):
            raise ValueError(f"ANDROMEDA_ENV={environment} requires a PostgreSQL ANDROMEDA_DATABASE_URL")
        if environment == "production" and not is_postgresql_url(selected_database_url):
            raise ValueError("ANDROMEDA_ENV=production requires a PostgreSQL ANDROMEDA_DATABASE_URL")

        configured_frontend_origin = os.environ.get("FRONTEND_ORIGIN")
        ops_api_key = _optional_secret_from_environment("ANDROMEDA_OPS_API_KEY")
        if environment in {"staging", "production"}:
            if not configured_frontend_origin or not configured_frontend_origin.strip():
                raise ValueError(f"ANDROMEDA_ENV={environment} requires an explicit FRONTEND_ORIGIN")
            if ops_api_key is None:
                raise ValueError(f"ANDROMEDA_ENV={environment} requires ANDROMEDA_OPS_API_KEY")
            if len(ops_api_key) < 16:
                raise ValueError("ANDROMEDA_OPS_API_KEY must contain at least 16 characters")

        settings = cls(
            database_url=selected_database_url,
            frontend_origin=configured_frontend_origin or DEFAULT_FRONTEND_ORIGIN,
            log_level=os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            environment=environment,
            pool_size=_int_from_environment_with_legacy("ANDROMEDA_DB_POOL_SIZE", "BMSTU_DB_POOL_SIZE", 5),
            max_overflow=_int_from_environment_with_legacy("ANDROMEDA_DB_MAX_OVERFLOW", "BMSTU_DB_MAX_OVERFLOW", 10),
            pool_timeout=_int_from_environment_with_legacy("ANDROMEDA_DB_POOL_TIMEOUT", "BMSTU_DB_POOL_TIMEOUT", 30),
            pool_recycle=_int_from_environment_with_legacy("ANDROMEDA_DB_POOL_RECYCLE", "BMSTU_DB_POOL_RECYCLE", 1800),
            profile_cookie_name=os.environ.get("ANDROMEDA_PROFILE_COOKIE_NAME", DEFAULT_PROFILE_COOKIE_NAME),
            profile_cookie_max_age=_positive_int_from_environment("ANDROMEDA_PROFILE_COOKIE_MAX_AGE", DEFAULT_PROFILE_COOKIE_MAX_AGE),
            profile_cookie_secure=_bool_from_environment("ANDROMEDA_PROFILE_COOKIE_SECURE", environment in {"staging", "production"}),
            profile_cookie_samesite=_samesite_from_environment("ANDROMEDA_PROFILE_COOKIE_SAMESITE"),
            profile_ttl_seconds=_positive_int_from_environment("ANDROMEDA_PROFILE_TTL_SECONDS", DEFAULT_PROFILE_TTL_SECONDS),
            auth_cookie_name=os.environ.get("ANDROMEDA_AUTH_COOKIE_NAME", DEFAULT_AUTH_COOKIE_NAME),
            auth_cookie_max_age=_positive_int_from_environment("ANDROMEDA_AUTH_COOKIE_MAX_AGE", DEFAULT_AUTH_COOKIE_MAX_AGE),
            auth_cookie_secure=_bool_from_environment("ANDROMEDA_AUTH_COOKIE_SECURE", environment in {"staging", "production"}),
            auth_cookie_samesite=_samesite_from_environment("ANDROMEDA_AUTH_COOKIE_SAMESITE"),
            auth_session_ttl_seconds=_positive_int_from_environment("ANDROMEDA_AUTH_SESSION_TTL_SECONDS", DEFAULT_AUTH_SESSION_TTL_SECONDS),
            auth_password_min_length=_positive_int_from_environment("ANDROMEDA_AUTH_PASSWORD_MIN_LENGTH", DEFAULT_AUTH_PASSWORD_MIN_LENGTH),
            rate_limit_window_seconds=_positive_int_from_environment("ANDROMEDA_RATE_LIMIT_WINDOW_SECONDS", DEFAULT_RATE_LIMIT_WINDOW_SECONDS),
            auth_rate_limit_max=_positive_int_from_environment("ANDROMEDA_AUTH_RATE_LIMIT_MAX", DEFAULT_AUTH_RATE_LIMIT_MAX),
            sensitive_rate_limit_max=_positive_int_from_environment("ANDROMEDA_SENSITIVE_RATE_LIMIT_MAX", DEFAULT_SENSITIVE_RATE_LIMIT_MAX),
            ops_rate_limit_max=_positive_int_from_environment("ANDROMEDA_OPS_RATE_LIMIT_MAX", DEFAULT_OPS_RATE_LIMIT_MAX),
            ops_api_key=ops_api_key,
            ingestion_min_relative_count=_ratio_from_environment("ANDROMEDA_INGEST_MIN_RELATIVE_COUNT", 0.25),
            ingestion_run_timeout_seconds=_positive_int_from_environment("ANDROMEDA_INGEST_RUN_TIMEOUT_SECONDS", 30 * 60),
        )
        _validate_cookie_settings(settings.profile_cookie_name, settings.profile_cookie_samesite, settings.profile_cookie_secure, "ANDROMEDA_PROFILE_COOKIE_NAME")
        _validate_cookie_settings(settings.auth_cookie_name, settings.auth_cookie_samesite, settings.auth_cookie_secure, "ANDROMEDA_AUTH_COOKIE_NAME")
        if environment in {"staging", "production"}:
            if not settings.profile_cookie_secure or not settings.auth_cookie_secure:
                raise ValueError(f"ANDROMEDA_ENV={environment} requires secure profile and auth cookies")
            if environment == "production" and any(
                not origin.strip().lower().startswith("https://")
                for origin in settings.frontend_origin.split(",")
                if origin.strip()
            ):
                raise ValueError("ANDROMEDA_ENV=production requires HTTPS FRONTEND_ORIGIN values")
        logger.debug(
            "settings_loaded environment=%s dialect=%s database_target=%s log_level=%s profile_cookie_secure=%s profile_cookie_samesite=%s profile_ttl_seconds=%d",
            settings.environment,
            database_dialect(settings.database_url),
            redact_database_url(settings.database_url),
            settings.log_level,
            settings.profile_cookie_secure,
            settings.profile_cookie_samesite,
            settings.profile_ttl_seconds,
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


def _environment_with_legacy_fallback(primary: str, legacy: str, default: str) -> str:
    value = os.environ.get(primary)
    if value is not None:
        return value
    legacy_value = os.environ.get(legacy)
    if legacy_value is not None:
        logger.warning("deprecated_environment_used primary=%s legacy=%s", primary, legacy)
        return legacy_value
    return default


def _int_from_environment_with_legacy(primary: str, legacy: str, default: int) -> int:
    value = _environment_with_legacy_fallback(primary, legacy, str(default))
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{primary} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{primary} must be non-negative")
    return parsed


def _positive_int_from_environment(name: str, default: int) -> int:
    value = _int_from_environment(name, default)
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def _ratio_from_environment(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


def _bool_from_environment(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _samesite_from_environment(name: str) -> str:
    value = os.environ.get(name, "lax").strip().lower()
    if value not in VALID_SAMESITE_VALUES:
        raise ValueError(f"{name} must be one of: lax, strict, none")
    return value


def _optional_secret_from_environment(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _validate_cookie_settings(name: str, samesite: str, secure: bool, env_name: str) -> None:
    if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name) is None:
        raise ValueError(f"{env_name} must contain only safe cookie name characters")
    if samesite == "none" and not secure:
        raise ValueError(f"{env_name.removesuffix('_NAME')}_SECURE must be true when SameSite=None")


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
