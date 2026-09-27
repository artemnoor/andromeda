from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet

from andromeda_telegram.state.repository import SessionRepository


def test_session_cookie_is_encrypted_and_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    repository = SessionRepository(path, Fernet.generate_key().decode())

    repository.save_cookie("telegram-user-key", "opaque-cookie-value")

    assert repository.get_cookie("telegram-user-key") == "opaque-cookie-value"
    assert b"opaque-cookie-value" not in path.read_bytes()


def test_assistant_session_state_is_stored_alongside_the_opaque_cookie(tmp_path: Path) -> None:
    repository = SessionRepository(tmp_path / "state.sqlite3", Fernet.generate_key().decode())
    repository.save_cookie("telegram-user-key", "opaque-cookie-value")

    repository.save_assistant_state("telegram-user-key", "query-session:" + "b" * 32, 3)

    state = repository.get_assistant_state("telegram-user-key")
    assert state is not None
    assert state.session_id == "query-session:" + "b" * 32
    assert state.revision == 3
