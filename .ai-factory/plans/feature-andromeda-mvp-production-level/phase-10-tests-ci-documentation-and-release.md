# Phase 10: Test system, CI, developer experience, documentation, and release

Plan: [index.md](index.md)

Tasks: MVP-090, MVP-091, MVP-092, MVP-093, MVP-094, MVP-095

Depends on: MVP-010, MVP-012, MVP-022, MVP-041, MVP-051, MVP-061, MVP-071, MVP-080, MVP-083

Priority: P0 for release gate; P1 for developer experience; P2/P3 for later quality

## Implementation status

Implemented locally through the canonical path. Test taxonomy, coverage
configuration, local targets, CI gates, deployment contract checks, current
documentation, release evidence, disposable PostgreSQL deployment, TLS
gateway smoke, backup/restore, and failed-image rollback are now exercised.
On 2026-09-19, the repository-controlled `source_health.py --mode live
--university all` probe also completed successfully against a disposable,
migrated SQLite database and wrote
`artifacts/release/source-health-20260919.json`. It accepted BMSTU and HSE as
`degraded` with typed source gaps and no blocking gaps (BMSTU 344 snapshots,
134 programmes, 100% curriculum/admission/taxonomy coverage; HSE 1,493
snapshots, 96 programmes, 85/96 curriculum, 49/96 admission, 84.59% taxonomy
coverage). A `core.autocrlf=false` clean-checkout simulation with documented
`npm ci` also passed the full canonical local target (`535 passed, 8 skipped`,
frontend/Telegram/fixture/migration/production smoke included). Remote GitHub
Actions has a successful baseline `main` run for commit `4088116`, but no
feature-branch run exists for this uncommitted implementation snapshot, and
the source-health workflow has no recorded run. MVP-095 remains open because
an owner-attached CI/repeatability/deployment record is still external release
evidence, not a fact a local snapshot can establish. The current worktree was
also rerun through `python scripts/andromeda.py full` after the clean-checkout
simulation: it exited 0 with backend `535 passed, 8 skipped`, frontend unit
`19 passed`, Telegram `14 passed`, migration checks `22 passed`, backend
coverage `87%`, fixture ingestion, and production-like smoke all passing.
The disposable PostgreSQL 16 target was also rerun with a unique ephemeral
container: `5 passed` across PostgreSQL ingestion, smoke, and user-profile
persistence; the container had no persistent volume and was removed after the
run.
The release metadata ledger now records a secret-free clean/dirty worktree
state and hashes of tracked diff/untracked manifest; `--require-clean` fails
closed and is part of the CI documentation job. This improves checkpoint
attribution but does not replace the still-missing owner-attached CI,
deployment, restore, and authorized live-source records.

## Objective

Provide one obvious verification path from clean checkout to fixture smoke,
backend/frontend/integration/E2E checks, production-like deployment smoke, and
release evidence. Make tests more useful without reducing their architectural
coverage or deleting valid boundary checks.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| Test breadth | CONFIRMED strong baseline | backend tests include api, architecture, contracts, infrastructure, ingestion, integration, modules, scripts, vertical; frontend has unit/E2E; Telegram has tests |
| Critical business coverage | PARTIALLY CONFIRMED | recommendation/proftest/decision/admission/ingestion tests exist, but negative states, provenance propagation, concurrency, and some UI claims have gaps |
| Duplicate/legacy tests | PARTIALLY CONFIRMED | tracer runner tests import compatibility paths; some docs list E2E filenames not present |
| Coverage reporting | CONFIRMED GAP | no pytest-cov/coverage gate, Vitest coverage configuration, or CI coverage artifacts found |
| CI | PARTIALLY CONFIRMED | .github/workflows/andromeda-ci.yml covers backend, frontend, fixture/fullstack, PostgreSQL, proftest, Telegram; repeated installs/Poppler and no explicit architecture/coverage/dependency gate |
| OpenAPI drift | PARTIALLY CONFIRMED | frontend check-api-drift exists; without a running API local command returned 404, while OPENAPI_FILE=openapi.json mode passed |
| Migration gate | PARTIALLY CONFIRMED | PostgreSQL CI applies Alembic head, but readiness/schema-head drift and an explicit migration check should be named |
| Developer setup | PARTIALLY CONFIRMED | docs/getting-started.md, docs/postgresql.md, Docker/Poppler/Playwright/Telegram docs exist; commands and env names are duplicated/inconsistent |
| Deployment | PARTIALLY CONFIRMED | deploy/yc compose and staging runbook exist; clean image seed/port/env/reproducibility issues remain |
| Documentation truth | PARTIALLY CONFIRMED | README/docs say MVP / Private Alpha; taxonomy and migration-head claims are stale/unverified; backend README retains tracer CLI |

