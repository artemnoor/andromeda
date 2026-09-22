from __future__ import annotations

from types import SimpleNamespace

from andromeda.infrastructure.jevql.adapter import JevQLAdapter
from andromeda.infrastructure.jevql.config import JevQLConfig
from andromeda.infrastructure.jevql.transport import EmbeddedTransport, SharedServiceTransport
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


def test_shared_service_is_not_selected_when_embedded_is_available() -> None:
    embedded = _FakeTransport(
        True,
        {"matches": {"discipline:one": True}, "confidence": 0.9},
    )
    shared = _FakeTransport(True, {"matches": {}, "confidence": 0.0})
    result = JevQLAdapter(
        config=JevQLConfig(mode="auto"),
        embedded=embedded,
        shared_service=shared,
    ).evaluate(_request())

    assert result.status is SemanticPredicateStatus.AVAILABLE
    assert embedded.calls == 1
    assert shared.calls == 0


def test_embedded_transport_calls_upstream_jevql_judge_api() -> None:
    class UpstreamClient:
        def judge(self, question, rows, *, kind, raw):
            assert question.startswith("Does this")
            assert rows[0]["canonical_id"] == "discipline:one"
            assert kind == "bool"
            assert raw is True
            return SimpleNamespace(
                answers=[SimpleNamespace(passed=True, confidence=0.91)],
            )

    transport = EmbeddedTransport(client_factory=UpstreamClient)
    result = transport.evaluate(_request())

    assert result["matches"] == {"discipline:one": True}
    assert result["provider"] == "jevql"


def test_shared_transport_constructs_upstream_jevql_url_client() -> None:
    captured = {}

    class UpstreamClient:
        def judge(self, question, rows, *, kind, raw):
            return SimpleNamespace(answers=[SimpleNamespace(passed=False, confidence=0.8)])

    def factory():
        captured["constructed"] = True
        return UpstreamClient()

    transport = SharedServiceTransport(
        JevQLConfig(mode="shared_service", shared_endpoint="http://jevql:7433", shared_allowed_hosts=("jevql",)),
        client_factory=factory,
    )
    result = transport.evaluate(_request())

    assert captured["constructed"] is True
    assert result["matches"] == {"discipline:one": False}
