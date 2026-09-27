# Phase 08 — Vertical slices, existing flow compatibility and performance

Plan: [index.md](index.md)
Tasks: T22–T24
Depends on: Phase 07 / Tasks T18–T21

## Objective

Доказать, что Jev ecosystem integrations extend existing universal analytics rather than creating parallel flows. Validate end-to-end behavior, degraded paths, PostgreSQL query counts and renderer neutrality.

## Task T22 — Complete analytics and admission vertical slices

### Implementation steps

1. Route all model-assisted resolution through QuestionRegistry and DecisionModelPort; final factual execution remains AnalyticsExecutor and existing admission services.
2. Add acceptance fixtures:
   - math A vs B;
   - mean math BMSTU vs HSE for one direction over all comparable current programs;
   - top programming/low physics;
   - admission 270 → ask missing subjects → ask scope only when needed;
   - complete admission request → no redundant questions;
   - three-program comparison with semantic metrics and admission fit.
3. Verify population, coverage, basis and curriculum year in every analytics response.
4. Preserve DecisionContext, AdmissionFit, recommendations and decision_analytics semantics.
5. Optional semantic predicate/tree calls are visible in result metadata and never replace materialized metrics by default.

### Tests

- backend/tests/e2e/test_jev_ecosystem_scenarios.py;
- backend/tests/modules/analytics/test_multi_university_aggregation.py;
- backend/tests/modules/conversation/test_no_redundant_questions.py;
- existing admission/comparison/recommendation regression suites.

### Acceptance criteria

- all scenarios pass with flags off;
- shadow mode produces comparison telemetry but same user response;
- Jev unavailable/degraded path passes;
- unsupported metric remains typed error;
- no raw SQL or arbitrary model action executes.

### Dependencies, rollback and risks

Depends on T19 and existing analytics/admission contracts. Rollback is test-gated flag off.

## Task T23 — Verify ResponsePlan/ResponseEnvelope and channel adapters

### Implementation steps

1. Reuse backend/src/andromeda/modules/presentation/ contracts and existing Web/OG routes; do not create provider-specific UI decisions in Telegram/MAX.
2. Add templates/evidence fields only through channel-neutral ResponsePlan/ResponseEnvelope.
3. Extend telegram-bot only at transport mapping if new response variants require it; business decisions remain backend-owned.
4. Add Web assistant fixtures and OG render checks for ranking, comparison, partial data, semantic evidence and degraded message.
5. Confirm MAX readiness: same assistant endpoint/session mapping, no MAX-specific analytics or Jev logic.

### Tests

- backend/tests/modules/presentation/test_response_policy.py;
- backend/tests/api/test_assistant_api.py;
- frontend Vitest/Playwright for assistant/OG cards;
- Telegram adapter contract tests;
- OpenAPI drift and generated client checks.

### Acceptance criteria

- renderer never recomputes metrics;
- partial/unavailable data is visible;
- text/image/PDF choice remains policy-driven;
- Telegram/Web contracts do not import Jev SDKs;
- future MAX can consume same envelope.

### Dependencies, rollback and risks

Depends on T22 and existing presentation policy. Rollback keeps existing templates; optional evidence fields are additive.

## Task T24 — Benchmark, PostgreSQL plan and optional runtime budgets

### Implementation steps

1. Extend backend/scripts/profile_analytics.py and profile_queries.py with deterministic materialized metric query, multi-university mean/ranking, resolver/session decision, shadow latency, jevQL predicate budget and jev-tree candidate narrowing.
2. Use PostgreSQL EXPLAIN (ANALYZE, BUFFERS) fixtures for allow-listed queries; check indexes and N+1 counts.
3. Set measured gates, not invented SLAs:
   - no full-catalog Python load on common query;
   - no semantic reclassification on request-time materialized path;
   - bounded external calls/concurrency;
   - stable repeated-query/cache result.
4. Add regression benchmark snapshots with environment/tool identity; mark informative vs blocking thresholds.
5. Test changed-only semantic/projection rebuild and cache invalidation after new ingestion.

### Tests

- PostgreSQL integration workflow;
- benchmark smoke in CI;
- repository query-count assertions;
- projection rebuild tests;
- optional service unavailable/slow tests.

### Acceptance criteria

- common analytics remains SQL/materialized;
- no N+1 regression;
- optional Jev cost/latency measurable and bounded;
- performance evidence attached to rollout review.

### Dependencies, rollback and risks

Depends on T22 and current projection repository. Rollback removes benchmark gate only; never loosens correctness tests.

## Commit checkpoint C7

After T22–T24: commit vertical acceptance corpus, presentation compatibility and performance evidence. Keep live Jev disabled until rollout gates pass.

## Phase Verification

- pytest backend/tests/e2e backend/tests/modules/analytics backend/tests/modules/conversation backend/tests/api -q
- python backend/scripts/profile_analytics.py --help
- python backend/scripts/profile_queries.py --help
- frontend lint/unit/build and Telegram contract tests
- PostgreSQL integration workflow with optional runtimes disabled

Expected result: all canonical scenarios pass, no redundant clarification is introduced, response rendering remains channel-neutral, and benchmark/query-count evidence is recorded.
