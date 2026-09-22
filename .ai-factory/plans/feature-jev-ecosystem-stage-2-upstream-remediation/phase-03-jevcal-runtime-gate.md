# Phase 03: TypeSafe client, jevcal artifact and runtime gate

Plan: [index.md](index.md)
Tasks: 6–9
Depends on: Phase 02 / Tasks 4–5

## Objective

Establish the official TypeSafe SDK surface first, then produce the real upstream jevcal artifact and reuse its runtime Cascade semantics for trust decisions. This phase must not create a second calibration engine or change public typed ports.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|---|---|---|
| `backend/src/andromeda/infrastructure/jev/typesafe_client.py` | `_official_client_factory`, `health_check`, `_questions_for`, `_payload_for`, `_confidence_bucket` | Existing adapter is reusable but pins/assumes SDK 0.6.0 and uses buckets without calibrated acceptance. |
| `backend/scripts/jevcal_calibrate.py` | `_select_threshold`, `_accuracy`, `_ece`, `_build_lock` | Local threshold/ECE algorithm must be removed in favor of upstream commands/API. |
| `backend/src/andromeda/infrastructure/jev/runtime.py` | `build_decision_policy`, `_validate_lock` | Current runtime checks lock presence/model shadow status but does not use upstream Cascade semantics. |
| `backend/src/andromeda/infrastructure/jev/adapter.py` | `JevDecisionModelAdapter` | Existing typed boundary is the correct location for Cascade result mapping and fallback. |
| upstream TypeSafe SDK v0.7.1 | `TypeSafeClient`, typed answer/usage/model APIs | Real provider client and raw probability source. |
| upstream jevcal | `compile_question`, `build_lock`, `runtime.Cascade`, `metrics.pick_threshold` | Upstream owns confidence measure, threshold selection, lock shape and runtime trust. |

## Files to Change

| Path | Action | Required change |
|---|---|---|
| `backend/src/andromeda/infrastructure/jev/typesafe_client.py` | modify | Use official v0.7.1 API and expose bounded raw answer evidence. |
| `backend/scripts/jevcal_calibrate.py` | replace | Thin wrapper around upstream `lint/measure/compile/run/check`; no local math. |
| `backend/src/andromeda/infrastructure/jev/calibration.py` | create/modify | Thin upstream Cascade owner/adapter and compatibility validator. |
| `backend/src/andromeda/infrastructure/jev/adapter.py` | modify | Feed raw evidence to Cascade and map accepted/unresolved results. |
| `backend/src/andromeda/infrastructure/jev/runtime.py` | modify | Load/validate official client and Cascade artifact at enabled-runtime construction. |
| `backend/config/jev/` | add versioned lock/manifest path contract | Do not commit production secrets or inadequate fixture as enabled lock. |
| `backend/tests/infrastructure/jev/` | create/modify | SDK, artifact, Cascade, compatibility and fail-closed tests. |

## Task 6: Upgrade the official TypeSafe SDK adapter before calibration wiring

### Intent

Make the official TypeSafe SDK the real provider surface before any calibration artifact is consumed. This prevents the gate from being designed around a stale or synthetic response shape.

### Implementation Steps

1. Update the lazy import/factory in `backend/src/andromeda/infrastructure/jev/typesafe_client.py` to official SDK v0.7.1 constructor semantics: API key, model, configured allowlisted base URL, timeout and SDK retry policy. Do not accept a request-provided endpoint.
2. Translate registry definitions to actual SDK-native `Choice`, `Noul` or `Score` questions according to their output schema. Keep definition ID/version in the envelope, not in untrusted model fields.
3. Parse official `SystemOneResponse` typed answers, including `ChoiceAnswer.probabilities`, `confidence`, `NoulAnswer.noul`, `ScoreAnswer` fields and typed `Usage`. Preserve a bounded `JevAnswerEvidence` infra object for Tasks 8 and 12; do not expose SDK classes outside infrastructure.
4. Keep `_confidence_bucket` only as a display/telemetry mapping. Remove its use from decision acceptance and include raw confidence/probability presence flags, not raw maps, in normal logs.
5. Update `health_check()` to call the official model listing API and verify configured model/provider/version compatibility without logging the endpoint or key.
6. Keep retries/timeouts bounded and close the SDK/http client on shutdown where current composition supports lifecycle hooks.

