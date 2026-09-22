# Phase 06: Real jevQL runtime

Plan: [index.md](index.md)
Tasks: 13–15
Depends on: Phase 01 / Task 2

## Objective

Replace the broken/local jevQL transport assumptions with the actual upstream Python SDK and protocol while preserving `SemanticPredicatePort`, enforcing materialized-metric priority, and never allowing user/model-generated SQL.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|---|---|---|
| `backend/src/andromeda/infrastructure/jevql/transport.py` | `EmbeddedTransport`, `PrivateProcessTransport`, `SharedServiceTransport` | Embedded factory seeks nonexistent `jevql.EmbeddedClient`; the remediation removes the custom process protocol and routes both supported modes through upstream `Jevql`. |
| `backend/src/andromeda/infrastructure/jevql/adapter.py` | bounds/cache/circuit/result mapping | Existing adapter owns safety policy and should map actual upstream result into the same port. |
| `backend/src/andromeda/infrastructure/jevql/config.py` | mode/fallback/budget settings | Reuse configuration but make platform/capability behavior truthful. |
| upstream jevQL | `Jevql`, `judge`, `query_dicts`, `explain`, `health`, `close`, `JevqlError` | Actual embedded/private/shared API and error model. |
| AnalyticsEngine/materialized projections | existing metric/query paths | Stable metric values must be used before runtime semantic judging. |

## Files to Change

| Path | Action | Required change |
|---|---|---|
| `backend/src/andromeda/infrastructure/jevql/transport.py` | replace adapters | Use upstream `Jevql` and actual HTTP/engine protocol. |
| `backend/src/andromeda/infrastructure/jevql/adapter.py` | modify | Map `judge` answers/errors and preserve budget/circuit/cache semantics. |
| `backend/src/andromeda/infrastructure/jevql/config.py` | modify | Platform capability, engine/cache path and fallback order. |
| `backend/src/andromeda/infrastructure/analytics` or existing query service | modify only routing point | Materialized metric first; predicate only when registered/unmaterialized. |
| `backend/tests/infrastructure/jevql/` | create/modify | SDK, protocol, platform, budget/security/observability tests. |

## Task 13: Replace the fake EmbeddedClient path with upstream Jevql.judge

### Intent

Use the actual embedded Python SDK first where its native engine is supported. The adapter must call `Jevql.judge` on bounded, already narrowed rows rather than generating SQL or inventing an engine API.

### Implementation Steps

1. Replace the lazy `jevql.EmbeddedClient` lookup in `EmbeddedTransport` with `jevql.Jevql(...)`, passing configured database/model/threshold/max_rows/cache/no_cache/engine path/timeout options supported by the pinned SDK.
2. Implement `judge(question, rows, kind, options, threshold)` through the upstream SDK. Use only registered predicate definitions and existing bounded candidate rows; do not interpolate user text into SQL.
3. Map upstream `JudgeResult`/answer objects to the existing `SemanticPredicateResult`/evidence contract. Preserve matched canonical IDs, provider/model, threshold, usage/cache metadata and `JevqlError.code` in safe infra fields.
4. Make transport lifecycle idempotent with `health()` and `close()`. Use an explicit cache path/no-cache policy; do not put raw rows or private text in logs.
5. Report embedded capability based on package/platform/native engine availability. On unsupported Windows wheels, return capability unavailable and let configured fallback order decide; do not create a substitute `EmbeddedClient`.

### Required Interfaces and Contracts

- Existing `SemanticPredicatePort` remains unchanged.
- Internal request: registered predicate ID/version, bounded row schema, max rows/chars, operation kind and safe question text.
- Internal result: matches, answer/evidence, provider/model, cache status, latency, budget usage and source status.
- `JevqlError` codes map to typed unavailable/budget/auth/transport/internal outcomes; unknown codes fail closed.

### Error Handling and Logging

- Log `INFO` predicate ID/version, candidate count, mode, cache hit, latency and result count.
- Log `WARNING` budget exceeded, platform unavailable, timeout or low-confidence/unresolved result.
- Log `ERROR` auth/configuration/engine failure with error code.
- Never log raw candidate rows, API keys, SQL, cookies or full semantic question text.

