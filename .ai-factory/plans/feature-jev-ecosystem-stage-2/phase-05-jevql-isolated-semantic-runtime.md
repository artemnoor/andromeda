# Phase 05 — jevQL: embedded-first optional semantic predicates

Plan: [index.md](index.md)
Tasks: T12–T14
Depends on: Phase 01 / Tasks T02–T03 and existing analytics executor

## Objective

Добавить jevQL только как embedded-first optional runtime для rare запросов, где deterministic materialized metrics недостаточно. Common catalog analytics remains SQL/ProgramMetric-backed. jevQL is not a PostgreSQL extension, ORM expression or general SQL endpoint. Private subprocess/shared service are fallback deployment modes, not the default.

## Task T12 — Define SemanticPredicatePort and query safety policy

### Implementation steps

1. Add a vendor-neutral port under backend/src/andromeda/modules/analytics/contracts/ or existing repository ports:
   - SemanticPredicate;
   - SemanticPredicateResult;
   - SemanticPredicatePort.
2. The port accepts canonical row IDs, allow-listed fields, bounded question/feature definition and max rows; it cannot accept SQL, table names, joins or user-provided endpoints.
3. Extend AnalyticsExecutor to choose materialized metric → deterministic repository query → optional semantic predicate only when MetricRegistry explicitly declares it.
4. Define query budget: max rows, max chars per row, batch size, concurrency and timeout. QuerySpec rejects unbounded semantic predicates.
5. Add result metadata: predicate definition, provider/model identity, cache identity, evaluated population, selected rows, confidence/status and fallback reason.

### Tests

- backend/tests/modules/analytics/test_semantic_predicate_port.py;
- QuerySpec rejects raw SQL/table/function injection;
- budget bounds;
- only registry-approved metrics invoke the port;
- empty/partial result is not treated as false.

### Acceptance criteria

- no model-generated SQL can reach repository;
- common metrics path makes zero jevQL calls;
- predicate use is explainable and bounded.

### Dependencies, rollback and risks

Depends on T02–T03 and existing AnalyticsExecutor. Rollback disables predicate capability; materialized metrics remain available.

## Task T13 — Add embedded-first jevQL adapter with private-engine fallback

### Implementation steps

1. Create backend/src/andromeda/infrastructure/jevql/: client.py typed client; transport.py with EmbeddedTransport, PrivateProcessTransport and optional SharedServiceTransport; adapter.py mapping jevQL results to SemanticPredicatePort; config.py for mode/path/endpoint/token/timeouts.
2. Use the official Python SDK as the first deployment mode. Let the SDK start/manage its private engine through its embedded subprocess lifecycle where the current platform supports it; do not reimplement jevQL parsing, batching, cache or engine management.
3. If the embedded SDK cannot meet Windows/Linux packaging, process-lifecycle, throughput or security requirements, use a dedicated private subprocess with the jevQL serve protocol. A shared internal service is a third fallback only after a measured capability/benchmark decision and explicit ownership.
4. Reuse official jevQL two-pass protocol in every mode: cheap deterministic filtering outside the model, bounded row collection, batched evaluation, and cache keyed by model/kind/question/options/canonical row JSON.
5. Require local bearer token/mTLS only for process/service modes, allow-listed endpoints, health checks and process lifecycle timeouts. User input must never select the mode, endpoint or engine path.
6. Treat cache as unencrypted sensitive data: configurable path/retention, no shared secrets/private profiles, no production prompt logging. Map jevQL error codes sql, budget, api, auth, internal and transport to typed degraded results.

### Tests

- fake embedded SDK, private-process and HTTP protocol contract tests;
- capability matrix proving embedded mode is attempted before private process/service;
- endpoint allowlist/SSRF rejection;
- malformed response and error-code mapping;
- max rows/chars/batch/concurrency;
- Windows development path uses the supported embedded/private mode or returns capability unavailable without crashing;
- integration test with pinned SDK/process fixtures, not a live provider.

### Acceptance criteria

- jevQL is optional and embedded-first;
- default composition does not require a shared jevQL service;
- private process/shared service is selected only by validated capability/benchmark policy;
- no jevQL package is imported by default application startup;
- failure returns INSUFFICIENT_DATA/UNAVAILABLE with reason, never fabricated match;
- cache keys include canonical row identity and definition version.

### Dependencies, rollback and risks

Depends on T12. Rollback disables JEVQL_ENABLED or selects deterministic materialized metrics; no canonical data change. Risk: SDK/platform mismatch, service overengineering and private row leakage; gate each deployment mode behind explicit capability, budget and benchmark evidence.

## Task T14 — Connect semantic predicate results to explainable analytics

### Implementation steps

1. Extend AnalyticsResult/explanation contracts with optional semantic_predicate_evidence.
2. For each selected row record predicate definition/version, feature/criterion, evaluated row ID, result status and confidence bucket.
3. Ensure ResponsePlan can say semantic filter unavailable/partial rather than silently omitting rows.
4. Add request-level circuit breaker/degraded mode after repeated budget/auth/transport failures; deterministic materialized query continues.
5. Add cache invalidation key tied to semantic definition/model version and canonical row hash.

### Tests

- analytics integration with fake predicate adapter;
- partial population/coverage;
- cache hit and invalidation;
- circuit breaker opens/recovery;
- provenance path from result to ProgramProjection/CurriculumItem.

### Acceptance criteria

- user-visible analytics never equates unassessed with false;
- result explains which rows were evaluated;
- normal ranking/comparison remains deterministic when optional runtime is off.

### Dependencies, rollback and risks

Depends on T13. Rollback removes optional evidence field from presentation only; core result schema remains backwards-compatible.

## Commit checkpoint C4

After T12–T14: commit isolated jevQL contract, adapter, budget/circuit-breaker and evidence path. Keep feature flag disabled in all default environments.

## Phase Verification

- pytest backend/tests/modules/analytics -q
- pytest backend/tests/infrastructure/jevql -q
- python backend/scripts/check_architecture.py

Expected result: common analytics never requires jevQL, embedded mode is preferred before process/service fallback, protocol fixtures enforce budgets/allowlists, and unavailable/partial predicates remain typed degraded results.