## Files to Change

| Future change | Path |
| --- | --- |
| Test configuration | backend/pyproject.toml, frontend-next/package.json, vitest.config.mjs, playwright.config.ts, telegram-bot/pyproject.toml |
| Canonical command entrypoint | repository toolchain file chosen after inventory; backend/scripts and frontend scripts |
| CI | .github/workflows/andromeda-ci.yml, .github/workflows/source-health.yml |
| Tests/artifacts | backend/tests/, frontend-next/tests/, telegram-bot/tests/ |
| Deployment smoke | deploy/yc/, ops/postgres/, docs/deployment.md |
| Current docs | README.md, backend/README.md, docs/{mvp,testing,getting-started,configuration,postgresql,telegram-bot,architecture}.md |
| Historical docs | docs/archive/ and release evidence/runbook paths |

## Task MVP-090: Make the test system critical-logic driven

### Intent

Retain the large test suite while making it clear what each layer proves and
where critical business risks remain.

### Implementation Steps

1. Build a test taxonomy matrix:
   unit/domain, contract/OpenAPI, architecture, repository/database,
   ingestion/parser, vertical/API, frontend unit, E2E, Telegram, security,
   smoke, and production-like deployment.
2. Mark critical rules:
   admission separation, Content Fit determinism, anti-interest penalty,
   provenance/gaps, taxonomy normalization, canonical identity,
   atomic/quality-gated projection, optimistic revision, session stale/expiry,
    auth isolation/transfer, no-shortlist-prune, and JSON-wire enum
    compatibility across proftest/decision/analytics/admission contracts.
3. Map each rule to meaningful tests, not only line coverage.
4. Remove/merge duplicate tests only after checking their boundary/value; do
   not drop architecture or compatibility checks due to count.
5. Replace brittle whole-response snapshots with semantic assertions where
   volatile fields or implementation details are frozen.
6. Add negative cases and failure injection identified by Phases 3–9.
7. Add backend and frontend coverage reports with path exclusions limited to
   generated/metadata files, and publish reports as CI artifacts.
8. Set coverage thresholds only after a baseline run; enforce critical-path
   test presence separately from percentage.

### Required Interfaces and Contracts

- Test names state layer and behavior.
- Fixtures use canonical IDs and manifest/source hashes.
- Integration tests use disposable PostgreSQL for database semantics.
- Tests do not rely on source network availability except separately gated
  operational checks.

### Error Handling and Logging

- CI test artifacts include safe logs, junit/HTML reports, commit, schema
  revision, and fixture manifest hashes.
- Failed assertions include flow/stage/run ID where available.
- No test artifact may contain secrets or live profile data.

### Tests

- Existing backend test tree and frontend tests.
- Add/organize tests under clear paths without moving unrelated user files.
- Backend command: python -m pytest -q backend/tests
- Frontend command: npm run test:unit
- Telegram command: python -m pytest -q telegram-bot/tests
- Add coverage commands once tool configuration is selected.
- Add HTTP/schema regression cases for valid JSON string enum values and
  invalid values returning 422; keep these cases in the critical contract
  matrix because strict-model/runtime-version drift has caused real deployment
  failures.

### Acceptance Criteria

- Every critical business rule has at least one domain/contract/integration
  test and, where user-visible, one E2E assertion.
- Coverage report is published but not used as the sole quality claim.
- Duplicate/brittle tests have a documented disposition.
- No current architecture boundary test is removed.
- The critical contract matrix includes the JSON-wire enum compatibility cases
  and identifies their backend/frontend/runtime smoke coverage.

### Verification

- Run full backend, frontend unit, Telegram, and selected E2E suites.
- Inspect reports for missing critical paths and secret leakage.
- Compare duration/flakiness before changing parallelization.

## Task MVP-091: Create one canonical local verification/bootstrap path

### Intent

Allow a new developer or AI agent to set up, run, and verify the system with a
small number of documented commands while preserving separate backend,
frontend, ingestion, PostgreSQL, Playwright, and Telegram concerns.

### Implementation Steps

1. Inventory current commands in README.md, backend/README.md,
   docs/getting-started.md, docs/postgresql.md, docs/testing.md,
   docs/telegram-bot.md, CI, package scripts, and deployment docs.
