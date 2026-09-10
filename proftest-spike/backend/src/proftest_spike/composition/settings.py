"""Environment-backed Spike settings with safe defaults."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    andromeda_api_base_url: str = "http://127.0.0.1:8000"
    spike_cors_origin: str = "http://127.0.0.1:5174"
    log_level: str = "INFO"
    http_timeout_seconds: float = 15.0
    max_programs: int = 500
    catalog_cache_ttl_seconds: float = 300.0

    @classmethod
    def from_environment(cls) -> "Settings":
        defaults = cls()
        return cls(
            andromeda_api_base_url=os.getenv("ANDROMEDA_API_BASE_URL", defaults.andromeda_api_base_url).rstrip("/"),
            spike_cors_origin=os.getenv("SPIKE_CORS_ORIGIN", defaults.spike_cors_origin),
            log_level=os.getenv("LOG_LEVEL", defaults.log_level).upper(),
            http_timeout_seconds=_positive_float(os.getenv("SPIKE_HTTP_TIMEOUT_SECONDS"), defaults.http_timeout_seconds),
            max_programs=_positive_int(os.getenv("SPIKE_MAX_PROGRAMS"), defaults.max_programs),
            catalog_cache_ttl_seconds=_positive_float(os.getenv("SPIKE_CATALOG_CACHE_TTL_SECONDS"), defaults.catalog_cache_ttl_seconds),
        )


def configure_logging(level: str) -> None:
    """Configure controllable verbose logging for local Spike runs."""

    normalized = level.upper()
    numeric_level = getattr(logging, normalized, logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger().setLevel(numeric_level)


def _positive_float(raw_value: str | None, default: float) -> float:
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _positive_int(raw_value: str | None, default: int) -> int:
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


__all__ = ["Settings", "configure_logging"]
