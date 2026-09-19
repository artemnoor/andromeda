"""Environment-backed configuration with fail-fast secret validation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    backend_url: str
    renderer_url: str
    render_hmac_secret: str
    session_encryption_key: str
    web_app_url: str
    session_db: Path
    log_level: str = "INFO"
    request_timeout_seconds: float = 15.0
    render_timeout_seconds: float = 20.0
    request_retry_attempts: int = 2
    request_retry_backoff_seconds: float = 0.25
    session_cookie_name: str = "andromeda_profile_session"

    @classmethod
    def from_env(cls) -> "Settings":
        bot_token = _required("TELEGRAM_BOT_TOKEN")
        backend_url = _url("ANDROMEDA_BACKEND_URL", "http://backend:8020")
        renderer_url = _url("ANDROMEDA_RENDERER_URL", "http://frontend:3000")
        render_hmac_secret = _required("ANDROMEDA_RENDER_HMAC_SECRET")
        session_encryption_key = _required("ANDROMEDA_SESSION_ENCRYPTION_KEY")
        web_app_url = _url("ANDROMEDA_WEB_APP_URL", "http://localhost:3000")
        session_db = Path(os.getenv("ANDROMEDA_SESSION_DB", "./data/telegram.sqlite3"))
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        request_timeout = float(os.getenv("ANDROMEDA_REQUEST_TIMEOUT_SECONDS", "15"))
        render_timeout = float(os.getenv("ANDROMEDA_RENDER_TIMEOUT_SECONDS", "20"))
        request_retry_attempts = int(os.getenv("ANDROMEDA_REQUEST_RETRY_ATTEMPTS", "2"))
        request_retry_backoff = float(os.getenv("ANDROMEDA_REQUEST_RETRY_BACKOFF_SECONDS", "0.25"))
        if request_timeout <= 0 or render_timeout <= 0:
            raise ValueError("HTTP timeouts must be positive")
        if not 1 <= request_retry_attempts <= 3 or not 0 <= request_retry_backoff <= 5:
            raise ValueError("HTTP retry policy must be bounded")
        return cls(
            bot_token=bot_token,
            backend_url=backend_url,
            renderer_url=renderer_url,
            render_hmac_secret=render_hmac_secret,
            session_encryption_key=session_encryption_key,
            web_app_url=web_app_url,
            session_db=session_db,
            log_level=log_level,
            request_timeout_seconds=request_timeout,
            render_timeout_seconds=render_timeout,
            request_retry_attempts=request_retry_attempts,
            request_retry_backoff_seconds=request_retry_backoff,
        )


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _url(name: str, default: str) -> str:
    value = os.getenv(name, default).strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        raise ValueError(f"{name} must be an absolute HTTP URL")
    return value


__all__ = ["Settings"]