### Tests

- Mock the real `jevql.Jevql` object and assert exact `judge` call parameters.
- Test `JevqlError` code mapping, close/health, cache/no-cache and max-row enforcement.
- Test Windows/platform-unavailable capability without importing a fake symbol.
- Test no model-generated SQL path exists in adapter.

### Acceptance Criteria

- Embedded mode calls the actual upstream `Jevql` SDK, not `EmbeddedClient`.
- Existing semantic predicate result/port compatibility remains intact.
- Unsupported embedded platform degrades explicitly and safely.

### Verification

- `uv run --extra jevql pytest backend/tests/infrastructure/jevql -q -k "embedded or sdk"` — expected pass with mocked SDK.
- `rg "EmbeddedClient" backend/src/andromeda/infrastructure/jevql` — expected no upstream-client lookup.

## Task 14: Use the upstream Jevql SDK for embedded/private and shared modes

### Intent

Honor the upstream SDK’s actual deployment model. `Jevql()` starts/uses the embedded private engine; `Jevql(url=..., token=...)` connects to a shared service. Remove the Andromeda-owned private-process JSON protocol and do not add a bespoke HTTP client around the shared service.

### Implementation Steps

1. Remove the custom `PrivateProcessTransport` command/framing protocol and its command-based configuration. The upstream `Jevql()` object is the only owner of the embedded/private engine subprocess lifecycle; Andromeda only passes supported SDK options such as database URL, model, threshold, row budget, cache path and timeout.
2. Use `Jevql(url=..., token=...)` for shared service mode. The SDK owns the upstream `/v1/*` protocol, authentication and response decoding; Andromeda validates configured HTTPS/host allowlist before constructing it and never accepts a URL/token from a request or model output.
3. Keep one internal mapper from upstream SDK results/errors to `SemanticPredicateResult`; do not implement query execution, SQL parsing, request framing or a second `/v1/judge` client in Andromeda.
4. Implement fallback order `Jevql()` embedded/private → `Jevql(url=..., token=...)` shared → unavailable, with no implicit network fallback.
5. Add health checks and startup capability reporting for each SDK mode; preserve the existing circuit breaker and bounded concurrency from the adapter. On unsupported Windows embedded wheels, report embedded unavailable and use shared mode only when explicitly configured.

### Required Interfaces and Contracts

- `Jevql()` and `Jevql(url=..., token=...)` are the only upstream construction paths; no Andromeda-owned process protocol or direct HTTP transport is introduced.
- Embedded/shared results and `JevqlError` values are normalized through one internal mapper before `SemanticPredicatePort` sees them.
- Shared URL/token are loaded from secret configuration, host-allowlisted and never serialized into logs or result metadata.

### Error Handling and Logging

- Log fallback transitions at `WARNING` with source mode, safe reason code and latency.
- Log `ERROR` for unsupported native engine, TLS/host configuration violation, invalid SDK response or upstream error code.
- Never log shared tokens, raw SDK bodies, SQL, private rows or engine command lines.

### Tests

- Test `Jevql()` construction/options, embedded engine unavailable behavior, timeout and malformed SDK result.
- Test `Jevql(url=..., token=...)` host allowlist, token redaction, upstream SDK result/error mapping and timeout.
- Test fallback order and explicit unavailable outcome without starting a custom process.
- Test no direct HTTP/process protocol or arbitrary SQL/query endpoint is exposed.

### Acceptance Criteria

- Embedded/private and shared modes both use the actual upstream Python SDK.
- Fallback is deterministic and configuration-driven, not silently networked or process-spawned by Andromeda.
- Security checks reject untrusted endpoints and oversized responses.

### Verification

- Run focused transport tests with a mocked upstream `Jevql` SDK for embedded and shared constructors.
- Inspect logs under failure tests — expected only mode/error code/latency, no secret/body.

## Task 15: Enforce materialized-metric priority, wire jevQL into AnalyticsExecutor and add security/observability

