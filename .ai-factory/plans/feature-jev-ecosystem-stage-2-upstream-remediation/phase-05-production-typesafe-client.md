# Phase 05: Production decision-policy wiring

Plan: [index.md](index.md)
Tasks: 12
Depends on: Phase 03 / Tasks 6–9; Phase 04 / Task 11

## Objective

Wire the already-upgraded official TypeSafe client and the already-validated upstream Cascade adapter into the existing `DecisionModelPort` composition. This phase owns orchestration, health and deterministic fallback only; it must not create another calibration gate.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|---|---|---|
| `backend/src/andromeda/infrastructure/jev/runtime.py` | `build_decision_policy`, `JevCapabilityReport` | Existing composition point and capability report. |
| `backend/src/andromeda/infrastructure/jev/adapter.py` | `JevDecisionModelAdapter` | Existing typed provider boundary; Task 8 owns trust semantics. |
| `backend/src/andromeda/infrastructure/jev/typesafe_client.py` | official SDK transport from Task 6 | Provider health/model/usage source. |
| `backend/src/andromeda/infrastructure/jev/calibration.py` | upstream Cascade adapter from Task 8 | Single owner of calibrated acceptance. |

## Files to Change

| Path | Action | Required change |
|---|---|---|
| `backend/src/andromeda/infrastructure/jev/runtime.py` | modify | Compose client, health, Cascade artifact and fallback in correct order. |
| `backend/src/andromeda/infrastructure/jev/adapter.py` | modify if needed | Consume the one Cascade adapter without duplicating policy. |
| `backend/src/andromeda/infrastructure/jev/config.py` | modify if needed | Explicit endpoint allowlist, timeout/retry and shadow/production mode. |
| `backend/tests/infrastructure/jev/` | create/modify | Composition, health, shadow and degraded-mode tests. |

## Task 12: Wire production Jev health, calibration compatibility and deterministic fallback

### Intent

Make the complete production path truthful: official client + real lock + compatible model + upstream Cascade gate. Keep deterministic behavior authoritative in shadow/degraded mode.

### Implementation Steps

1. Update `build_decision_policy()` to assemble `TypeSafeJevTransport`, the Task 8 Cascade adapter and `JevDecisionModelAdapter` only after startup validation passes. Return an explicit capability report when any prerequisite is unavailable.
2. Validate configured model against official `models.list()` and the upstream lock’s requested/observed model fields. Validate registry and definition versions before a definition can be invoked.
3. Route every provider answer through the single Task 8 Cascade adapter; accepted answers become the existing typed intent/metric decision, rejected answers call deterministic policy with `calibration_rejected`, and provider errors call deterministic fallback with an explicit provider failure reason.
4. Preserve shadow mode: call Jev/Cascade when enabled/shadow configured, record provider/gate comparison telemetry, but return deterministic policy output. Production mode may return Jev only when artifact status is `production_ready`.
5. Add lifecycle cleanup for SDK/transport instances and ensure startup failure cannot create an unbounded retry loop.

### Required Interfaces and Contracts

- `JevCapabilityReport` gains only safe status/reason/artifact/model metadata; existing consumers remain compatible.
- Decision source values are `deterministic`, `jev_shadow`, `jev_accepted`, `jev_fallback`.
- There is exactly one calibrated acceptance owner: the upstream `jevcal.runtime.Cascade` adapter from Task 8.
- Fallback is deterministic and typed; no generic “best guess” text is allowed.

### Error Handling and Logging

- `INFO`: mode, decision source, definition, model version, artifact ID, latency and Cascade outcome.
- `WARNING`: shadow discrepancy, calibrated rejection, provider timeout or degraded mode.
- `ERROR`: invalid configuration, artifact schema mismatch, auth failure or lifecycle failure.
- Redact all input text and secrets; use case/session hash only.

### Tests

- End-to-end adapter test: official SDK fake → evidence → upstream Cascade adapter → accepted typed decision.
- Rejection/error/health/stale-lock/model mismatch tests prove deterministic output and no exception leak.
- Shadow mode test proves user-visible result equals deterministic result while telemetry records Jev.
- Existing `DecisionModelPort` and decision-flow regression tests remain green.

### Acceptance Criteria

- No production Jev response bypasses upstream Cascade compatibility or per-definition gate.
- No lock/provider/model failure changes existing deterministic behavior unexpectedly.
- System One Adapter is not imported by runtime composition.
- No second local confidence/threshold policy is introduced in runtime wiring.

### Verification

- Run focused Jev runtime tests and existing decision tests.
- Start with no key, stale lock, valid fixture lock and valid fake production lock; expected capability states are deterministic/degraded, fixture-only, and accepted only for the valid production lock respectively.

## Phase Risks and Mitigations

- Risk: runtime wiring accidentally becomes a second policy owner. Mitigation: composition tests assert one Cascade adapter and no threshold logic in `runtime.py`/`adapter.py`.
- Risk: provider/model version changes invalidate calibration. Mitigation: model list and upstream lock compatibility checks.

## Phase Completion Checklist

- Task 12 satisfies acceptance criteria.
- Official TypeSafe client and upstream Cascade are composed only after validation.
- Deterministic fallback remains available and tested.
