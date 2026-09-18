"""Encrypted, bot-local persistence for opaque backend session cookies."""

from __future__ import annotations

from pathlib import Path
import sqlite3
import threading

from cryptography.fernet import Fernet, InvalidToken


class SessionRepository:
    """Store only an encrypted opaque cookie per private Telegram transport key."""

    def __init__(self, path: Path, encryption_key: str) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fernet = Fernet(encryption_key.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise ValueError("ANDROMEDA_SESSION_ENCRYPTION_KEY must be a valid Fernet key") from exc
        self._lock = threading.RLock()
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS bot_sessions (owner_key TEXT PRIMARY KEY, cookie BLOB NOT NULL, updated_at TEXT NOT NULL)")

    def get_cookie(self, owner_key: str) -> str | None:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT cookie FROM bot_sessions WHERE owner_key = ?", (owner_key,)).fetchone()
        if row is None:
            return None
        try:
            return self._fernet.decrypt(bytes(row[0])).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError) as exc:
            raise RuntimeError("stored bot session could not be decrypted") from exc

    def save_cookie(self, owner_key: str, cookie: str) -> None:
        if not cookie or len(cookie) > 4096:
            raise ValueError("session cookie is empty or too large")
        encrypted = self._fernet.encrypt(cookie.encode("utf-8"))
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO bot_sessions(owner_key, cookie, updated_at) VALUES (?, ?, datetime('now')) "
                "ON CONFLICT(owner_key) DO UPDATE SET cookie = excluded.cookie, updated_at = excluded.updated_at",
                (owner_key, encrypted),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5, isolation_level="IMMEDIATE")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection


__all__ = ["SessionRepository"]
