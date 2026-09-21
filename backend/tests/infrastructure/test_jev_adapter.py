from __future__ import annotations

from typing import Mapping

from andromeda.infrastructure.jev.adapter import JevAdapterConfig, JevDecisionModelAdapter
from andromeda.modules.conversation.services.decision_model import RuleBasedDecisionModel
from andromeda.modules.conversation.contracts.policy import DecisionModelSource
from andromeda.modules.presentation.contracts.policy import ResponseRequest


class _UnavailableTransport:
    def request(self, operation: str, payload: Mapping[str, object], *, timeout_seconds: float) -> object:
        raise TimeoutError(operation)


class _InvalidTransport:
    def request(self, operation: str, payload: Mapping[str, object], *, timeout_seconds: float) -> object:
        if operation == "resolve_intent":
            return {"intent": "execute_sql", "source": "jev", "confidence": "high"}
        return {"response_format": "text", "template": "<script>bad</script>"}


def test_jev_unavailable_falls_back_without_changing_deterministic_intent() -> None:
    adapter = JevDecisionModelAdapter(
        _UnavailableTransport(),
        RuleBasedDecisionModel(),
        config=JevAdapterConfig(max_retries=0),
    )

    decision = adapter.resolve_intent("Где больше математики?")

    assert decision.source is DecisionModelSource.FALLBACK
    assert decision.intent.value == "analytics_query"
    assert decision.fallback_reason == "provider_unavailable"


def test_invalid_provider_intent_and_template_are_not_trusted() -> None:
    adapter = JevDecisionModelAdapter(_InvalidTransport(), RuleBasedDecisionModel())

    intent = adapter.resolve_intent("Где больше математики?")
    presentation = adapter.choose_presentation(ResponseRequest())

    assert intent.source is DecisionModelSource.FALLBACK
    assert intent.intent.value == "analytics_query"
    assert presentation.source is DecisionModelSource.FALLBACK
    assert presentation.template == "analytics-summary"
