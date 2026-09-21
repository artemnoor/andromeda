"""Fail-closed production/shadow Jev composition helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from andromeda.infrastructure.config.settings import Settings
from andromeda.modules.conversation.contracts.policy import DecisionPolicyPort
from andromeda.modules.conversation.services.decision_model import RuleBasedDecisionModel
from andromeda.modules.conversation.services.model_decision_policy import (
    ModelBackedDecisionPolicy,
    ShadowDecisionPolicy,
)
from andromeda.modules.conversation.services.rule_decision_policy import RuleBasedDecisionPolicy

from .adapter import JevAdapterConfig, JevDecisionModelAdapter
from .question_registry import QuestionRegistry
from .typesafe_client import TypeSafeJevTransport

logger = logging.getLogger("andromeda.infrastructure.jev.runtime")


@dataclass(frozen=True, slots=True)
class JevCapabilityReport:
    enabled: bool
    shadow: bool
    provider: str
    model: str
    reason: str
    lock_id: str | None = None


def build_decision_policy(settings: Settings) -> tuple[DecisionPolicyPort, JevCapabilityReport]:
    deterministic = RuleBasedDecisionPolicy()
    if not settings.jev_enabled and not settings.jev_shadow_enabled:
        return deterministic, _report(settings, reason="disabled_by_config")
    try:
        registry = QuestionRegistry.from_file(_registry_path())
        lock_id = _validate_lock(settings) if settings.jev_enabled else None
        if settings.jev_api_key is None:
            raise RuntimeError("provider_key_missing")
        transport = TypeSafeJevTransport(
            api_key=settings.jev_api_key,
            endpoint=settings.jev_endpoint,
            model=settings.jev_model,
            registry=registry,
            timeout_seconds=settings.jev_timeout_seconds,
        )
        if not transport.health_check():
            raise RuntimeError("provider_health_failed")
        model = JevDecisionModelAdapter(
            transport,
            RuleBasedDecisionModel(),
            config=JevAdapterConfig(
                timeout_seconds=settings.jev_timeout_seconds,
                max_retries=1,
                provider=settings.jev_runtime_provider,
                model=settings.jev_model,
            ),
            registry=registry,
        )
        if settings.jev_shadow_enabled:
            policy: DecisionPolicyPort = ShadowDecisionPolicy(model, deterministic)
            report = _report(settings, reason="shadow_enabled", lock_id=lock_id)
        else:
            policy = ModelBackedDecisionPolicy(model, deterministic)
            report = _report(settings, reason="production_enabled", lock_id=lock_id)
        _log_report(report)
        return policy, report
    except Exception as exc:
        report = _report(settings, reason=type(exc).__name__)
        _log_report(report)
        return deterministic, report


def _registry_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / "jev" / "question-definitions.v1.yaml"


def _validate_lock(settings: Settings) -> str:
    if not settings.jev_calibration_lock_path:
        raise RuntimeError("calibration_lock_missing")
    path = Path(settings.jev_calibration_lock_path)
    if not path.is_file():
        raise RuntimeError("calibration_lock_not_found")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("calibration_lock_invalid") from exc
    lock_id = document.get("lock_id") if isinstance(document, dict) else None
    model = document.get("model") if isinstance(document, dict) else None
    if not isinstance(lock_id, str) or not isinstance(model, dict) or model.get("source") == "shadow_only":
        raise RuntimeError("calibration_lock_not_production_ready")
    return lock_id


def _report(settings: Settings, *, reason: str, lock_id: str | None = None) -> JevCapabilityReport:
    return JevCapabilityReport(
        enabled=settings.jev_enabled and reason == "production_enabled",
        shadow=settings.jev_shadow_enabled and reason == "shadow_enabled",
        provider=settings.jev_runtime_provider,
        model=settings.jev_model,
        reason=reason,
        lock_id=lock_id,
    )


def _log_report(report: JevCapabilityReport) -> None:
    logger.info(
        "jev_capability enabled=%s shadow=%s provider=%s model=%s reason=%s lock_id=%s",
        report.enabled,
        report.shadow,
        report.provider,
        report.model,
        report.reason,
        report.lock_id or "none",
    )


__all__ = ["JevCapabilityReport", "build_decision_policy"]
