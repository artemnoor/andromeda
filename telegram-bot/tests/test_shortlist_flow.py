from __future__ import annotations

from andromeda_telegram.handlers.keyboards import image_actions
from andromeda_telegram.state.callbacks import CallbackStore


def test_shortlist_image_actions_keep_callbacks_opaque_and_short() -> None:
    store = CallbackStore()
    markup = image_actions("telegram:42", ("program:01", "program:02"), store, "https://andromeda.example")
    callbacks = [button.callback_data for row in markup.inline_keyboard for button in row if button.callback_data]

    assert callbacks
    assert all(len(callback.encode("utf-8")) <= 64 for callback in callbacks)
    assert all("program:01" not in callback for callback in callbacks)
