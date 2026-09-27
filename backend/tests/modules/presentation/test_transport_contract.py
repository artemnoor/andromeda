from __future__ import annotations

import pytest
from pydantic import ValidationError

from andromeda.modules.presentation.contracts.transport import ChannelKind, TransportInput


def test_future_max_transport_is_only_a_bounded_wire_contract() -> None:
    event = TransportInput(channel=ChannelKind.MAX, external_session_id="max-session-1", text="Где больше математики?")

    assert event.channel is ChannelKind.MAX
    assert event.capabilities.mini_app is False

    with pytest.raises(ValidationError):
        TransportInput(channel=ChannelKind.MAX, external_session_id="x", text="x" * 2001)
