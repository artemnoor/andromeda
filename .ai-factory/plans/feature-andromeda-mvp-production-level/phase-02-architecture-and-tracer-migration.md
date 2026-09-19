# Phase 2: Architecture ownership and tracer-bullet migration

Plan: [index.md](index.md)

Tasks: MVP-010, MVP-011, MVP-012, MVP-013

Depends on: MVP-001, MVP-003

Priority: P0 for runtime ownership; P1 for cleanup

## Objective

Make the existing serious architecture the architecture that actually runs.
This phase does not flatten bounded contexts or remove layering. It removes
ambiguous runtime ownership, makes compatibility explicit, and retires
tracer-bullet paths only after parity evidence exists.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| Subject-module dependency direction | FALSE POSITIVE for broad violation | backend/tests/architecture/test_module_boundaries.py and Graphify report show no internal import cycles; 13 architecture tests passed |
| Modular monolith / bounded contexts | INTENTIONAL | .ai-factory/RULES.md, docs/architecture.md, backend/src/andromeda/modules/* |
| Duplicate composition root | CONFIRMED | backend/src/andromeda/composition/container.py exports AndromedaContainer/build_container, but source-only search found no active caller; runtime wiring is in backend/src/andromeda/api/dependencies/services.py and does not have identical current coverage |
| Dead or consumer-less ports | CONFIRMED | ComparisonSummaryServicePort, CurriculumRepository, ProgramRepository, DisciplineRepository, and DisciplineIdentityResolver definitions have no production consumers in source-only search; identity resolver service is separately tested |
| Tracer runner | CONFIRMED | backend/scripts/run_andromeda_demo.py delegates to run_tracer_demo.py; run_tracer_demo.py imports run_tracer_bullet.py; legacy tests import those modules |
| Tracer database seed | CONFIRMED | backend/Dockerfile copies data/tracer.db, backend/docker-entrypoint.sh bootstraps /app/data/tracer.db, while the default URL names /app/data/andromeda.db; data/tracer.db is not tracked |
| Retired spike | OUTDATED as active runtime; workspace hygiene remains | docs/archive/proftest-spike.md and runtime surface test say executable spike manifests are gone; an untracked proftest-spike directory still exists and must not be deleted in this plan |
| Compatibility facades | INTENTIONAL, bounded | proftest ranking.py, matching.py, explanations.py are allowlisted by the architecture test and documented as one-cycle compatibility surfaces |

## Files to Change

| Future change | Path |
| --- | --- |
| Single canonical composition root | backend/src/andromeda/api/dependencies/services.py and/or backend/src/andromeda/composition/container.py |
| Boundary gates | backend/tests/architecture/test_module_boundaries.py and new same-module layer test |
| Canonical runner | backend/scripts/run_andromeda_demo.py, backend/scripts/run_andromeda_ingestion.py, new canonical runner module under backend/src/andromeda/composition or backend/scripts |
| Compatibility tests | backend/tests/scripts/test_tracer_events_runner.py, test_tracer_campus_runner.py, backend/tests/integration/test_demo_runner.py, test_tracer_bullet.py |
| Stale runtime metadata | backend/Dockerfile, backend/docker-entrypoint.sh, backend/README.md, package metadata/egg-info if tracked |
| Historical archive | docs/archive/proftest-spike.md and a new tracer migration note; do not alter existing history claims without evidence |

## Task MVP-010: Establish one canonical composition root

### Intent

Resolve the confirmed ambiguity between the unused
AndromedaContainer/build_container and the API dependency wiring. The result
must retain typed ports and repositories while ensuring every runtime surface
uses the same wiring for current profile, ingestion, auth, decision,
recommendation, and proftest services.

### Implementation Steps

1. Inventory all service factories and dependency providers in
   backend/src/andromeda/api/dependencies/services.py and
   backend/src/andromeda/composition/container.py.
2. Compare their returned object graphs, including current profile,
   ingestion-run service, retry behavior, auth repositories, and decision
   repositories.
3. Choose one owner based on actual runtime usage. Either make
   build_container the provider used by API/scripts, or reduce it to a
   typed composition implementation behind the API provider. Do not leave
   two independently maintained graphs.
4. Add a typed composition contract that can be inspected in tests without
   importing FastAPI routes or ORM models into subject modules.
5. Keep infrastructure construction in composition/API outer layers and keep
   business logic in module services.
6. Update Telegram and ingestion scripts to consume the canonical provider
   through the documented outer boundary.

### Required Interfaces and Contracts

- Every module receives existing repository.ports or contracts.public types.
- No subject module may import the chosen composition root.
- The composition object must expose all services currently reachable through
  API dependencies, including profile and ingestion-run operations.
- A single database session/engine policy must be visible at the outer
  boundary; no hidden second engine or SQLite fallback may be introduced.

### Error Handling and Logging

- Composition failures must fail at startup with a safe dependency name and
  environment, not with a partially initialized application.
- Do not log connection strings, API keys, session cookies, or constructed
  profile data.
- Include composition version/commit in startup diagnostics only if the
  repository already has a safe build metadata mechanism.

### Tests

- Add/update backend/tests/architecture/test_composition_root.py.
- Extend backend/tests/api/ and backend/tests/integration/ fixtures to assert
  API dependencies and script entrypoints receive equivalent services.
- Run backend/tests/architecture/test_module_boundaries.py and
  backend/tests/architecture/test_runtime_surface_inventory.py.
- Run backend/tests/integration/test_demo_runner.py and current profile,
  decision, auth, and ingestion API suites.

### Acceptance Criteria

- There is exactly one documented active composition graph.
- No service used by an API route is absent from the canonical graph.
- No source-only runtime path constructs a competing service graph.
- Architecture tests fail if a future provider bypasses the canonical graph.

### Verification

- Use a source-only import/reference scan excluding generated graph outputs.
- Start the API in test mode and exercise health, decision, proftest,
  recommendation, and ops dependencies.
- Compare the before-state regression evidence from MVP-003.

## Task MVP-011: Strengthen architecture gates without flattening architecture

### Intent

Close the gap between the current boundary tests and the full intended
architecture. Current tests protect cross-module imports but do not detect
same-module layer direction, dead public ports, duplicate composition roots, or
unowned compatibility paths.

### Implementation Steps

1. Keep the existing subject-module allowlist and public contract/repository
   port rule as the primary guard.
2. Add AST/source checks for subject-module internal direction:
   domain must not import services/repository; contracts must not import
   infrastructure; repository ports must not import concrete adapters.
3. Add a report-only dead abstraction check based on source consumers,
   excluding tests and intentional public exports; require an explicit
   annotation/registry entry before deleting anything.
4. Add a composition-root uniqueness check for runtime constructors.
5. Add compatibility facade checks that require a documented owner, expiry
   condition, parity test, and allowlisted imports.
6. Keep architecture tests deterministic and independent of installed
   database/network services.

### Required Interfaces and Contracts

- The test must recognize all current subject modules:
  admin_ops, admission_fit, admissions, auth, campus, comparison, curricula,
  decision, disciplines, events, personal_route, proftest, programs,
  recommendations, and universities.
- The exact compatibility allowlist remains explicit.
- A dead-port finding is initially report-only; removal requires task-level
  parity evidence.

### Error Handling and Logging

- Architecture violations must identify importing file, imported symbol,
  allowed public surface, and rule.
- Reports must omit local absolute paths where possible and never include
  environment values.
- A tooling parse failure must fail the gate, not silently skip a module.

### Tests

- backend/tests/architecture/test_module_boundaries.py
- backend/tests/architecture/test_runtime_surface_inventory.py
- new backend/tests/architecture/test_layer_directions.py
- new backend/tests/architecture/test_public_surface_usage.py
- Run python -m pytest -q backend/tests/architecture from repository root.

### Acceptance Criteria

- Existing 13 architecture tests remain green.
- A deliberate illegal same-module import is caught by a test fixture or
  AST assertion.
- Dead definitions are reported with a consumer count and explicit decision
  rather than removed by broad search-and-delete.
- Compatibility facades have one owner and one migration checkpoint.

### Verification

- Run the architecture suite on a clean checkout.
- Compare the report with Graphify output, treating Graphify inferred edges
  as investigation hints rather than proof.
- Review every new violation against .ai-factory/RULES.md before changing
  source.

## Task MVP-012: Migrate tracer entrypoints and seed names

### Intent

Remove tracer-bullet naming from critical runtime paths while preserving
behavior until canonical parity is proven. The current wrapper chain and
untracked tracer seed make clean deployment and maintenance ambiguous.

### Implementation Steps

1. Before renaming or deleting anything, inventory the complete tracer
   namespace rather than only run_tracer* and tracer.db: scripts, symbols
   such as RawTracerBundle, parser/capture modules, tracer.* logger names,
   tests/fixtures/tracer/raw, docs, and generated or ignored metadata. Give
   every hit an explicit disposition: leave as an intentional current
   contract, migrate, replace, or delete only after equivalence evidence.
   Do not rename/remove a shared raw contract or adapter fixture for naming
   hygiene alone.
2. Extract the real reusable demo/verification functions from
   backend/scripts/run_tracer_demo.py and run_tracer_bullet.py into a
   canonical module or runner owned by current Andromeda paths.
3. Make run_andromeda_ingestion.py and run_andromeda_demo.py call only the
   canonical implementation.
4. Update tests to import the canonical functions first. Keep temporary
   compatibility imports only for one explicit migration cycle.
5. Replace tracer.db seed/fallback names with an intentional local/demo
   database policy. For staging and production images require an explicit
   PostgreSQL URL and fail closed.
6. Remove the compatibility wrappers only after parity tests cover the full
   command surface, result payload, events/campus checks, compare/admission
   checks, and process lifecycle.
7. Update backend/README.md, docs/getting-started.md, docs/postgresql.md,
   docs/deployment.md, and CI references together.
8. Do not delete the untracked proftest-spike or user-generated data in this
   task. Classify it and provide a separate safe archive/cleanup decision.

### Required Interfaces and Contracts

- Preserve CLI flags used by documented fixture/live workflows until the
  replacement is verified.
- Preserve ingestion run IDs, counts, source hashes, and safe failure codes.
- Preserve current source adapter registry and adapter-specific behavior.
- Preserve the documented retired-spike archive as history only.

### Error Handling and Logging

- A runner must report stage, university, mode, run ID, database target
  category, and counts.
- A failure before canonical projection must leave no partial canonical
  projection; a failed audit update must be visible as an operational error.
- Never log raw source bodies, secrets, cookies, or full URLs with credentials.

### Tests

- Before parity:
  backend/tests/scripts/test_tracer_events_runner.py,
  backend/tests/scripts/test_tracer_campus_runner.py,
  backend/tests/integration/test_demo_runner.py,
  backend/tests/integration/test_bmstu_full_ingestion.py,
  backend/tests/integration/test_tracer_bullet.py.
- Add canonical equivalents and a one-cycle wrapper parity test.
- Record the tracer namespace inventory and every disposition in the migration
  checkpoint/release evidence; an executable or test hit without a disposition
  fails the checkpoint.
- Run fixture BMSTU/HSE smoke and Docker image build in an isolated environment.

### Acceptance Criteria

- CI and docs call only canonical Andromeda entrypoints.
- No critical runtime path imports run_tracer_demo or run_tracer_bullet after
  the migration checkpoint.
- Docker build does not depend on an untracked data/tracer.db.
- Every tracer-named executable, fixture, logger, contract, documentation, or
  generated-metadata hit is classified; no unclassified critical-path hit
  remains after the migration checkpoint.
- Old and new runner outputs are equivalent for the frozen baseline, or every
  intentional difference is documented and tested.
- The old wrappers are removed only after the parity suite is green.

### Verification

- Run source/repository rg for run_tracer, tracer.db, tracer.* logger names,
  tracer-named contracts/modules/fixtures, generated metadata, and deprecated
  BMSTU URL references; each remaining hit must be classified as archive,
  compatibility test, intentional current contract, or intentional fallback.
- Build backend image from clean checkout.
- Run Alembic upgrade and fixture smoke using the same database URL for
  entrypoint, API, and runner.

## Task MVP-013: Resolve dead ports and compatibility ownership

### Intent

Reduce maintenance ambiguity without treating abstraction count as a defect.
Unused ports may be intentional future boundaries, but an unowned public
abstraction has no production value and can mislead future changes.

### Implementation Steps

1. For ComparisonSummaryServicePort, CurriculumRepository,
   ProgramRepository, and DisciplineIdentityResolver, record intended
   consumer, absence reason, or replacement.
2. If a port is not needed by a current or committed near-term consumer,
   deprecate it with a dated migration note and remove only after all imports,
   exports, and tests are updated.
3. If it is intended as a public boundary, add a real consumer through the
   correct port and test its contract; do not create a fake consumer only to
   justify the abstraction.
4. Keep identity normalization and repository reader/writer split if they
   represent real domain responsibilities.
5. Add a compatibility registry for the three proftest facades with owner,
   target, reason, and removal condition.

### Required Interfaces and Contracts

- No domain/service code may depend on a concrete infrastructure class.
- Public contract exports remain typed and stable for the migration cycle.
- Removal of a port is an API change within the repository and requires
  affected consumer inventory.

### Error Handling and Logging

- Deprecated compatibility paths emit a bounded warning with the canonical
  replacement, not a stack trace per request.
- No warning may contain user profile values or source contents.

### Tests

- backend/tests/modules/recommendations/test_boundary.py
- backend/tests/modules/proftest/test_boundary.py
- backend/tests/architecture/test_public_surface_usage.py
- Existing import and contract tests for each affected module.

### Acceptance Criteria

- Every remaining public port has a real consumer or explicit documented
  architectural reason.
- Every removed port has parity/regression evidence and no source consumer.
- The compatibility facade list is finite, tested, and has a removal trigger.

### Verification

- Run mypy with strict configuration.
- Run full backend module/contract suites.
- Review the source-only consumer report as part of the release evidence.

## Phase Risks and Mitigations

- **Risk:** deleting wrappers breaks user scripts. **Mitigation:** keep a
  one-cycle adapter with deprecation diagnostics until canonical parity passes.
- **Risk:** choosing the wrong composition root changes object lifetimes.
  **Mitigation:** compare graph outputs and execute API/integration tests before
  removing either root.
- **Risk:** classifying a useful port as dead because only tests use it.
  **Mitigation:** require a documented domain consumer decision and do not use
  raw reference count as the deletion criterion.

## Phase Completion Checklist

1. One composition root owns every runtime service graph.
2. Boundary tests protect module direction, public surfaces, and compatibility.
3. Canonical runner parity is proven before tracer wrappers are removed.
4. Docker clean checkout no longer depends on an untracked tracer database.
5. All remaining historical/spike artifacts are classified without destructive
   cleanup.
