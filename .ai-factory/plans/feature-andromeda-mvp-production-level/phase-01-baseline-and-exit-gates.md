# Phase 1: Baseline, product truth, and exit gates

Plan: [index.md](index.md)

Tasks: MVP-001, MVP-002, MVP-003, MVP-004

Depends on: none

Priority: P0

## Objective

Create a reproducible evidence baseline for the transition. This phase does not
change product behavior. It turns the current repository state into explicit
flow contracts, regression evidence, and a release gate that can distinguish a
working private-alpha fixture from a production-capable MVP.

The phase must preserve the existing modular monolith, typed public contracts,
separate bounded contexts, and architecture tests. It must not introduce a
second orchestration layer merely to report status.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Area | Observed state | Consequence |
| --- | --- | --- |
| Repository baseline | HEAD 4088116, current branch feature/andromeda-mvp-production-level; pre-existing M frontend-next/next-env.d.ts and multiple untracked user artifacts | Baseline and later implementation must not overwrite those files |
| Backend vertical surface | backend/src/andromeda/api/main.py includes programs, admissions, admission_fit, compare, proftest, recommendations, events, campus, personal_route, admin_ops, auth, decision, health | A flow matrix can trace real API entrypoints rather than infer capabilities from documentation |
| Frontend surface | frontend-next/src/app/page.tsx routes home, flow, catalog, program, decision, compare, proftest, admission, recommendations, events, campus/personal route, account, and ops views | The product audit must test the user journey through the actual single-app router |
| Contracts | frontend-next/src/lib/generated.ts is generated from frontend-next/openapi.json; frontend-next/src/lib/types.ts aliases generated schemas | Contract drift and domain leakage need separate checks |
| Existing smoke | backend/scripts/run_andromeda_demo.py exists, but delegates to run_tracer_demo.py; CI invokes the wrapper with fixture mode and check | Existing green smoke is useful baseline evidence but is not yet a canonical production gate |
| Existing verification | backend architecture suite passed 13 tests; focused backend slice passed 90 tests; frontend unit suite passed 13 tests; frontend check-api-drift failed locally with OpenAPI request 404 because no API server was running | A clean-checkout gate must distinguish expected environment prerequisites from real regressions |
| Claims | README.md and docs/mvp.md say MVP / Private Alpha; docs/testing.md and docs/architecture.md claim a live taxonomy audit with 2,582 disciplines and fallback_unclassified = 0, but no executable metric with that name was found | Claims need an evidence owner and a documented confidence level |

## Files to Change

| Future change | Path |
| --- | --- |
| Capability and evidence matrix | docs/mvp-capability-matrix.md |
| Backend vertical smoke tests | backend/tests/vertical/test_mvp_production_flows.py |
| Frontend browser gate | frontend-next/tests/mvp-production-flow.spec.ts |
| Ingestion and source evidence fixtures | backend/tests/fixtures/mvp/ and backend/tests/ingestion/ |
| Release evidence/runbook | docs/mvp-production-level.md and docs/operations/mvp-release-checklist.md |
| Canonical commands | repository toolchain files selected in MVP-091; do not add a parallel command before that task |

## Task MVP-001: Build the five-flow capability truth matrix

### Intent

Replace broad aspirational language with an evidence-backed matrix for:

1. Kuda ya mogu postupit;
2. what to choose in a university;
3. which programs fit;
4. comparison of options;
5. short adaptive proftest start.

The matrix must identify what is implemented, what is partial, what is
source-dependent, and what is intentionally out of MVP. It must not classify a
typed not_available response as a completed capability.

### Implementation Steps

1. Enumerate the actual frontend entrypoints from
   frontend-next/src/app/page.tsx and the API route modules included by
   backend/src/andromeda/api/main.py.
2. For each flow, trace the concrete chain:
   route/component → frontend-next/src/lib/api.ts → generated OpenAPI schema →
   API route/dependency → module service → repository port → infrastructure
   repository/model → fixture/live source → response rendering.
3. Record the owning bounded context and public contract at each boundary.
   Use the existing DecisionContext, Recommendation, AdmissionFit, Proftest
   session, Comparison, Events, and Campus contracts; do not create a shared
   catch-all product contract.
4. Record every placeholder, source gap, empty state, and not_available field
   with the user-visible copy and the reason it is returned.
5. Mark each claim with one of the requested statuses and an evidence path.
   A claim without a path, symbol, test, or configuration reference remains
   unverified and cannot be used as an exit criterion.
6. Add a supported-universities/data-scope section that explicitly says
   BMSTU and HSE are adapter targets, which source-backed facts are available,
   and which Career Fit / Workload Readiness claims remain outside the MVP.

### Required Interfaces and Contracts

- Preserve generated OpenAPI types as the wire source of truth.
- Keep Content Fit, Admission Fit, Career Fit, and Workload Readiness distinct.
- Treat sourceGaps, missingData, optional metrics, and provenance as typed
  states, not as UI strings inferred from null values.
