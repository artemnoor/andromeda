from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_DATABASE_URL = "sqlite:///./data/tracer.db"
DEFAULT_FRONTEND_ORIGIN = "http://localhost:5173"
DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    frontend_origin: str = DEFAULT_FRONTEND_ORIGIN
    log_level: str = DEFAULT_LOG_LEVEL

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            database_url=os.environ.get("BMSTU_DATABASE_URL", DEFAULT_DATABASE_URL),
            frontend_origin=os.environ.get("VITE_FRONTEND_ORIGIN", DEFAULT_FRONTEND_ORIGIN),
            log_level=os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
        )