2. Choose the existing repository toolchain mechanism that can express
   canonical targets; do not add Makefile/Taskfile only by preference.
3. Define targets for:
   fast checks, backend tests, frontend unit/lint/build, ingestion fixture,
   integration/PostgreSQL, Playwright, Telegram, full CI, production smoke,
   OpenAPI export/drift, migration upgrade/check, and security/dependency
   audit.
4. Make prerequisites explicit: Python version/dependencies, Node/npm,
   PostgreSQL/Docker, Poppler, Playwright Chromium, env examples, ports,
   and Telegram optional secrets.
5. Provide a non-destructive fixture path using disposable DB/data; never
   require user secrets or touch pre-existing untracked data.
6. Ensure the canonical demo/ingestion names from MVP-012 are used.
7. Make command output identify what it ran and how to recover.

### Required Interfaces and Contracts

- Test entrypoints call existing scripts/API/contracts, not duplicate logic.
- Backend/frontend use the same OpenAPI artifact and database target policy.
- Development SQLite remains a fast/test option; PostgreSQL is required for
  staging/production-like checks.

### Error Handling and Logging

- Missing prerequisite gives a clear install/action message and exits
  non-zero; no silent skip for mandatory checks.
- Commands redact env values and print only variable names/target classes.
- Cleanup is scoped to disposable test resources and never deletes workspace
  user files.

### Tests

- Validate every target on Windows PowerShell and CI Linux where supported.
- Run docs command snippets in clean temporary checkout/container.
- Add a bootstrap smoke that reaches health/live, health/ready, catalog,
  decision, and fixture ingestion.

### Acceptance Criteria

- README has one canonical quick path and links to detailed runbooks.
- A new agent can identify required commands without knowing internal test
  directories.
- Fast checks and full CI differ explicitly by scope and runtime cost.
- No command refers to removed tracer wrappers after MVP-012.

### Verification

- Execute from clean checkout with no pre-existing local database.
- Execute PostgreSQL/Playwright/Telegram optional paths with documented
  prerequisites.
- Compare command results to CI jobs.

## Task MVP-092: Make CI strict, efficient, and explanatory

### Intent

Keep all meaningful checks while reducing redundant setup and making failures
actionable. Never hide a failing check by deleting assertions or skipping
jobs.

### Implementation Steps

1. Define required gates: formatting/lint/type, architecture, unit/domain,
   contracts/OpenAPI drift, migrations/schema, ingestion fixture, backend/API,
   frontend build/unit, PostgreSQL integration, E2E, Telegram, security/
   dependency audit, coverage, and production smoke.
2. Split independent jobs and cache pip/npm/Playwright/system dependency
   inputs where safe.
3. Avoid repeated Python/npm installs while keeping job isolation explicit.
4. Add a migration check from empty DB and current head.
5. Add OpenAPI export/drift check using tracked artifact or started backend;
   do not leave a 404-only local invocation as the only documented mode.
6. Add architecture and dead-surface reports as explicit jobs.
7. Add coverage and critical-test reports as artifacts.
8. Keep live source-health in a separate non-PR operational workflow, but
   persist/alert results and ensure it cannot mutate data by default.
9. Add CI annotations for skipped PostgreSQL/browser checks and why.

### Required Interfaces and Contracts

- CI uses the canonical commands from MVP-091.
- Job environment uses ANDROMEDA_DATABASE_URL and the documented current
  migration head; deprecated variables are test-only during transition.
- Artifacts are safe and attributable to commit/run.

### Error Handling and Logging

- Each job reports prerequisite failure separately from assertion failure.
- Logs are redacted and retained long enough for diagnosis.
- A flaky test is quarantined only with owner, issue, retry policy, and
  non-release status; never silently ignored.

### Tests

- .github/workflows/andromeda-ci.yml
- .github/workflows/source-health.yml
- Validate backend all tests, mypy, architecture, fixture all-university,
  frontend drift/unit/lint/build, fullstack E2E, PostgreSQL, proftest,
  Telegram, security, coverage, and migration gates.

### Acceptance Criteria

- Full CI passes from clean checkout with documented dependencies.
- Required checks are explicit and no meaningful current gate is removed.
- Parallel/cached jobs reduce duplicate setup without sharing mutable state.
- Artifacts include test reports, coverage, migrations, OpenAPI, and smoke
  evidence.

### Verification

- Run CI on a branch with intentional failures in each new gate and confirm
  actionable failure.