### Required Interfaces and Contracts

- Existing `DecisionModelPort` signature and typed result contracts do not change.
- New infra-only `JevAnswerEvidence` includes operation, answer, probability support, raw confidence, model requested/observed, usage, retry count, latency and response ID if available.
- A provider response with missing/ambiguous answer or unsupported schema is invalid and goes to existing fallback.

### Error Handling and Logging

- Log `INFO` provider/model/operation/latency/usage totals and probability-presence, not content.
- Log `WARNING` bounded retry/fallback and `ERROR` invalid schema/auth/configuration with stable error code.
- Redact SDK request/response bodies if SDK transport logging is enabled; never log API key, bearer header, cookies or raw prompt.

### Tests

- Mock official SDK `TypeSafeClient` with typed Choice/Noul/Score responses and usage.
- Test constructor endpoint/model/timeout/retry mapping, model list health, malformed answer, missing probabilities and client error.
- Test no SDK import occurs in canonical ingestion or domain modules.

### Acceptance Criteria

- The production adapter runs against official `typesafe-sdk` v0.7.1 API.
- Raw probability/confidence evidence is available to upstream Cascade without changing public typed ports.
- Hardcoded buckets cannot accept or reject a decision.

### Verification

- `uv run --extra jev pytest backend/tests/infrastructure/jev -q -k "typesafe or sdk"` — expected pass.
- Python import/constructor smoke against the locked SDK — expected pass without a network call.

## Task 7: Invoke upstream jevcal to produce the real calibration artifact

### Intent

Make calibration provenance truthful. The script may orchestrate/export/validate, but threshold selection, confidence measures, holdout evaluation and lock compilation must be performed by pinned upstream jevcal.

### Implementation Steps

1. Replace local functions in `backend/scripts/jevcal_calibrate.py` with a subprocess-first wrapper around the pinned `jevcal` CLI (`lint`, `measure`, `compile`, `run`, `check`) using native artifacts from Task 4. If a command is unavailable at the pinned commit, call the corresponding public `jevcal.compile`/`jevcal.runtime` API; do not copy the algorithm.
2. Use upstream `compile_question`/`build_lock` semantics and the upstream confidence measure specified by each definition/tool config. Store the exact upstream `decisions.lock.json` (or exact upstream output name), report, dataset SHA, registry hash, provider/model requested and observed, holdout/seed, and upstream package revision.
3. Add a small Andromeda sidecar manifest only for repository compatibility fields: registry definition versions, corpus source kind, artifact path, upstream commit, minimum support policy, and enablement status. The sidecar must not duplicate thresholds or recompute metrics.
4. Run upstream `jevcal check` against the generated lock/report and fail if the artifact is incomplete, model-drifted, hash-mismatched or insufficient for the requested mode.
5. Remove or make unreachable local `_select_threshold`, `_accuracy`, `_ece` and any local calibration loop. A code review must be able to point to the upstream call that owns each result.

### Required Interfaces and Contracts

- Input: native questions/dataset, registry hash, provider/model observations, explicit mode `fixture` or `production`.
- Output: raw upstream jevcal lock/report plus Andromeda provenance sidecar.
- Runtime lock fields remain upstream-owned: per-question target, measure, threshold/status/baseline, dataset/questions hashes, holdout/seed, model and provider metadata.
- Production mode rejects shadow-only or fixture artifacts; fixture mode may compile for wiring but cannot set runtime enabled.

### Error Handling and Logging

- Log each upstream command, version, exit code, artifact path and SHA at `INFO`; capture stdout/stderr to a redacted report file.
- Log `ERROR` and stop on non-zero command, malformed lock, unsupported upstream schema, missing support, hash mismatch or model drift.
- Never log rows, prompts, credentials, full provider responses or threshold values as unstructured user-visible text.

### Tests

- Unit-test command construction and sidecar validation with a fake upstream executable.
- Integration-test the pinned jevcal compile/check path on the fixture corpus; assert output is parseable by upstream runtime.
- Assert source code no longer contains local ECE/threshold-selection logic.
- Commands: `uv run --extra evaluation pytest backend/tests/infrastructure/jev/test_jevcal_calibrate.py -q`; `uv run --extra evaluation python backend/scripts/jevcal_calibrate.py --source fixture --offline`.

