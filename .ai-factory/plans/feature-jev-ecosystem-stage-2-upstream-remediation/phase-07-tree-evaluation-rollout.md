# Phase 07: jev-tree proof, integrated evaluation and rollout

Plan: [index.md](index.md)
Tasks: 16–19
Depends on: Phases 01–06 as specified per task

## Objective

Finish the remediation with a narrow jev-tree proof, one comparable evaluation harness, CI/architecture gates, documentation and rollback verification. Preserve existing flows and make no claim stronger than the available corpus supports.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|---|---|---|
| `backend/src/andromeda/modules/entity_resolution/services/hierarchical.py` | deterministic narrowing, `_threshold=255`, candidate hash | Existing behavior already avoids provider calls for small sets and validates canonical IDs. |
| `backend/src/andromeda/infrastructure/jev_tree/transport.py` | Node bridge invocation | Existing bridge is the actual package boundary. |
| `backend/jev-tree-bridge/src/index.mjs` | `createJevTree` | Must retain upstream package call and add provenance/contract smoke only. |
| `backend/evals/jev/system_one_evaluator.py` | eval observations | Final harness compares deterministic, official Jev and System One without mixing production roles. |
| `.github/workflows/andromeda-ci.yml` | backend/frontend/architecture jobs | Add offline and optional external gates without requiring paid credentials for ordinary CI. |

## Files to Change

| Path | Action | Required change |
|---|---|---|
| `backend/src/andromeda/infrastructure/jev_tree/{adapter,transport,config}.py` | modify | Package/runtime provenance, threshold and safe telemetry. |
| `backend/jev-tree-bridge/{package.json,package-lock.json,src/index.mjs}` | verify/modify | Exact upstream package/runtime contract and bounded errors. |
| `backend/tests/entity_resolution/` and bridge tests | create/modify | Small/large candidate behavior and canonical hash validation. |
| `backend/evals/jev/` | modify | Integrated source-backed evaluation/report schema. |
| `.github/workflows/andromeda-ci.yml`, `docs/testing.md` | modify | Offline gates, optional secret smoke and command documentation. |
| `docs/architecture/integration-seams.md`, `docs/architecture/jev-rollout.md`, `backend/evals/jev/README.md` | modify | Actual upstream roles, rollout/fallback and evidence limitations. |

## Task 16: Wire jev-tree into EntityResolver and prove large-candidate-only invocation

### Intent

Preserve the already-correct jev-tree architecture, wire the existing adapter into the active EntityResolver composition, and prove the user’s specific requirement: deterministic narrowing first, provider only for genuinely large candidate sets, never for a small set such as 20 programs.

### Implementation Steps

1. Add package/version/runtime metadata to the existing Node bridge response or adapter capability report using `jev-tree@0.1.0`, Node `>=22` and the locked package hash; do not alter `createJevTree` selection semantics.
2. Keep `HierarchicalResolutionService` deterministic path for `len(candidates) <= candidate_threshold` and provider path only above threshold. Ensure threshold is configurable but bounded and that the candidate hash is calculated after deterministic narrowing.
3. Wire the existing `JevTreeAdapter` into the active `EntityResolver`/composition-root path behind `JEV_TREE_ENABLED`. Preserve deterministic resolver construction when disabled, and prove the application/entity-resolution vertical slice reaches the adapter when enabled.
4. Preserve adapter validation that provider result includes the expected candidate hash and canonical candidate ID; an unknown ID, stale hash, unavailable provider or timeout returns deterministic candidates/unresolved state.
5. Add an upstream bridge smoke test and a 20-candidate test that spies on transport and proves zero calls. Add a `threshold+1` candidate composition test proving the enabled EntityResolver invokes upstream jev-tree exactly through the adapter and maps the stable canonical result.

### Required Interfaces and Contracts

- Existing entity resolver ports and result contracts do not change.
- The active EntityResolver composition has exactly one optional `JevTreeAdapter` binding controlled by `JEV_TREE_ENABLED`; adapter-only tests are insufficient for acceptance.
- Provider request contains candidate hash, bounded candidate labels/IDs, question and tree config; no full catalog/private profile.
- Provider selection reason is `deterministic_small_set` or `jev_tree_large_set`.

### Error Handling and Logging

- `INFO`: candidate count, threshold, route, package/runtime and latency.
- `WARNING`: tree unavailable/timeout/invalid result and deterministic fallback.
- Never log all candidate labels, user text, API keys or raw model output.

