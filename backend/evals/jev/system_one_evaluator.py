"""Opt-in System One evaluation harness.

This module is deliberately outside ``andromeda``. It may compare a provider
against deterministic decisions, but it cannot become a runtime dependency of
the application composition root.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from andromeda.modules.conversation.contracts.decision_definitions import DecisionDefinition


class SystemOneClientProtocol(Protocol):
    def system_one(self, *, state: str, questions: Mapping[str, object], **kwargs: object) -> object: ...


class SystemOneQuestionFactory(Protocol):
    def build(self, definition: DecisionDefinition, case: Mapping[str, object]) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class SystemOneEvaluationCase:
    case_id: str
    definition: DecisionDefinition
    input_text: str
    expected: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class SystemOneEvaluationResult:
    case_id: str
    definition_id: str
    definition_version: str
    status: str
    failure_reason: str | None
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    retry_count: int | None
    provider: str
    model: str
    sanitized_output: Mapping[str, object] | None


class SystemOneEvaluator:
    """Run explicitly selected cases and emit aggregate-safe structured rows."""

    def __init__(self, client: SystemOneClientProtocol, question_factory: SystemOneQuestionFactory) -> None:
        self._client = client
        self._question_factory = question_factory

    def evaluate(
        self,
        cases: Sequence[SystemOneEvaluationCase],
        *,
        provider: str,
        model: str,
        allow_failures: bool = False,
    ) -> tuple[SystemOneEvaluationResult, ...]:
        results: list[SystemOneEvaluationResult] = []
        for case in cases:
            started = time.monotonic()
            try:
                response = self._client.system_one(
                    state=case.input_text,
                    questions=self._question_factory.build(case.definition, {"expected": case.expected}),
                    provider=provider,
                    model=model,
                )
                usage = getattr(response, "usage", None)
                dumped = _safe_dump(response)
                results.append(
                    SystemOneEvaluationResult(
                        case_id=case.case_id,
                        definition_id=case.definition.definition_id,
                        definition_version=case.definition.version,
                        status="completed",
                        failure_reason=None,
                        latency_ms=int((time.monotonic() - started) * 1000),
                        input_tokens=_usage_int(usage, "input_tokens_total"),
                        output_tokens=_usage_int(usage, "output_tokens_total"),
                        retry_count=_usage_int(usage, "n_retries"),
                        provider=provider,
                        model=model,
                        sanitized_output=_sanitize_output(dumped),
                    )
                )
            except Exception as exc:
                if not allow_failures:
                    raise
                results.append(
                    SystemOneEvaluationResult(
                        case_id=case.case_id,
                        definition_id=case.definition.definition_id,
                        definition_version=case.definition.version,
                        status="provider_error",
                        failure_reason=type(exc).__name__,
                        latency_ms=int((time.monotonic() - started) * 1000),
                        input_tokens=None,
                        output_tokens=None,
                        retry_count=None,
                        provider=provider,
                        model=model,
                        sanitized_output=None,
                    )
                )
        return tuple(results)


class OfficialSystemOneQuestionFactory:
    """Build a single bounded Noul question using the optional official adapter."""

    def __init__(self) -> None:
        try:
            from system_one_adapter import Noul
        except ImportError as exc:  # pragma: no cover - exercised by CLI preflight
            raise RuntimeError("install the optional 'evaluation' dependency first") from exc
        self._noul = Noul

    def build(self, definition: DecisionDefinition, case: Mapping[str, object]) -> Mapping[str, object]:
        del case
        return {
            "decision": self._noul(
                instructions=(
                    f"{definition.instructions} Return only the typed decision for "
                    f"definition {definition.definition_id} ({definition.version})."
                )
            )
        }


def _safe_dump(value: object) -> Mapping[str, object]:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
    elif isinstance(value, Mapping):
        dumped = dict(value)
    else:
        dumped = {"value_type": type(value).__name__}
    return dumped if isinstance(dumped, Mapping) else {"value_type": type(dumped).__name__}


def _sanitize_output(value: Mapping[str, object]) -> Mapping[str, object]:
    sensitive = {"messages", "llm_attempts", "debug", "prompt", "state", "text", "cookie", "token"}
    return {key: "[REDACTED]" if key.lower() in sensitive else _sanitize_value(item) for key, item in value.items()}


def _sanitize_value(value: object) -> object:
    if isinstance(value, str):
        return value[:256]
    if isinstance(value, Mapping):
        return {str(key): _sanitize_value(item) for key, item in value.items() if str(key).lower() not in {"text", "prompt", "state"}}
    if isinstance(value, (list, tuple)):
        return tuple(_sanitize_value(item) for item in value[:32])
    return value


def _usage_int(usage: object, name: str) -> int | None:
    if usage is None:
        return None
    value = getattr(usage, name, None)
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(usage, Mapping):
        candidate = usage.get(name)
        if isinstance(candidate, int) and candidate >= 0:
            return candidate
    return None


__all__ = [
    "OfficialSystemOneQuestionFactory",
    "SystemOneClientProtocol",
    "SystemOneEvaluationCase",
    "SystemOneEvaluationResult",
    "SystemOneEvaluator",
    "SystemOneQuestionFactory",
]
