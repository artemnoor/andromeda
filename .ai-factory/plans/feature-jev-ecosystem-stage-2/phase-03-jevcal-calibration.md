# Phase 03 — Jevcal calibration and fail-closed runtime gate

Plan: [index.md](index.md)
Tasks: T06–T08
Depends on: Phase 02 / Tasks T04–T05

## Objective

Подключить jevcal как DEV/EVAL_TOOL для empirical confidence calibration и lock artifacts. Runtime consumes only validated, committed calibration metadata; it never calls jevcal on a user request.

## Task T06 — Export typed decision data to Jevcal

### Implementation steps

1. Create backend/scripts/jevcal_export.py using shared corpus/definition registry.
2. Export only supported Jevcal sample shapes: discrete options for intent/metric/action/presentation; bounded numeric score only where definition explicitly uses score; semantic labels as separate dataset keys.
3. Record definition_id, definition_version, dataset_split, schema_version, source_model and case IDs in sidecar metadata.
4. Pin exact jevcal commit/version in backend/evals/jev/TOOLS.lock and keep local cache/output ignored except reviewed lock/report artifacts.
5. Document that jevcal cache is not source of truth and is not copied to production.

### Tests

- export fixture against local fake corpus;
- unsupported kind rejection;
- split preservation;
- metadata completeness;
- deterministic output hash.

### Acceptance criteria

- exported data is consumable by audited jevcal API/CLI;
- no raw private text is required;
- reproducibility hash and tool identity are recorded.

### Dependencies, rollback and risks

Depends on T04–T05. Rollback deletes exporter and generated local cache. Risk: jevcal API drift; adapter fails with actionable pin mismatch.

## Task T07 — Generate and validate calibration lock artifacts

### Implementation steps

1. Add backend/scripts/jevcal_calibrate.py:
   - run jevcal on train/dev/heldout;
   - compute coverage, ECE, top probability/margin/entropy/confidence where supported;
   - write backend/config/jev/locks/decisions.v1.lock.json;
   - include tool commit, definition version, dataset hash, model identity, threshold, calibration date and quality metrics.
2. Validate lock with JSON Schema in backend/config/jev/schemas/decision-lock.schema.json.
3. Use immutable artifact identity; alias jev-latest is forbidden for production.
4. Reject lock if heldout split is missing, denominator is zero, thresholds are not finite, or required quality metrics fail.
5. Keep deterministic action thresholds separate from semantic feature confidence; do not reuse generic confidence > 0.9.

### Runtime behavior

A missing/invalid/stale lock returns calibration_unavailable and uses deterministic policy. It never silently enables Jev.

### Tests

- lock schema and semantic validation;
- stale definition/model/dataset hash;
- missing heldout/zero denominator;
- deterministic fallback when lock invalid;
- no acceptance based only on top probability.

### Acceptance criteria

- lock is reproducible from pinned corpus/tool;
- runtime proves which artifact enabled a decision;
- quality gates are empirical and per definition.

### Dependencies, rollback and risks

Depends on T06. Rollback keeps gate disabled and removes only untrusted lock. No Alembic migration.

## Task T08 — Add CI calibration and reproducibility gates

### Implementation steps

1. Extend .github/workflows/andromeda-ci.yml with opt-in jev-evaluation job using pinned tools and sanitized corpus.
2. CI runs deterministic replay on relevant changes; real provider calls are manual/protected or scheduled and never required for fork PRs.
3. Check corpus/schema/privacy; lock reproducibility; no uncommitted lock diff; per-definition minimum coverage/quality; no raw prompt/secrets in artifacts; optional packages absent from core import.
4. Publish aggregate metrics and artifact metadata only; never provider payloads.
5. Gate production Jev enablement on passing lock for every definition used in that environment.

### Tests and commands

Use uv run python backend/scripts/check_eval_artifacts.py, uv run python backend/scripts/jevcal_calibrate.py --check, backend tests and architecture checks.

### Acceptance criteria

- bad calibration lock fails CI;
- deterministic backend CI runs without provider keys;
- fork PRs do not require network;
- default production flag remains off.

### Dependencies, rollback and risks

Depends on T07. Rollback disables only optional CI job; existing CI is not weakened.

## Commit checkpoint C2

After T06–T08: commit corpus protocol, exporters, schema-validated lock gate and CI checks. Do not route user traffic to Jev yet.

## Phase Verification

- python backend/scripts/check_eval_artifacts.py
- python backend/scripts/jevcal_calibrate.py --check
- pytest backend/tests/evaluation backend/tests/infrastructure -q

Expected result: the lock is schema-valid/reproducible, heldout checks fail closed, and no provider key is required in ordinary CI.