### Tests

- 20 candidates: zero transport calls.
- `threshold+1` candidates: one actual bridge call, canonical hash verified.
- Composition-root/entity-resolution vertical slice: enabled flag reaches `JevTreeAdapter`; disabled flag bypasses it.
- Invalid hash/ID and no-result tests.
- Node `npm ci` and bridge smoke with actual installed `jev-tree`.

### Acceptance Criteria

- The adapter uses actual upstream jev-tree package and has provenance metadata.
- The production EntityResolver can actually reach `JevTreeAdapter` when `JEV_TREE_ENABLED=true`.
- No provider call occurs for 20 programs or any set at/below threshold.
- Existing entity resolution behavior remains compatible.

### Verification

- `npm ci --ignore-scripts` and bridge tests — expected pass.
- `uv run pytest backend/tests -q -k "hierarchical or jev_tree or entity_resolver_composition"` — expected small-set zero-call, enabled composition and large-set bounded-call assertions.

## Task 17: Run one source-backed evaluation harness through deterministic, Jev and System One paths

### Intent

Provide comparable evidence for control questions without inventing production calibration claims. All calibration metrics must come from upstream jevcal; this task only orchestrates and reports.

### Implementation Steps

1. Extend the existing eval runner under `backend/evals/jev/` to run the same registry-versioned corpus through deterministic policy, official TypeSafe client (shadow/fake or explicitly external), and System One Adapter benchmark.
2. Feed observations to upstream jevcal report/measure/check commands from Task 6. Store a report with per-definition sample count, heldout count, accepted/rejected status, coverage, latency, retries, usage and fallback reasons.
3. Add an optional jevQL predicate benchmark using materialized-first and unmaterialized routes; record candidate counts and budget/cache outcomes without evaluating private production rows in fixtures.
4. Add a shadow comparison event schema for deterministic vs Jev intent/metric/next-action/presentation decisions. It must not update user state or response in shadow mode.
5. Mark any result with insufficient support as `not_calibrated`/`fixture_only`; do not print “production accuracy” or ECE claims for the current corpus.

### Required Interfaces and Contracts

- Evaluation report references registry hash, dataset hash, upstream tool revisions, model versions and code commit.
- One case has one stable ID and one expected label; missing/error is a separate outcome, not false.
- Report fields are safe and aggregate; raw provider/model text is excluded.

### Error Handling and Logging

- Log batch-level progress and aggregate counts at `INFO`; per-case failures at `DEBUG` by hashed ID.
- `WARNING` for insufficient corpus/provider unavailable; `ERROR` for schema/provenance mismatch.
- No raw prompts, profiles, tokens or provider bodies.

### Tests

- Golden fixture report schema and deterministic reproducibility.
- Test current corpus is explicitly not production-calibrated.
- Test Jev unavailable still produces deterministic report/fallback.
- Test report refuses mixed registry/dataset/model versions.

### Acceptance Criteria

- Deterministic, official Jev and System One results are comparable on the same case set.
- Metrics are sourced from upstream jevcal or labeled as unavailable; no local calibration math is introduced.
- Evaluation is isolated from runtime user-facing state.

### Verification

- Run the offline harness with fixture corpus — expected safe report marked `fixture_only`.
- Run the report validator — expected failure for mixed hashes and pass for a coherent artifact.

## Task 18: Add CI gates, optional external smoke checks and architecture boundary checks

### Intent

Make upstream integration regressions visible while keeping ordinary CI offline, reproducible and free of paid provider secrets.

### Implementation Steps

1. Update `.github/workflows/andromeda-ci.yml` with an offline job that runs locked dependency checks, focused Jev/jevcal/jev-align/jevQL tests, Node bridge tests, architecture boundary checks and existing regression tests.
2. Add an opt-in external smoke job gated by repository secrets/environment (official TypeSafe endpoint/model only). It must be non-required or explicitly environment-protected, use a tiny sanitized case, enforce timeout/cost limits and never publish calibration/semantic values.
3. Add CI checks that fixture lock cannot set production-ready status, `jevcal check` is run on generated fixture artifacts, package versions match `TOOLS.lock`, no domain imports optional tools, and no raw SQL/model-generated query path exists.
4. Run OpenAPI/contract checks only if existing API files are touched; this remediation should not add endpoints or alter public API contracts.
5. Preserve all existing backend/frontend/architecture jobs and fail on underlying errors; do not relax a check to hide a dependency failure.

