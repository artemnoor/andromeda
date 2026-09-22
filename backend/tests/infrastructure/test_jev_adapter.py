from __future__ import annotations

from pathlib import Path
from typing import Mapping

from andromeda.infrastructure.jev.adapter import JevAdapterConfig, JevDecisionModelAdapter
from andromeda.infrastructure.jev.contracts import (
    JevAnswerEvidence,
    JevFailureReason,
    JevRequestEnvelope,
    JevResponseEnvelope,
    JevUsage,
    ModelIdentity,
)
from andromeda.infrastructure.jev.question_registry import QuestionRegistry
from andromeda.modules.conversation.services.decision_model import RuleBasedDecisionModel
from andromeda.modules.conversation.contracts.policy import DecisionModelOperation, DecisionModelSource
from andromeda.modules.presentation.contracts.policy import ResponseRequest


class _UnavailableTransport:
    def request(self, operation: str, payload: Mapping[str, object], *, timeout_seconds: float) -> object:
        raise TimeoutError(operation)


class _InvalidTransport:
    def request(self, operation: str, payload: Mapping[str, object], *, timeout_seconds: float) -> object:
        if operation == "resolve_intent":
            return {"intent": "execute_sql", "source": "jev", "confidence": "high"}
        return {"response_format": "text", "template": "<script>bad</script>"}


class _EnvelopeTransport:
    def __init__(self) -> None:
        self.requests: list[JevRequestEnvelope] = []

    def request_envelope(self, request: JevRequestEnvelope) -> object:
        self.requests.append(request)
        return {
            "intent": "analytics_query",
            "source": "jev",
            "confidence": "high",
        }


class _RejectedCalibration:
    artifact_id = "fixture-artifact"

    def evaluate(self, definition_id: str, evidence: JevAnswerEvidence):
        assert definition_id == "intent.v1"
        assert evidence.answer_value == "analytics_query"
        return type("Gate", (), {"accepted": False, "artifact_id": self.artifact_id, "reason": "calibration_rejected"})()


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


def test_typed_transport_receives_registry_definition_and_schema() -> None:
    transport = _EnvelopeTransport()
    registry = QuestionRegistry.from_file(
        Path(__file__).resolve().parents[2]
        / "config"
        / "jev"
        / "question-definitions.v1.yaml"
    )
    adapter = JevDecisionModelAdapter(transport, RuleBasedDecisionModel(), registry=registry)

    decision = adapter.resolve_intent("Где больше математики?")

    assert decision.source is DecisionModelSource.JEV
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.definition_id == "intent.v1"
    assert request.definition_version == "intent-definition.v1"
    assert request.operation is DecisionModelOperation.RESOLVE_INTENT
    assert request.output_schema.fields == ("intent", "confidence")
    assert request.timeout_class.value == "interactive"


def test_missing_registry_artifact_is_a_typed_fallback() -> None:
    registry = QuestionRegistry.from_document(
        {
            "definitions": [
                {
                    "definition_id": "intent.v1",
                    "kind": "intent",
                    "operation": "resolve_intent",
                    "version": "intent-definition.v1",
                    "instructions": "test",
                    "output_schema": {"fields": ["intent"]},
                    "deterministic_fallback": "rule_based_intent",
                    "timeout_class": "interactive",
                    "pii_policy": "sanitized",
                    "evaluation_dataset_key": "test.intent.v1",
                }
            ]
        }
    )
    adapter = JevDecisionModelAdapter(_EnvelopeTransport(), RuleBasedDecisionModel(), registry=registry)

    decision = adapter.resolve_metric("математика", candidates=("mathematics_share",))

    assert decision.source is DecisionModelSource.FALLBACK
    assert decision.fallback_reason == JevFailureReason.ARTIFACT_MISSING.value


def test_calibration_gate_rejects_provider_answer_before_domain_parsing() -> None:
    class Transport:
        def request_envelope(self, request: JevRequestEnvelope) -> JevResponseEnvelope:
            return JevResponseEnvelope(
                payload={"intent": "analytics_query", "source": "jev", "confidence": "high"},
                identity=ModelIdentity(artifact_id="intent.v1@intent-definition.v1"),
                usage=JevUsage(),
                evidence=JevAnswerEvidence(
                    answer_kind="choice",
                    answer_value="analytics_query",
                    probabilities={"analytics_query": 0.6, "unknown": 0.4},
                    has_probability_evidence=True,
                ),
            )

    adapter = JevDecisionModelAdapter(
        Transport(),
        RuleBasedDecisionModel(),
        calibration=_RejectedCalibration(),
    )

    decision = adapter.resolve_intent("Где больше математики?")

    assert decision.source is DecisionModelSource.FALLBACK
    assert decision.fallback_reason == JevFailureReason.CALIBRATION_REJECTED.value
