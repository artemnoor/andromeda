from __future__ import annotations

from andromeda.infrastructure.jevql.adapter import JevQLAdapter
from andromeda.infrastructure.jevql.config import JevQLConfig
from andromeda.infrastructure.jevql.transport import PrivateProcessTransport
from andromeda.modules.analytics.contracts.semantic_predicate import (
    SemanticPredicate,
    SemanticPredicateRequest,
    SemanticPredicateRow,
    SemanticPredicateStatus,
)


def _request() -> SemanticPredicateRequest:
    return SemanticPredicateRequest(
        predicate=SemanticPredicate(
            definition_id="discipline-fit.v1",
            definition_version="semantic-taxonomy.v1",
            question="Does this discipline involve applied programming?",
            allowed_fields=("discipline_name",),
        ),
        rows=(SemanticPredicateRow(canonical_id="discipline:one", fields={"discipline_name": "Python"}),),
    )


class _FakeTransport:
    def __init__(self, available: bool, response: object) -> None:
        self._available = available
        self.response = response
        self.calls = 0

    def available(self) -> bool:
        return self._available

    def evaluate(self, request: SemanticPredicateRequest) -> object:
        self.calls += 1
        return self.response


def test_private_process_transport_is_not_selected_when_embedded_is_available() -> None:
    embedded = _FakeTransport(
        True,
        {"matches": {"discipline:one": True}, "confidence": 0.9},
    )
    private = _FakeTransport(True, {"matches": {}, "confidence": 0.0})
    result = JevQLAdapter(
        config=JevQLConfig(mode="auto"),
        embedded=embedded,
        private_process=private,
    ).evaluate(_request())

    assert result.status is SemanticPredicateStatus.AVAILABLE
    assert embedded.calls == 1
    assert private.calls == 0


def test_private_process_command_is_bounded_and_shell_free() -> None:
    transport = PrivateProcessTransport(("python", "-c", "print('{}')"), timeout_seconds=1)
    assert transport.available()
