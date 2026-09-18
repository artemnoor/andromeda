from __future__ import annotations

from andromeda_telegram.state.callbacks import CallbackPayload, CallbackStore


def test_callback_token_is_short_expiring_and_owner_bound() -> None:
    now = [0.0]
    store = CallbackStore(ttl_seconds=10, clock=lambda: now[0])
    token = store.issue("user-a", CallbackPayload(action="details", program_ids=("program:01",)))

    assert len(token.encode("utf-8")) <= 64
    assert store.consume("user-b", token) is None
    assert store.consume("user-a", token) is not None
    assert store.consume("user-a", token) is None

    expired = store.issue("user-a", CallbackPayload(action="details"))
    now[0] = 11
    assert store.consume("user-a", expired) is None