- Run with network/source unavailable and verify only source-health is
  affected, not fixture/product tests.
- Review workflow diff for secrets and broad path filters.

## Task MVP-093: Prove production-like deployment and rollback

### Intent

Show that a tracked clean checkout can produce the documented staging shape,
apply migrations, run frontend/backend/Telegram/Caddy, pass smoke, and
recover from a failed release.

### Implementation Steps

1. Build backend/frontend/Telegram images from tracked inputs with pinned/
   reproducible dependencies. Verify both supported packaging shapes: the
   frontend Docker runner entrypoint (/app/server.js) and the VM/systemd
   release artifact expected by deploy/yc/andromeda-frontend.service and
   cloud-init.yaml at
   frontend-runtime/.next/standalone/server.js. Use
   frontend-next/scripts/prepare-standalone.mjs or replace it only with a
   documented equivalent.
2. Start deploy/yc/compose.yaml with disposable PostgreSQL and secret
   environment values outside Git.
3. Run Alembic upgrade explicitly; verify readiness at the expected head.
4. Run fixture ingestion, catalog/program, admission, comparison, anonymous
   decision, proftest, account transfer, and ops smoke.
5. Validate internal port 8020, explicit server-side frontend internal URL,
   frontend same-origin /api with no localhost fallback, Telegram renderer/
   backend URLs, Caddy HTTPS/domain assumptions, and the server-side OG route.
6. Exercise backup/restore and previous-image forward-compatibility rollback.
7. Record image digest, migration revision, fixture/source evidence, prepared
   standalone entrypoint/path, runtime commit/hash, and smoke results.

### Required Interfaces and Contracts

- Staging/production does not fall back to untracked SQLite seed.
- Health/readiness and API routes have stable safe contracts.
- Docker and VM/systemd release artifacts have an explicit, tested entrypoint
  contract; their runtime environment points to the same API/database policy.
- Rollback follows Alembic compatibility rules; no applied migration edit.

### Error Handling and Logging

- Deployment logs include service, image, migration, health, and smoke stage;
  no secrets.
- Failed migration does not start a partially compatible service.
- Restore smoke uses isolated database and redacts dump paths/credentials.

### Tests

- deploy/yc/compose.yaml and docs/deployment.md runbook checks.
- Docker image build tests in CI.
- New production smoke script/test from MVP-002.
- PostgreSQL backup/restore and migration compatibility checks.
- Docker runner and VM/systemd-like standalone packaging checks, including
  public same-origin /api and server-side OG/internal fetch.

### Acceptance Criteria

- Production-like stack starts from clean checkout and passes smoke.
- Failure of DB/source/API/frontend/Telegram is diagnosable.
- Both Docker and VM/systemd-like packaging shapes start from the documented
  artifact layout; browser requests do not fall back to localhost and
  server-side frontend fetches reach backend:8020.
- Previous image rollback is safe for the schema compatibility boundary.
- Deployment evidence is reproducible and secret-free.

### Verification

- Execute on disposable VM/compose environment.
- Run a Docker packaging smoke and a separate VM/systemd-like extracted-release
  smoke; verify the exact standalone server.js path and runtime commit/image
  parity in both.
- Run clean restore and smoke after restore.
- Confirm no user data or untracked workspace file was used as a seed.

## Task MVP-094: Reconcile current docs, archive, and AI workflow

### Intent

Make README and operational documentation describe reality, while keeping
historical/ADR material available and preserving evidence guardrails for
future agents.

### Implementation Steps

1. Reconcile stage wording: do not call the project MVP Production Level
   until MVP-095 passes; before then name it Private Alpha / transition plan.
2. Update README supported universities, source/data scope, experimental
   capabilities, known gaps, canonical commands, and production boundary.
3. Split current docs, operational runbooks, and historical/archive notes.
4. Correct stale migration head, taxonomy audit, E2E filenames, tracer CLI,
   environment variable names, ports, and deployment claims.
5. Document Career Fit, Workload Readiness, ML, reviews, mass coverage, and
   guaranteed admission as out of scope unless separately approved.
6. Audit AGENTS.md, .ai-factory/RULES.md, configuration paths, and skill
   guidance for obsolete paths/rituals; preserve evidence/no-failure-hiding
   guardrails.
7. Add dependency inventory and security scan results with ownership.
8. Do not delete history or untracked user artifacts in a documentation
   cleanup task.

### Required Interfaces and Contracts