- Keep explicit shortlist state separate from derived suggestions.
- Record profile scope and account transfer behavior as part of the flow
  contract, not as frontend-only behavior.

### Error Handling and Logging

- The matrix must distinguish an API unavailable error, empty valid result,
  insufficient source data, and a product capability that is intentionally not
  exposed.
- Smoke evidence must include a correlation/request identifier when captured
  from HTTP logs, but must never include cookies, API keys, database URLs, or
  raw personal profile contents.
- Log source gaps and run IDs by stable identifiers only; redact source body
  content and credentials.

### Tests

- Existing backend contract and vertical tests:
  backend/tests/api/, backend/tests/contracts/, backend/tests/vertical/.
- Existing frontend flow coverage:
  frontend-next/tests/decision-analytics.spec.ts,
  frontend-next/tests/proftest-decision-integration.spec.ts,
  frontend-next/tests/proftest.spec.ts,
  frontend-next/tests/catalog-programs.spec.ts,
  frontend-next/tests/legacy-flow-compat.spec.ts.
- Documentation also names admissions.spec.ts, recommendations.spec.ts, and
  admission-fit.spec.ts; source inventory did not find those exact files, so
  they are proposed additions rather than current evidence.
- Add matrix assertions in backend/tests/contracts/ or a documented
  release-evidence test location only after the contract is finalized.

### Acceptance Criteria

- Every one of the five user flows has an owner, entrypoint, contract,
  data source, response state, and known limitation.
- No row calls Career Fit, Workload Readiness, or a comparable metric
  implemented when the backend returns not_available or only evidence text.
- The matrix identifies exact backend/frontend tests that prove the row.
- A reviewer can tell which claims are fixture-only, source-dependent, or
  production-supported without reading implementation details.

### Verification

- Review all route and contract references against the current OpenAPI export.
- Run backend architecture tests and the focused recommendation/proftest
  suite.
- Run frontend unit tests and the existing browser tests required by each
  matrix row.
- Record any skipped live-source or deployment checks as explicit unknowns.

## Task MVP-002: Define the executable MVP production smoke

### Intent

Turn the exit criteria into a small, deterministic smoke that starts from a
clean PostgreSQL-like environment, loads supported fixture data, runs the
critical anonymous user journey, and verifies both positive and degraded
states.

### Implementation Steps

1. Reuse the current fixture adapters and canonical ingestion runner rather
   than inserting fixture rows directly into tests.
2. Define the data setup boundary: Alembic upgrade, BMSTU and HSE fixture
   ingestion, API start, frontend start, and test cleanup.
3. Cover anonymous profile/session creation, proftest start/resume/complete,
   recommendation explanation, admission data with an explicit gap, shortlist
   mutation, comparison, final choice, reload, logout/account transfer, and
   a failed/retried ingestion run.
4. Add one degraded fixture case where data is absent but the response remains
   useful and honest.
5. Keep the smoke independent of live university websites. Live reproducibility
   is a separate release evidence requirement.

### Required Interfaces and Contracts

- Use existing public HTTP contracts and generated client types.
- Assert that recommendation output includes Content Fit evidence and its
  confidence/provenance contract once MVP-050 lands.
- Assert Admission Fit does not change Content Fit ranking.
- Assert explicit shortlist is not silently pruned by a recommendation refresh.
- Assert all mutation calls carry the expected revision and handle 409.

### Error Handling and Logging

- A failed setup step must identify stage, university, run ID, database target
  class, and safe error code; never emit credentials or source payloads.
- Test logs must keep per-request correlation IDs and per-ingestion run IDs
  so a failure can be diagnosed from CI artifacts.
- A missing optional source must be reported as a known partial-data assertion,
  not silently converted into a passed full-capability assertion.

### Tests

- Target new paths:
  backend/tests/vertical/test_mvp_production_flows.py and
  frontend-next/tests/mvp-production-flow.spec.ts.
- Reuse backend/scripts/run_andromeda_ingestion.py and the canonical demo
  only after the tracer wrapper migration in MVP-010.
- Run with disposable PostgreSQL in CI and with SQLite only for fast contract
  checks; do not use the SQLite path as evidence of staging readiness.

### Acceptance Criteria

- One documented command can run the fixture smoke from a clean checkout.
- The smoke proves the critical journey end to end and checks loading,
  error, empty, and partial-data states.
- The smoke fails when the API returns a misleading placeholder for a claimed
  capability.
- The smoke produces safe, downloadable evidence containing commit, migration
  head, fixture manifest hashes, and test results.

### Verification

- Execute on SQLite test mode and PostgreSQL 16 disposable mode.
- Execute through the Docker deployment shape from deploy/yc/compose.yaml
  after image/bootstrap work is complete.
- Compare smoke results before and after each risky migration checkpoint.