### Acceptance Criteria

- Calibration artifacts are generated by actual upstream jevcal and pass its own check.
- The Andromeda wrapper does not calculate accuracy, ECE, confidence measures or thresholds.
- Every artifact carries registry/dataset/upstream/model provenance and explicit fixture/production status.

### Verification

- `uv run --extra evaluation python backend/scripts/jevcal_calibrate.py --source fixture --offline` — expected deterministic upstream artifact/report.
- Parse the raw lock with upstream `jevcal.runtime.Cascade` — expected no schema error.
- `rg "def _select_threshold|def _ece|def _accuracy" backend/scripts/jevcal_calibrate.py` — expected no matches.

## Task 8: Reuse jevcal.runtime.Cascade for the per-definition fail-closed runtime gate

### Intent

Connect real calibration evidence to production trust without writing a second jevcal. Prefer direct reuse of upstream `jevcal.runtime.Cascade` and its lock semantics. Do not reimplement threshold acceptance locally unless an incompatibility is demonstrated by source/code evidence and recorded as a blocking implementation finding.

### Implementation Steps

1. In `backend/src/andromeda/infrastructure/jev/calibration.py`, create only a thin typed adapter around the pinned upstream `jevcal.runtime.Cascade`. The adapter may validate Andromeda registry/model/sidecar metadata before constructing Cascade, but it must delegate measure calculation, per-definition threshold lookup, accepted/unresolved semantics and fallback decision to upstream Cascade.
2. Validate at load time: upstream lock schema/version, registry hash and every definition version, model requested/observed compatibility, provider identity, dataset/source kind, artifact age/expiry policy, status, minimum support policy and required probability keys. Reject fixture/shadow-only artifacts in production mode.
3. In `JevDecisionModelAdapter`, pass the `JevAnswerEvidence` from Task 6 through the Cascade-compatible answer/probability shape. Map Cascade’s accepted/unresolved outcome into existing typed intent/metric decisions; map low confidence to the existing deterministic fallback with reason `calibration_rejected`.
4. Keep `_confidence_bucket` only for telemetry. Do not copy upstream `confidence_measures`, `pick_threshold`, Wilson/holdout logic or ECE code into Andromeda.
5. Keep `DecisionModelPort`, `JevRequestEnvelope`, `JevResponseEnvelope`, QueryFrame/QuerySession and deterministic policy contracts unchanged; add only infra metadata needed to explain Cascade acceptance/rejection.
6. Make `runtime.py` build fail closed when enabled Jev has no valid artifact, stale artifact, mismatched model/version, unsupported definition or unavailable probability evidence.

### Required Interfaces and Contracts

- `CascadeCalibrationAdapter.evaluate(definition_id, answer_evidence) -> GateDecision` delegates the trust calculation to one upstream `jevcal.runtime.Cascade` instance/operation.
- `GateDecision` contains `accepted`, upstream measure/threshold when provided, observed outcome, reason, artifact ID, definition version and model version. These fields are an adapter view of upstream output, not a second algorithm.
- Acceptance uses the upstream lock’s per-definition measure/threshold. UI `high/medium/low` remains non-authoritative telemetry.
- Compatibility is fail-closed for missing definition, stale version, model mismatch, malformed probabilities, non-production artifact or unsupported answer type.

### Error Handling and Logging

- Log `INFO` gate accepted/rejected with definition ID, artifact ID, model version, upstream measure name, outcome and latency; do not log raw probability maps.
- Log `WARNING` for deterministic fallback due to low confidence, and `ERROR` for invalid artifact/configuration or Cascade schema incompatibility.
- Include a stable `fallback_reason` in typed infra metadata; never expose provider secrets or user text.

### Tests

- Test direct construction/use of upstream `jevcal.runtime.Cascade` with the generated lock and provider-shaped answer fixtures.
- Test two definitions with different upstream thresholds and prove a single global threshold is never consulted.
- Test top-probability, margin/entropy/provided measure routing by asserting upstream Cascade output, not by duplicating formulas.
- Test stale artifact, registry hash mismatch, model mismatch, missing probabilities, fixture mode in production and low-confidence fallback.
- Test confidence bucket changes do not alter Cascade gate outcome.
- Commands: focused pytest under `backend/tests/infrastructure/jev`; existing runtime/adapter regression tests.