- Documentation links to actual paths/commands and generated OpenAPI.
- Archive docs have no executable stale instructions presented as current.
- AI workflow requires context → analysis → plan → implementation → tests →
  verification and source evidence.

### Error Handling and Logging

- Runbook failures state symptom, safe diagnostic, recovery, and escalation.
- Never document example credentials that could be mistaken for real secrets.
- Operational examples use placeholders and secret-manager language.

### Tests

- Add documentation link/path checker in CI.
- Execute README/docs command snippets in disposable environment.
- Validate AGENTS and .ai-factory path references against repository state.

### Acceptance Criteria

- A reader can tell current capability, experimental/out-of-scope capability,
  and history without inference.
- Every documented command exists and has current prerequisites.
- No README or MVP doc claims unsupported live audit/production readiness.
- AI instructions are accurate and keep architectural guardrails.

### Verification

- Run source/link audit excluding generated/raw fixture payloads.
- Review docs against capability matrix and release evidence.
- Run CI documentation gate.

## Task MVP-095: Run final exit gate and preserve rollback checkpoints

### Intent

Provide the evidence needed to change the product status from Tracer Bullet /
Private Alpha foundation to MVP Production Level only when the user’s
16-point exit criteria are actually true.

### Implementation Steps

1. Freeze release commit and record migration/schema head, image digests,
   dependency versions, taxonomy/policy versions, and source fixture/live
   evidence.
2. Run every P0 acceptance test and every exit checklist item.
3. Verify all five flows end to end in fixture and production-like deployment.
4. Verify no misleading product-visible placeholder remains in claimed
   capabilities.
5. Verify BMSTU/HSE ingestion reproducibility, quality gate, retry, failed
   run diagnostics, and last-good protection.
6. Verify critical business tests, full CI, OpenAPI/schema drift, security
   baseline, readiness/migrations, frontend state handling, and production
   smoke.
7. Create a release evidence report with pass/fail/unknown and owner for every
   item. Unknown means no status promotion.
8. Tag/checkpoint the release and retain previous image/migration/backup
   rollback references.

### Required Interfaces and Contracts

- Exit gate is evidence-based, not a line-count/coverage-only threshold.
- Public status claims match docs and deployment evidence.
- Rollback/fallback is documented for source, schema, UI, and contract changes.

### Error Handling and Logging

- A failed exit item includes reproducible command, safe artifact, root cause,
  and next action.
- Release report excludes secrets and personal data.
- No failing check is hidden, weakened, or deleted to pass the gate.

### Tests

- Full canonical CI command.
- Production smoke command.
- Backend/frontend/Telegram suites.
- Security/dependency/migration/OpenAPI/architecture checks.
- Live source reproducibility check only with explicitly authorized staging
  credentials/network and safe data target.

### Acceptance Criteria

All of the user-requested exit criteria are true:

1. Main user flows are end to end.
2. No product-visible placeholder is presented as implemented capability.
3. BMSTU/HSE ingestion is reproducible.
4. Ingestion errors are diagnosable.
5. Schema/migrations are stable.
6. Critical business rules have meaningful tests.
7. Full CI passes from clean checkout.
8. Production-like deployment is documented and runnable.
9. Frontend handles loading/error/empty/partial states.
10. Recommendation is explainable.
11. Missing data is correctly represented.
12. Security baseline passes.
13. Documentation matches code.
14. No critical-path tracer shortcuts remain.
15. Production smoke exists and passes.
16. A new university does not require generic-domain changes without a real
    domain reason.

### Verification

- Attach release evidence to the commit/plan handoff.
- Review with architecture, product, operations, and security owners.
- If any item is unknown or fails, keep status at Private Alpha transition,
  not MVP Production Level.

## Phase Risks and Mitigations

- **Risk:** CI becomes too slow or opaque. **Mitigation:** canonical targets,
  safe caching, parallel independent jobs, and clear fast/full split.
- **Risk:** documentation cleanup deletes useful history. **Mitigation:** move
  historical material to archive with links; do not mass-delete.
- **Risk:** release status is promoted from fixture-only evidence. **Mitigation:**
  require production-like deployment and explicitly authorized live evidence.

## Phase Completion Checklist

1. Test layers and critical rules are mapped and reported.
2. One bootstrap/verification path is documented and runnable.
3. CI is strict, cached/parallel where safe, and artifact-producing.
4. Production-like deployment, backup/restore, and rollback are exercised.
5. Current docs/AI workflow match repository state.
6. Final exit report is all-pass with no unresolved critical unknowns.
