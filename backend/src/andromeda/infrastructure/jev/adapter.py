"""Strict, provider-neutral boundary for an optional external decision model."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from andromeda.modules.analytics.contracts.results import AnalyticsResult
from andromeda.modules.analytics.domain.metric_registry import MetricRegistry
from andromeda.modules.conversation.contracts.policy import (
    ConfidenceBucket,
    DataCapabilities,
    DecisionAction,
    DecisionModelOperation,
    DecisionModelPort,
    DecisionModelSource,
    IntentDecision,
    MetricDecision,
    NextActionDecision,
    PresentationDecision,
    SemanticFeatureDecision,
)
from andromeda.modules.conversation.contracts.public import QuerySession
from andromeda.modules.presentation.contracts.policy import (
    PresentationCapabilities,
    ResponseRequest,
)

logger = logging.getLogger("andromeda.infrastructure.jev.adapter")
_ALLOWED_TEMPLATES = {"analytics-summary", "metric-comparison", "metric-cards", "analytics-report", "analytics-explorer"}


class JevTransport(Protocol):
    """Minimal provider-neutral transport; timeout belongs to the implementation."""

    def request(self, operation: str, payload: Mapping[str, object], *, timeout_seconds: float) -> object: ...


@dataclass(frozen=True, slots=True)
class JevAdapterConfig:
    timeout_seconds: float = 2.0
    max_retries: int = 1
    max_failures: int = 3
    circuit_open_seconds: float = 30.0
    max_output_bytes: int = 32_000


class JevDecisionModelAdapter(DecisionModelPort):
    """Validate every external answer and fall back to deterministic behavior."""

    def __init__(
        self,
        transport: JevTransport,
        fallback: DecisionModelPort,
        *,
        config: JevAdapterConfig | None = None,
    ) -> None:
        self._transport = transport
        self._fallback = fallback
        self._config = config or JevAdapterConfig()
        if self._config.timeout_seconds <= 0 or self._config.max_retries < 0:
            raise ValueError("invalid Jev adapter bounds")
        self._failures = 0
        self._circuit_open_until = 0.0
        self._metric_registry = MetricRegistry()

    def resolve_intent(self, text: str) -> IntentDecision:
        if len(text) > 2000:
            return self._fallback_intent(text, "input_too_large")
        response = self._call(DecisionModelOperation.RESOLVE_INTENT, {"text": text})
        if response is None:
            return self._fallback_intent(text, "provider_unavailable")
        try:
            value = IntentDecision.model_validate(response, strict=False)
            return value.model_copy(update={"operation": DecisionModelOperation.RESOLVE_INTENT, "source": DecisionModelSource.JEV})
        except (TypeError, ValueError):
            return self._fallback_intent(text, "invalid_provider_output")

    def resolve_metric(self, text: str, *, candidates: tuple[str, ...] = ()) -> MetricDecision:
        if len(text) > 2000:
            return self._fallback_metric(text, candidates, "input_too_large")
        response = self._call(
            DecisionModelOperation.RESOLVE_METRIC,
            {"text": text, "candidates": candidates[:8]},
        )
        if response is None:
            return self._fallback_metric(text, candidates, "provider_unavailable")
        try:
            value = MetricDecision.model_validate(response, strict=False)
            if value.metric_code is not None and candidates and value.metric_code not in candidates:
                raise ValueError("provider returned a metric outside the candidate set")
            if value.metric_code is not None:
                self._metric_registry.get(value.metric_code)
            return value.model_copy(update={"operation": DecisionModelOperation.RESOLVE_METRIC, "source": DecisionModelSource.JEV})
        except (TypeError, ValueError):
            return self._fallback_metric(text, candidates, "invalid_provider_output")

    def choose_next_action(
        self,
        session: QuerySession,
        *,
        available_actions: tuple[DecisionAction, ...] = tuple(DecisionAction),
        capabilities: DataCapabilities | None = None,
        last_result: AnalyticsResult | None = None,
    ) -> NextActionDecision:
        payload = {
            "intent": session.intent.value,
            "metrics": session.metrics,
            "missing_slots": tuple(slot.value for slot in session.missing_slots),
            "next_action": session.next_action.value,
            "available_actions": tuple(action.value for action in available_actions),
        }
        response = self._call(DecisionModelOperation.CHOOSE_NEXT_ACTION, payload)
        if response is None:
            return self._fallback_next_action(session, available_actions, capabilities, last_result, "provider_unavailable")
        try:
            value = NextActionDecision.model_validate(response, strict=False)
            if value.decision.action not in available_actions:
                raise ValueError("provider returned a forbidden action")
            return value.model_copy(update={"operation": DecisionModelOperation.CHOOSE_NEXT_ACTION, "source": DecisionModelSource.JEV})
        except (TypeError, ValueError):
            return self._fallback_next_action(session, available_actions, capabilities, last_result, "invalid_provider_output")

    def choose_presentation(
        self,
        request: ResponseRequest,
        *,
        capabilities: PresentationCapabilities | None = None,
    ) -> PresentationDecision:
        response = self._call(
            DecisionModelOperation.CHOOSE_PRESENTATION,
            {
                "comparison_requested": request.comparison_requested,
                "report_requested": request.report_requested,
                "interactive_requested": request.interactive_requested,
                "capabilities": (capabilities or PresentationCapabilities()).model_dump(mode="json"),
            },
        )
        if response is None:
            return self._fallback_presentation(request, capabilities, "provider_unavailable")
        try:
            value = PresentationDecision.model_validate(response, strict=False)
            if value.template not in _ALLOWED_TEMPLATES:
                raise ValueError("provider returned a forbidden presentation template")
            return value.model_copy(update={"operation": DecisionModelOperation.CHOOSE_PRESENTATION, "source": DecisionModelSource.JEV})
        except (TypeError, ValueError):
            return self._fallback_presentation(request, capabilities, "invalid_provider_output")

    def classify_semantic_features(
        self,
        input_text: str,
        *,
        feature_codes: tuple[str, ...] = (),
    ) -> SemanticFeatureDecision:
        if len(input_text) > 2000:
            return self._fallback_semantic(input_text, feature_codes, "input_too_large")
        response = self._call(
            DecisionModelOperation.CLASSIFY_SEMANTIC_FEATURES,
            {"text": input_text, "feature_codes": feature_codes[:64]},
        )
        if response is None:
            return self._fallback_semantic(input_text, feature_codes, "provider_unavailable")
        try:
            value = SemanticFeatureDecision.model_validate(response, strict=False)
            allowed = set(feature_codes)
            if any(item.feature_id.removeprefix("semantic-feature:") not in allowed for item in value.values) and allowed:
                raise ValueError("provider returned an unknown semantic feature")
            return value.model_copy(update={"operation": DecisionModelOperation.CLASSIFY_SEMANTIC_FEATURES, "source": DecisionModelSource.JEV})
        except (TypeError, ValueError):
            return self._fallback_semantic(input_text, feature_codes, "invalid_provider_output")

    def _call(self, operation: DecisionModelOperation, payload: Mapping[str, object]) -> object | None:
        now = time.monotonic()
        if now < self._circuit_open_until:
            return None
        attempts = self._config.max_retries + 1
        for attempt in range(attempts):
            started = time.monotonic()
            try:
                response = self._transport.request(operation.value, payload, timeout_seconds=self._config.timeout_seconds)
                if len(repr(response).encode("utf-8")) > self._config.max_output_bytes:
                    raise ValueError("provider output exceeds configured bound")
                self._failures = 0
                logger.info(
                    "decision_model_call operation=%s source=jev outcome=accepted attempt=%s duration_ms=%s",
                    operation.value,
                    attempt + 1,
                    int((time.monotonic() - started) * 1000),
                )
                return response
            except Exception as exc:  # provider boundary: fallback must be total
                self._failures += 1
                logger.warning(
                    "decision_model_call operation=%s source=jev outcome=fallback attempt=%s error=%s",
                    operation.value,
                    attempt + 1,
                    type(exc).__name__,
                )
                if attempt + 1 == attempts:
                    if self._failures >= self._config.max_failures:
                        self._circuit_open_until = time.monotonic() + self._config.circuit_open_seconds
                    return None
        return None

    def _fallback_intent(self, text: str, reason: str) -> IntentDecision:
        try:
            value = self._fallback.resolve_intent(text)
        except Exception:
            from andromeda.modules.conversation.contracts.public import ConversationIntent

            return IntentDecision(
                intent=ConversationIntent.UNKNOWN,
                source=DecisionModelSource.FALLBACK,
                confidence=ConfidenceBucket.UNAVAILABLE,
                fallback_reason=reason,
            )
        return value.model_copy(update={"source": DecisionModelSource.FALLBACK, "fallback_reason": reason})

    def _fallback_metric(self, text: str, candidates: tuple[str, ...], reason: str) -> MetricDecision:
        try:
            value = self._fallback.resolve_metric(text, candidates=candidates)
        except Exception:
            value = MetricDecision(
                metric_code=None,
                source=DecisionModelSource.FALLBACK,
                confidence=ConfidenceBucket.UNAVAILABLE,
            )
        return value.model_copy(update={"source": DecisionModelSource.FALLBACK, "fallback_reason": reason})

    def _fallback_next_action(
        self,
        session: QuerySession,
        available_actions: tuple[DecisionAction, ...],
        capabilities: DataCapabilities | None,
        last_result: AnalyticsResult | None,
        reason: str,
    ) -> NextActionDecision:
        value = self._fallback.choose_next_action(
            session,
            available_actions=available_actions,
            capabilities=capabilities,
            last_result=last_result,
        )
        return value.model_copy(update={"source": DecisionModelSource.FALLBACK, "fallback_reason": reason})

    def _fallback_presentation(
        self,
        request: ResponseRequest,
        capabilities: PresentationCapabilities | None,
        reason: str,
    ) -> PresentationDecision:
        value = self._fallback.choose_presentation(request, capabilities=capabilities)
        return value.model_copy(update={"source": DecisionModelSource.FALLBACK, "fallback_reason": reason})

    def _fallback_semantic(
        self,
        input_text: str,
        feature_codes: tuple[str, ...],
        reason: str,
    ) -> SemanticFeatureDecision:
        value = self._fallback.classify_semantic_features(input_text, feature_codes=feature_codes)
        return value.model_copy(update={"source": DecisionModelSource.FALLBACK, "fallback_reason": reason})


__all__ = ["JevAdapterConfig", "JevDecisionModelAdapter", "JevTransport"]
