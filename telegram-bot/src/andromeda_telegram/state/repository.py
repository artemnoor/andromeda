"""Encrypted, bot-local persistence for opaque backend session cookies."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


@dataclass(frozen=True, slots=True)
class AssistantSessionState:
    session_id: str
    revision: int


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
            connection.execute(
                "CREATE TABLE IF NOT EXISTS bot_sessions ("
                "owner_key TEXT PRIMARY KEY, cookie BLOB NOT NULL, updated_at TEXT NOT NULL, "
                "assistant_session_id TEXT, assistant_revision INTEGER)"
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(bot_sessions)")}
            if "assistant_session_id" not in columns:
                connection.execute("ALTER TABLE bot_sessions ADD COLUMN assistant_session_id TEXT")
            if "assistant_revision" not in columns:
                connection.execute("ALTER TABLE bot_sessions ADD COLUMN assistant_revision INTEGER")

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

    def get_assistant_state(self, owner_key: str) -> AssistantSessionState | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT assistant_session_id, assistant_revision FROM bot_sessions WHERE owner_key = ?",
                (owner_key,),
            ).fetchone()
        if row is None or row[0] is None or row[1] is None:
            return None
        return AssistantSessionState(session_id=str(row[0]), revision=int(row[1]))

    def save_assistant_state(self, owner_key: str, session_id: str, revision: int) -> None:
        if not session_id or revision < 1:
            raise ValueError("assistant session state is invalid")
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE bot_sessions SET assistant_session_id = ?, assistant_revision = ?, updated_at = datetime('now') WHERE owner_key = ?",
                (session_id, revision, owner_key),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5, isolation_level="IMMEDIATE")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection


__all__ = ["AssistantSessionState", "SessionRepository"]