### Intent

Use jevQL only where it adds value: a new/unmaterialized semantic predicate over a narrowed candidate set. Do not judge 20 programs or repeatedly evaluate an existing materialized metric.

### Implementation Steps

1. At the existing AnalyticsEngine/query routing point, classify each request as materialized metric, supported canonical field, registered semantic predicate or unsupported. Materialized metrics execute through existing deterministic analytics repositories first.
2. Invoke `SemanticPredicatePort` only for registered predicate definitions with no usable materialized projection and only after deterministic scope/filter narrowing. Enforce candidate count, row byte/field length, max calls, timeout and total budget before transport.
3. Wire the existing `JevQLAdapter`/`SemanticPredicatePort` into the active `AnalyticsExecutor` composition root behind `JEVQL_ENABLED`. Preserve deterministic executor construction when disabled, and prove a real assistant/API vertical slice reaches the port for one registered unmaterialized predicate.
4. Add predicate definition/version and registry hash to result evidence. Missing/partial data remains explicit; Jev cannot turn missing into false/zero.
5. Emit structured telemetry for predicate ID, materialized/runtime route, candidate count, mode, latency, cache hit, budget outcome, confidence bucket (telemetry only) and fallback reason.
6. Add security rejection for SQL-like model output, unregistered predicate, oversized question/rows, endpoint override, prompt-injection markers where existing sanitizer supports it, and any attempt to pass raw SQL through the port.

### Required Interfaces and Contracts

- Routing is typed/allow-listed; no natural-language-to-SQL path is added.
- The active `AnalyticsExecutor` composition has exactly one optional `JevQLAdapter` binding controlled by `JEVQL_ENABLED`; adapter-only unit tests are insufficient for acceptance.
- `SemanticPredicateResult` includes data-quality status and evidence/provenance sufficient to explain which candidate rows were judged, without storing raw private text.
- `max_rows`, max bytes and max calls are enforced before external invocation and reported in result metadata.

### Error Handling and Logging

- `INFO`: route and safe metrics; `WARNING`: runtime predicate fallback/budget/circuit; `ERROR`: validation/security violation.
- All logs use request/session hash, predicate ID/version and counts; no raw user question, rows, SQL, token or credentials.

### Tests

- Existing materialized `math/programming/AI` metric query must not call jevQL.
- New registered predicate with 20 narrowed candidates may call jevQL once within budget; unregistered predicate is rejected.
- An assistant/API vertical-slice test must prove enabled composition invokes `SemanticPredicatePort`; disabled composition must not instantiate/call it.
- Test budget overflow, missing data, cache hit, SQL-like output and prompt-injection/oversize rejection.
- Add a query-count assertion preventing N+1 predicate calls.

### Acceptance Criteria

- Stable/materialized metric paths remain deterministic and Jev-free.
- The production composition can actually reach `JevQLAdapter` when `JEVQL_ENABLED=true`; the adapter is not orphaned behind tests only.
- Runtime semantic judgment is bounded, source-backed in scope and explainable.
- No model/user input can generate or execute SQL.

### Verification

- Run AnalyticsExecutor composition/integration tests with a spy jevQL transport — materialized scenarios show zero calls.
- Run an assistant/API vertical-slice unmaterialized predicate scenario — exactly one bounded upstream judge call reaches the port and returns typed evidence.

## Phase Risks and Mitigations

- Risk: jevQL native package is unsupported on deployment OS. Mitigation: explicit capability/fallback status and deployment-specific private/shared configuration.
- Risk: rows leak to an external model. Mitigation: deterministic narrowing, field allowlist, byte budgets and redacted telemetry.
- Risk: shared service protocol is not actually upstream-compatible. Mitigation: pinned protocol contract test and no custom response accepted without schema validation.

## Phase Completion Checklist

- Tasks 13–15 satisfy acceptance criteria.
- Actual upstream `Jevql` is used where available; fallback modes are truthful.
- AnalyticsEngine does not route materialized metrics through runtime semantic judging.