### Required Interfaces and Contracts

- Offline CI never needs API keys, private endpoints, production corpus or native jevQL engine unavailable on the runner.
- External smoke is explicitly labeled `optional/external`, emits no secret values, and cannot mark calibration production-ready.
- CI artifact reports contain package/commit/test status, not raw prompts/responses.

### Error Handling and Logging

- CI logs may show package names, versions, test names and safe error codes.
- Mask all configured secrets; do not echo environment values or command lines containing tokens.
- External smoke timeout/failure is reported as degraded smoke, not converted into a passing production gate.

### Tests

- Run exact CI commands locally before committing: backend focused tests, full relevant pytest, mypy/architecture checks, `uv lock --check`, npm bridge checks, frontend unchanged regression command.
- Add a CI YAML validation/test if repository convention supports it.

### Acceptance Criteria

- Offline CI proves all integrations with fakes/fixtures and no external secrets.
- Optional external smoke tests the official production SDK path without enabling it.
- Existing CI remains at least as strict as before.

### Verification

- `git diff -- .github/workflows/andromeda-ci.yml` — expected additive gates only.
- Run the same commands listed in the workflow locally and record exit codes in the implementation handoff.

## Task 19: Update integration documentation and perform final rollout/rollback verification

### Intent

Make documentation match actual code only after implementation, then prove that operators can enable, shadow, degrade and roll back the integrations without schema or canonical-data changes.

### Implementation Steps

1. Update `docs/architecture/integration-seams.md` with actual upstream revisions/roles, registry ownership, official TypeSafe production path, System One eval-only boundary, real jevcal/jev-align calls, jevQL platform matrix and jev-tree threshold behavior.
2. Update `docs/architecture/jev-rollout.md` with fixture → shadow → production-ready transitions, per-definition calibration gate, stale-lock/model mismatch failure, provider fallback and rollback to deterministic policy.
3. Update `backend/evals/jev/README.md` with fixture vs production corpus, upstream commands, privacy rules, minimum-support configuration source and no-claim policy.
4. Update `docs/testing.md` with exact offline/external smoke/bridge/calibration commands and expected degraded results. Do not document experimental semantics as official facts.
5. Execute final verification from the clean branch: status/diff check, tests/lint/type/architecture, dependency lock checks, artifact provenance, no Alembic revision changes, and rollback by disabling Jev/using deterministic mode.

### Required Interfaces and Contracts

- Documentation must name exact current revisions from `TOOLS.lock`, not floating `main`.
- Rollback means configuration disables Jev/jevQL/tree optional providers and deterministic existing flows continue; it does not delete canonical data, semantic versions or migrations.
- Docs must state that source facts, inferred semantics, user choices, QuerySession state and telemetry remain separate.

### Error Handling and Logging

- Final verification records command, exit code and safe artifact hash.
- Any failure blocks handoff and is reported with path/command; do not mark the plan complete.
- No credentials or private corpus content enters docs or reports.

### Tests

- Full relevant regression suite from `.github/workflows/andromeda-ci.yml`.
- `git diff --check`, dependency lock checks, architecture checks, focused upstream contract tests and optional smoke where credentials are explicitly available.
- Verify no Alembic files changed and no public contracts changed unexpectedly.

### Acceptance Criteria

- Docs accurately describe real upstream usage and failure modes.
- Production can be rolled back to deterministic behavior by configuration without code/data deletion.
- The branch is clean except for the intended implementation commit(s), with all tests and gates passing.

### Verification

- `git status --short`, `git diff --check` — expected clean/no whitespace errors after commit.
- `git diff --name-only <baseline>...HEAD | Select-String "alembic|DecisionModelPort|QuestionRegistry|QuerySession|ResponsePlan"` — expected no unintended schema/public-contract rewrites.
- Run the full CI-equivalent command set and attach only safe aggregate results to the handoff.

## Phase Risks and Mitigations

- Risk: optional smoke secrets make CI non-reproducible. Mitigation: offline required gate and protected opt-in external job.
- Risk: docs drift from actual package versions. Mitigation: generate/verify version table from `TOOLS.lock` during final check.
- Risk: a rollout changes existing MVP flow. Mitigation: deterministic mode comparison and explicit rollback verification.

## Phase Completion Checklist

- Tasks 16–19 satisfy acceptance criteria.
- Full regression and architecture checks pass.
- Documentation and rollback evidence are complete; implementation can be handed off without hidden upstream assumptions.
