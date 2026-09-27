# Phase 01: Baseline, upstream pins and dependency proof

Plan: [index.md](index.md)
Tasks: 1–3
Depends on: none

## Objective

Freeze the exact remediation baseline, encode the inspected upstream revisions and package roles, and make dependency resolution reproducible before changing any adapter. This phase must not alter canonical data, database schema, or existing typed ports.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|---|---|---|
| `backend/pyproject.toml` | optional groups `evaluation`, `jev` | Current pins are `system-one-adapter==0.1.5` and `typesafe-sdk==0.6.0`; jevcal/jev-align/jevql are absent. |
| `backend/uv.lock` | locked `system-one-adapter`, `typesafe-sdk` packages | Lock must become the reproducibility source for the actual SDK versions. |
| `backend/evals/jev/TOOLS.lock` | jevcal/jev-align tool entries | Commits are recorded but runtime/tool package metadata is incomplete and does not prove invocation. |
| `.ai-factory/plans/feature-jev-ecosystem-stage-2/index.md` | previous Stage 2 plan | Must remain historical; this plan is additive remediation. |
| `AGENTS.md` | context → analysis → plan → implementation → tests → verification | Scope and safety rules require no unrelated changes. |

## Files to Change

| Path | Action | Required change |
|---|---|---|
| `.ai-factory/plans/feature-jev-ecosystem-stage-2-upstream-remediation/index.md` | create | This bundle; no application code. |
| `backend/evals/jev/TOOLS.lock` | modify | Add exact commit, package version, source URL, role, runtime, subdirectory and license for each upstream dependency. |
| `backend/pyproject.toml` | modify | Add only the selected optional dependency groups and update stale official adapter pins. |
| `backend/uv.lock` | regenerate | Resolve exact pins with `uv lock`; no hand-edited lock entries. |
| `backend/jev-tree-bridge/package.json` | verify/modify only if needed | Preserve actual npm `jev-tree@0.1.0` pin and engine requirement. |
| `backend/jev-tree-bridge/package-lock.json` | regenerate only if package metadata changes | Keep npm reproducibility. |
| `backend/tests/` or existing architecture test path | create/modify | Add dependency/provenance assertions without importing optional tools in canonical modules. |

## Task 1: Freeze the remediation baseline and audit manifest

### Intent

Prevent Stage 2 remediation from silently running on another branch, another HEAD, or a dirty worktree. Create a machine-checkable audit manifest for all six upstream sources so later tasks can prove what was actually installed and invoked.

### Implementation Steps

1. Add a repository-local audit manifest in `backend/evals/jev/TOOLS.lock` using the existing file format rather than introducing a second lock system. For each source record URL, exact revision, observed release/package version, runtime (Python/Node), subdirectory if any (`jevql/sdk/python`), role (`RUNTIME_ADAPTER`, `EVAL_TOOL`, or `ISOLATED_OPTIONAL_RUNTIME`), and whether it is permitted in canonical/domain imports.
2. Record `system-one-adapter-python` as eval-only, official TypeSafe SDK as production adapter dependency, jevcal and jev-align as optional evaluation/semantic tooling, jevQL as an optional infrastructure adapter with platform capabilities, and jev-tree as the existing Node optional runtime.
3. Add a verification command/script entry that compares the manifest against `git rev-parse HEAD`, `git branch --show-current`, resolved Python package metadata and npm lock metadata. The command must fail on drift; it must not checkout or repair a branch automatically.
4. Add an audit note to `docs/architecture/jev-rollout.md` only if the implementation phase lands; planning itself does not change docs.

### Required Interfaces and Contracts

- The manifest is provenance metadata, not a runtime feature flag.
- The expected baseline is exact branch `feature/jev-ecosystem-stage-2` and commit `105dacb029a6b38a27aed5c16affb359189d609e`.
- A dependency role must explicitly state whether a package may be imported by `andromeda.modules`; all six upstream integrations remain infrastructure/evaluation only.
- A manifest mismatch produces a non-zero exit and a structured error naming expected and observed values.

### Error Handling and Logging