### Acceptance Criteria

- A Jev answer is accepted only by the pinned upstream `jevcal.runtime.Cascade` semantics for its definition.
- A rejected/unsupported answer reaches existing deterministic fallback/unresolved behavior and is explainable.
- No hardcoded `.8/.5` threshold or locally copied jevcal acceptance algorithm exists.

### Verification

- Run the generated lock through upstream Cascade with the same evidence used by the adapter — expected identical accepted/unresolved result.
- `rg "confidence_measures|pick_threshold|_select_threshold|def _ece" backend/src/andromeda/infrastructure/jev backend/scripts/jevcal_calibrate.py` — expected only imports/calls to upstream symbols, no local implementations.

## Task 9: Separate fixture calibration from production enablement and stale-lock checks

### Intent

Prevent the current tiny corpus from being marketed or deployed as calibrated evidence. Production enablement must require actual support/holdout evidence according to upstream jevcal behavior and configurable Andromeda policy.

### Implementation Steps

1. Add a configuration model in the existing Jev settings path for `calibration_mode`, `minimum_support_per_definition`, `minimum_heldout_per_definition`, artifact max age, allowed model/provider and `allow_fixture_runtime` (default false).
2. Add a validator command that reads the upstream lock and sidecar, reports per-definition counts/status/holdout and returns non-zero when production requirements are not met. It must not invent accuracy or claim calibration for fixture rows.
3. Make runtime construction require this validator and the upstream Cascade adapter when `jev_enabled`; a missing/insufficient/stale artifact reports `calibration_unavailable` and selects deterministic policy rather than silently enabling Jev.
4. Keep shadow mode: deterministic output remains authoritative while Jev/Cascade observations are telemetry. Shadow mode must not change QuerySession, admission results or ResponsePlan.
5. Update `backend/evals/jev/README.md` with fixture vs production corpus instructions only when implementation lands; include no fabricated quality numbers.

### Required Interfaces and Contracts

- Fixture corpus can validate schema, exporter, adapter and offline CI only.
- Production corpus must be externally supplied/configured, labeled, versioned, privacy-reviewed and meet configured/upstream support rules.
- Enablement status values: `fixture_only`, `shadow_only`, `production_ready`, `rejected`; no implicit coercion.

### Error Handling and Logging

- Log `WARNING` for insufficient support and `INFO` for shadow-only operation.
- Log `ERROR` for stale lock, model mismatch, definition mismatch or impossible metadata.
- Never log calibration rows or sensitive evaluator content.

### Tests

- Current three-row-per-definition corpus must fail production enablement and pass fixture wiring.
- Test one missing definition, one insufficient holdout, one stale artifact and one model mismatch.
- Test shadow mode leaves deterministic response unchanged and emits a safe comparison event.

### Acceptance Criteria

- The current fixture lock cannot enable production runtime.
- Minimum sample configuration is explicit and validated against upstream support behavior.
- No new accuracy/ECE numbers are introduced without a real production corpus and upstream report.

### Verification

- `uv run pytest backend/tests/infrastructure/jev -q -k "calibration or shadow"` — expected pass.
- Run startup with `JEV_ENABLED=true` and fixture lock — expected deterministic capability report with `calibration_unavailable`, not production Jev.

## Phase Risks and Mitigations

- Risk: copying upstream metric code creates a second confidence engine. Mitigation: direct `jevcal.runtime.Cascade` adapter, upstream contract tests and a blocking finding if direct reuse is impossible.
- Risk: model API exposes confidence but not complete probabilities. Mitigation: fail closed for definitions requiring missing measure inputs.
- Risk: artifact exists but is silently stale. Mitigation: sidecar/lock hashes, model/version checks and max-age policy at startup and per request where configured.

## Phase Completion Checklist

- Tasks 6–9 satisfy acceptance criteria.
- Official TypeSafe SDK is established before calibration artifact/gate wiring.
- Fixture lock is proven non-production.
- Runtime gate delegates trust semantics to upstream Cascade and fallback remains deterministic.
