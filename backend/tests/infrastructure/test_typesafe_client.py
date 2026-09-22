from pathlib import Path
from types import SimpleNamespace

from andromeda.infrastructure.jev.contracts import JevRequestEnvelope
from andromeda.infrastructure.jev.question_registry import QuestionRegistry
from andromeda.infrastructure.jev.typesafe_client import TypeSafeJevTransport
from andromeda.modules.conversation.contracts.decision_definitions import (
    DecisionDefinitionKind,
    DecisionPiiPolicy,
    DecisionTimeoutClass,
)
from andromeda.modules.conversation.contracts.policy import DecisionModelOperation
from andromeda.modules.conversation.contracts.policy import DecisionModelSource
from andromeda.modules.conversation.contracts.decision_definitions import DecisionOutputSchema


ROOT = Path(__file__).parents[2]
REGISTRY = QuestionRegistry.from_file(ROOT / "config/jev/question-definitions.v1.yaml")


class _FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.models = SimpleNamespace(list=lambda **_: SimpleNamespace(models=(SimpleNamespace(name="jev-latest"),)))
        self.last_state = None
        self.last_questions = None

    def system_one(self, *, state, questions, **_):
        self.last_state = state
        self.last_questions = questions
        return SimpleNamespace(
            model="jev-latest-2026-09",
            usage=SimpleNamespace(input_tokens=10, output_tokens=2),
            choices={"answer": SimpleNamespace(choice="math", confidence=0.91)},
        )


def _request() -> JevRequestEnvelope:
    return JevRequestEnvelope(
        definition_id="metric.v1",
        definition_version="metric-definition.v1",
        definition_kind=DecisionDefinitionKind.METRIC,
        operation=DecisionModelOperation.RESOLVE_METRIC,
        redacted_payload={"text": "математика", "candidates": ("math", "physics")},
        correlation_id="jev:test",
        timeout_seconds=2.0,
        timeout_class=DecisionTimeoutClass.INTERACTIVE,
        pii_policy=DecisionPiiPolicy.SANITIZED,
        output_schema=DecisionOutputSchema(fields=("metric_code",)),
    )


def test_official_sdk_adapter_sends_only_registered_typed_question() -> None:
    holder = {}

    def factory(**kwargs):
        holder["client"] = _FakeClient(**kwargs)
        return holder["client"]

    transport = TypeSafeJevTransport(
        api_key="secret-key",
        endpoint="https://api.typesafe.ai",
        model="jev-latest",
        registry=REGISTRY,
        client_factory=factory,
    )
    response = transport.request_envelope(_request())

    assert response.identity.provider == "typesafe"
    assert response.identity.source is DecisionModelSource.JEV
    assert response.payload == {"metric_code": "math", "candidates": ("math",), "confidence": "high"}
    assert set(holder["client"].last_questions) == {"answer"}
    question = holder["client"].last_questions["answer"]
    assert question.model_dump(mode="json")["criteria"] == {"math": "math", "physics": "physics"}
    assert transport.health_check() is True


def test_client_rejects_non_https_provider_endpoint() -> None:
    try:
        TypeSafeJevTransport(
            api_key="secret-key",
            endpoint="http://evil.example",
            model="jev-latest",
            registry=REGISTRY,
        )
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("non-HTTPS endpoint must be rejected")