## Task MVP-003: Freeze current behavior before risky changes

### Intent

Create regression evidence before migrating tracer wrappers, recommendation
contracts, ingestion projection, taxonomy outcomes, authentication, or
frontend states. The old path must not be deleted simply because it is named
legacy.

### Implementation Steps

1. Capture current JSON responses for supported fixture scenarios, excluding
   secrets and volatile timestamps.
2. Capture current canonical counts, source hashes, program IDs, admission
   identities, area vectors, recommendation order, and profile revisions.
3. Capture compatibility behavior for old proftest endpoints and the current
   session API, including stale question IDs and 409 revision behavior.
4. Capture account transfer, anonymous cookie isolation, ops-key failure, and
   ingestion failure lifecycle behavior.
5. Convert only stable business behavior into assertions; do not snapshot
   internal SQLAlchemy rows or incidental log wording.

### Required Interfaces and Contracts

- Canonical IDs, public DTOs, status enums, and source-gap codes are stable
  comparison keys.
- Volatile fields use explicit normalization rules.
- Intended behavior changes must be listed as migrations with updated
  acceptance criteria, not hidden by broad snapshots.

### Error Handling and Logging

- Redact profile answers, password-derived values, cookies, API keys, and
  database connection strings.
- Include fixture manifest hash and migration revision in evidence metadata.
- Fail the evidence collector closed if a secret-like field is detected.

### Tests

- Existing suites:
  backend/tests/integration/test_demo_runner.py,
  backend/tests/integration/test_bmstu_full_ingestion.py,
  backend/tests/integration/test_hse_full_ingestion.py,
  backend/tests/api/test_proftest_sessions_api.py,
  backend/tests/api/test_auth_api.py,
  backend/tests/api/test_admin_ops_api.py.
- Add regression tests next to the owning context, not a single snapshot
  test that bypasses domain boundaries.

### Acceptance Criteria

- Every planned destructive or compatibility change has a before-state
  assertion.
- At least one fixture and one PostgreSQL-backed result are recorded for each
  critical path.
- Evidence is reproducible by another agent without access to private
  credentials.

### Verification

- Run the targeted 90-test backend slice and the 13-test architecture suite.
- Run the 13 frontend unit tests.
- Record the current local OpenAPI drift command limitation: it requires a
  running API and returned HTTP 404 when run without one.

## Task MVP-004: Formalize release decisions and unknowns

### Intent

Make unknown runtime facts visible. The repository currently proves fixture
paths and many unit/integration cases, but it does not prove live BMSTU/HSE
repeatability, a deployed clean checkout, production traffic behavior, or
the claimed live taxonomy audit.

### Implementation Steps

1. Create an evidence ledger with columns: claim, current status, evidence,
   missing evidence, owner, next verification, and release impact.
2. Mark live source, deployment, backup restore, concurrency, rate-limit, and
   browser accessibility checks as unverified until executed.
3. Record intentional decisions that must not be changed: modular monolith,
   bounded contexts, public contracts, strict typing, fail-closed blocking
   data, and adapter-specific university logic.
4. Require an explicit decision before changing product scope or promoting
   Career Fit/Workload Readiness from out-of-scope.

### Required Interfaces and Contracts

- The ledger is documentation/release evidence, not a runtime source of
  truth for domain behavior.
- Use stable task IDs and exit criteria from index.md.

### Error Handling and Logging

- Unknown is not equivalent to passed or failed.
- Do not publish an evidence report containing environment secrets or raw
  source documents.

### Tests

- Validate the ledger links to existing files and test names.
- Add a CI check later in MVP-092 that refuses a release claim when a P0
  evidence row is still unverified.

### Acceptance Criteria

- The plan can state exactly why the repository is not yet MVP Production
  Level without relying on general impressions.
- No critical unknown is silently assumed green.
- Intentional architectural complexity is explicitly protected.

### Verification

- Review with the architecture rules in .ai-factory/RULES.md and AGENTS.md.
- Re-run the evidence commands after each later phase and update only the
  ledger, not historical baseline artifacts.

## Phase Risks and Mitigations

- **Risk:** baseline snapshots freeze accidental behavior. **Mitigation:**
  snapshot public contracts and business outcomes only; label intentional
  behavior changes.
- **Risk:** a new smoke becomes a second orchestration implementation.
  **Mitigation:** keep it as a test/release harness over canonical API,
  ingestion, and composition paths.
- **Risk:** local untracked data is mistaken for repository evidence.
  **Mitigation:** record commit-controlled fixtures and manifest hashes only.

## Phase Completion Checklist

1. The five-flow matrix exists and has evidence for every status.
2. Critical baseline behavior has regression evidence.
3. The production smoke design names setup, teardown, data, and failure
   semantics.
4. Unknown runtime facts are listed instead of inferred.
5. No product or architecture scope was changed in this phase.