- Log `INFO` with branch, HEAD, package name and inspected revision when the audit passes.
- Log `ERROR` and exit non-zero for branch/HEAD/package/lock drift.
- Never log API keys, endpoint bearer tokens, cookies, raw user questions or full eval rows.

### Tests

- Add a unit test for manifest parsing and role validation.
- Add a subprocess test that passes on the expected branch/HEAD and fails for a synthetic mismatch.
- Run `uv run pytest backend/tests -q` only for the focused manifest test path, plus the repository’s architecture test command from CI.

### Acceptance Criteria

- The manifest contains all six upstream source revisions listed in `index.md` and distinguishes runtime, eval-only and optional roles.
- A clean checkout at `105dacb` passes the audit; a changed branch or commit fails without changing files.
- No domain/module import is added for an upstream tool.

### Verification

- `git branch --show-current; git rev-parse HEAD; git status --short` — expected branch/HEAD and empty status before implementation.
- `uv run python backend/scripts/verify_jev_tools.py` — expected exit 0 on the pinned environment and explicit drift errors otherwise.
- `git diff --check` — no whitespace errors.

## Task 2: Pin real upstream packages and prove reproducible installation

### Intent

Replace the current stale or missing dependency declarations with reproducible optional groups. The package layout must reflect upstream reality: jevcal is git-only in the inspected source, jev-align depends on GEPA and TypeSafe SDK, jevQL Python SDK lives under a subdirectory and has platform-limited native wheels, and the official TypeSafe SDK is currently stale at 0.6.0.

### Implementation Steps

1. In `backend/pyproject.toml`, update the production Jev optional group to `typesafe-sdk` pinned to upstream `0.7.1` or the exact commit/package resolution selected by the implementation after `uv lock`; preserve the current optional behavior so a canonical ingestion install does not require Jev.
2. Add an evaluation/tool group for jevcal from its pinned git revision `ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f`, and jev-align from `3d997fc76593036655c28d4964de43b55f81fe2c`, including only the dependencies required by their real public APIs. Do not put either tool in the default production group.
3. Add jevQL as an optional infrastructure group using the upstream Python SDK subdirectory/package, not a locally invented module. Declare the platform limitation explicitly in configuration/tests; do not force Windows to install an unavailable embedded native engine.
4. Update `system-one-adapter` to upstream `0.2.0` in the evaluation group. Keep it out of runtime composition.
5. Regenerate `backend/uv.lock` with `uv lock` and verify all direct git URLs, revisions, hashes and transitive dependencies. Do not hand-edit the lock.
6. Preserve `backend/jev-tree-bridge/package.json`/`package-lock.json` as the Node reproducibility boundary and verify `jev-tree@0.1.0`, Node `>=22` and the actual bridge entry point.

### Required Interfaces and Contracts

- `uv sync --locked --extra jev` must install the official SDK only.
- `uv sync --locked --extra evaluation` must install System One, jevcal and jev-align for offline/eval tooling.
- jevQL installation must be an explicit optional capability; runtime config reports embedded unavailable if the native package is not supported by the OS.
- `backend/pyproject.toml` remains the dependency source; `TOOLS.lock` records provenance and role, not a second resolver.

### Error Handling and Logging

- Dependency verification prints package name/version/source revision, not secrets.
- Lock resolution failures stop the task with the exact resolver error; do not silently downgrade to local code.
- Runtime capability checks must log `INFO` for available optional tools and `WARNING` for platform-unavailable optional tools; the warning must include the configured fallback mode.

### Tests

- Run `uv lock --check` and `uv sync --locked --extra jev` in a disposable environment.
- Run `uv sync --locked --extra evaluation` and import only public upstream symbols used by the plan.
- Run `npm ci --ignore-scripts` and the existing bridge test command.
- Add a test that canonical module imports do not require optional Jev packages.

### Acceptance Criteria

- `uv.lock` contains real, exact dependency records for the selected jevcal, jev-align, System One and TypeSafe SDK revisions.
- The official TypeSafe SDK is at least the upstream version required by the inspected jev-align/System One packages and exposes `TypeSafeClient.system_one` and typed answer classes used later.
- The jevQL dependency declaration points to the actual upstream Python SDK package/subdirectory; no `EmbeddedClient` symbol is fabricated.
- Default canonical installation remains runnable without Jev tools.

### Verification

- `uv lock --check` — expected pass.
- `uv run --extra jev python -c "from typesafe_sdk import TypeSafeClient; print(TypeSafeClient.__name__)"` — expected `TypeSafeClient`.
- `uv run --extra evaluation python -c "import jevcal, jev_align, system_one_adapter; print('ok')"` — expected pass.
- `git diff -- backend/pyproject.toml backend/uv.lock backend/evals/jev/TOOLS.lock` — only dependency/provenance changes.

## Task 3: Add a registry-to-tool export contract without duplicating Question Registry ownership

### Intent

Make one deterministic bridge from `QuestionRegistry` to the different upstream input formats. The registry remains authoritative for definition identity, version, instructions, criteria, expected answer shape and fallback; tool adapters own only native serialization and technical options.

### Implementation Steps

1. Extend `backend/src/andromeda/infrastructure/jev/question_registry.py` with an internal/export-facing typed representation that exposes the already-loaded definition fields needed by tools, without changing `QuestionDefinition` public semantics or adding tool-specific fields to the YAML source of truth.
2. Add a small exporter module under `backend/evals/jev/` for native target formats: jevcal question metadata/labels, jev-align task/story metadata, and TypeSafe/System One question objects. Keep each serializer separate so jevcal `target/measure/holdout`, jev-align acquisition/GEPA settings, and System One provider options remain tool-specific.
3. Define an explicit mapping for `intent.v1`, `metric.v1`, `next-action.v1`, `presentation.v1`, and `semantic-feature.v1`. Fail if a registry definition has no mapping or if two registry definitions map to one native id without an explicit alias.
4. Hash the canonical registry projection and include that hash in every exported artifact. The export must preserve definition version and evaluation key, but must not include PII or secrets.

### Required Interfaces and Contracts

- `QuestionRegistryExport` contains `definition_id`, `definition_version`, `instructions`, `criteria`, `options`, `input_schema`, `output_schema`, `fallback`, `timeout_seconds`, `eval_key`, and `registry_hash`.
- A `JevcalQuestionExport` may add native `target`, `measure`, `holdout`, `seed`, and `min_support`; these do not become registry fields.
- A `JevAlignTaskExport` may add dataset/acquisition/GEPA config; it is not used by jevcal.
- A TypeSafe question translator must return actual `Choice`, `Noul`, or `Score` objects (or the exact SDK-supported equivalent) and retain definition metadata outside the model payload.

### Error Handling and Logging

- Unknown definition, unsupported native answer type, schema mismatch or duplicate mapping fails before any external call.
- Log export count, definition IDs, registry hash and target format at `INFO`; log a redacted field-level validation error at `ERROR`.
- Never log instructions containing private data, raw stories, API headers or model responses.

### Tests

- Unit-test every current definition mapping and registry hash stability.
- Test unknown id, duplicate native id, invalid answer schema and PII redaction.
- Snapshot only the schema/keys of native exports, not user text or provider output.

### Acceptance Criteria

- All downstream exporters consume one registry projection and no downstream tool reads YAML independently.
- Tool-specific configuration remains outside the shared registry.
- A registry version change deterministically changes the export hash and invalidates stale calibration/alignment artifacts.

### Verification

- `uv run pytest backend/tests -q -k "question_registry or jev_export"` — expected pass.
- Run the exporter against the current five definitions and compare definition/version/hash fields across jevcal, jev-align and System One outputs.

## Phase Risks and Mitigations

- Risk: optional git dependencies make ordinary development slow or unavailable. Mitigation: separate `jev`, `evaluation` and jevQL extras and keep canonical imports lazy.
- Risk: upstream package APIs drift. Mitigation: exact revisions, public-symbol contract tests and `TOOLS.lock` verification.
- Risk: registry/tool config becomes a hidden second source of truth. Mitigation: registry owns semantic definition; adapters own only native technical settings.

## Phase Completion Checklist

- Tasks 1–3 satisfy their acceptance criteria.
- `uv lock --check`, focused tests and bridge install checks pass.
- No application/domain code, database schema or previous plan bundle was rewritten.
