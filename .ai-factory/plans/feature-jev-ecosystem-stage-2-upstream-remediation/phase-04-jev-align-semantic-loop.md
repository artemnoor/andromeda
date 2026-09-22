# Phase 04: Real jev-align semantic loop

Plan: [index.md](index.md)
Tasks: 10–11
Depends on: Phase 02 / Tasks 2–5; Phase 03 / Task 9

## Objective

Use upstream jev-align for uncertainty selection, human labels and GEPA optimization while preserving Andromeda’s existing human-review/publish boundary. No AI output may automatically mutate the semantic layer.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|---|---|---|
| `backend/scripts/jev_align_workflow.py` | export/review/publish CLI | Current workflow reimplements the lifecycle and does not invoke upstream `ClimbSession`/GEPA. |
| `backend/src/andromeda/modules/semantic` and related review services | `SemanticReviewWorkflow`, `SemanticMappingProposal` | Existing domain owner for proposal approval, semantic version and rebuild must remain authoritative. |
| upstream jev-align | `RunStore`, `ClimbSession.acquire`, `add_label`, `optimize`, `decide`, `build_function_artifact` | Upstream owns uncertainty selection/GEPA/pending proposal; Andromeda owns canonical approval/publish. |

## Files to Change

| Path | Action | Required change |
|---|---|---|
| `backend/scripts/jev_align_workflow.py` | replace orchestration | Thin driver around real upstream classes and existing Andromeda review API. |
| `backend/src/andromeda/infrastructure/jev_align/` | create or modify | Optional adapter for pinned upstream package and typed artifact mapping. |
| `backend/src/andromeda/modules/semantic/...` | modify only existing review integration point | Consume accepted proposal/version; no new semantic domain layer. |
| `.gitignore` | modify if required | Ignore `.jev-align/` run state and private artifacts. |
| `backend/tests/infrastructure/jev_align/` and semantic tests | create/modify | Upstream contract, human gate, reject/rewind and rebuild tests. |

## Task 10: Replace local uncertainty/optimization logic with upstream jev-align ClimbSession

### Intent

Connect the existing sanitized semantic dataset to the actual jev-align active-learning loop. The implementation must not implement its own uncertainty score, random audit selection or GEPA optimizer.

### Implementation Steps

1. Add a thin driver/adapter under `backend/src/andromeda/infrastructure/jev_align/` that imports pinned upstream `Story`, `RunState`, `TaskSpec`, `BackendConfig`, `RunStore`, `ClimbSession`, `create_backend` and `build_function_artifact` only from their actual public/source paths at the pinned revision.
2. Map canonical discipline/semantic review rows into sanitized jev-align stories with stable case IDs, current semantic definition/version, source provenance reference and allowed review fields. Do not pass private profiles, secrets or raw unrestricted curriculum text.
3. Use `ClimbSession.acquire()` for uncertainty/audit batch selection; persist labels through `add_label()`/`RunStore`; invoke `optimize()` to let upstream GEPA create a pending candidate/report. Andromeda must not calculate uncertainty or call GEPA directly.
4. Store upstream run directory/state under a configured `.jev-align` artifact directory outside source control. Include registry/semantic version and dataset hash in the run metadata so a candidate cannot be applied to a different dataset.
5. Keep provider/backend configuration tool-specific and separate from Question Registry. Use a fake backend in offline tests; real provider execution is opt-in and bounded by timeout/cost settings.

### Required Interfaces and Contracts

- `JevAlignRunRequest`: dataset hash, semantic definition/version, batch size, round, acquisition config, backend/model reference and output directory.
- `JevAlignProposal`: upstream run ID, candidate/report path, current semantic version, dataset hash, changed examples/metrics summary and status `pending`.
- A proposal is not a semantic value and cannot be read by AnalyticsEngine until Task 11 publishes it.
- If upstream symbols or artifact schema differ from the pin, fail the adapter contract test and stop; do not substitute a local algorithm.

### Error Handling and Logging

- Log `INFO` run ID, round, dataset hash, number of selected cases and proposal status.
- Log `WARNING` provider unavailable or no candidate produced; log `ERROR` dataset hash/version mismatch, malformed upstream artifact or pending-state conflict.
- Never log story content, labels, prompts, provider keys or full GEPA traces.

### Tests

- Contract-test imports and calls against pinned `ClimbSession` with a fake evaluation backend.
- Test `acquire` receives uncertain/audit rows from upstream and that Andromeda does not reorder them with a local score.
- Test `optimize` leaves a pending candidate and that `build_function_artifact` is rejected while a proposal is pending.
- Test dataset/semantic version mismatch and private-field redaction.

### Acceptance Criteria

- Upstream jev-align performs acquisition and GEPA optimization.
- Andromeda code is a driver/serializer/review adapter, not a second active-learning implementation.
- A pending upstream candidate cannot change production semantic mappings.

### Verification

- `uv run --extra evaluation pytest backend/tests/infrastructure/jev_align -q` — expected pass with fake backend.
- Inspect `.jev-align` run artifact — expected upstream run metadata, dataset hash and no secrets/private fields.
- `rg "uncertainty|optimize_candidate|GEPA" backend/scripts/jev_align_workflow.py backend/src/andromeda/infrastructure/jev_align` — matches must be upstream calls, not local algorithms.

## Task 11: Keep human approval as the semantic publish gate and version controlled rebuild

### Intent

Preserve the strong existing proposal → human → new version → rebuild workflow while consuming upstream proposal/artifact data. Reject, rewind and stale proposals must be safe and auditable.

### Implementation Steps

1. Adapt `backend/scripts/jev_align_workflow.py` review/publish commands to read `JevAlignProposal` and call the existing `SemanticReviewWorkflow`/`SemanticMappingProposal` owner rather than writing semantic rows directly.
2. On explicit human `accept`, verify run ID, candidate hash, dataset hash, current semantic version and review identity; create a new semantic definition/version and enqueue/execute the existing controlled rebuild path only after those checks.
3. On `reject` or `rewind`, call upstream `ClimbSession.decide("reject")`/run-store operation as appropriate, mark the proposal non-publishable and leave current semantic values untouched.
4. Prevent `build_function_artifact`/publication while upstream session has a pending proposal or while an Andromeda review is unresolved. Preserve idempotency by proposal ID and candidate hash.
5. Add safe audit events for proposal created, labels added, accepted, rejected, stale, rebuild started and rebuild completed. Do not add an autonomous semantic update cron.

### Required Interfaces and Contracts

- Publication requires an explicit human decision; no `jev-align` result is a source fact.
- New semantic version must reference upstream run/candidate hash, reviewer action, registry hash, source dataset hash and classifier/model version.
- Rebuild is scoped to affected disciplines/items and uses existing materialization/rebuild services; unrelated programs are not recalculated.

### Error Handling and Logging

- `409`/typed conflict for duplicate decision, stale candidate or version race; no partial semantic publish.
- `WARNING` for rejected proposal; `ERROR` for failed rebuild with prior semantic version retained.
- Log IDs/hashes/status/actor role, never labels or raw semantic text.

### Tests

- Test accept, reject, rewind, duplicate accept, stale dataset, stale version, candidate-hash mismatch and rebuild failure rollback.
- Test accepted proposal creates exactly one new semantic version and does not modify the previous version.
- Test no AnalyticsEngine query sees a pending candidate.

### Acceptance Criteria

- Human approval remains mandatory and visible in the audit trail.
- New semantic values are versioned and rebuildable; rejected/failed proposals do not mutate active semantics.
- Existing Semantic Layer contracts remain compatible.

### Verification

- Run focused semantic review/rebuild tests and inspect version/provenance records.
- Execute a fake accept/reject round twice — first accept is idempotent; second returns a safe conflict without duplicate version.

## Phase Risks and Mitigations

- Risk: upstream internal module paths change. Mitigation: exact pin, import contract tests, and one adapter file containing all upstream imports.
- Risk: GEPA candidate is treated as truth. Mitigation: pending status, human gate and version/hash checks before rebuild.
- Risk: private data enters run artifacts. Mitigation: sanitizer, artifact inspection tests and `.gitignore`.

## Phase Completion Checklist

- Tasks 10–11 satisfy acceptance criteria.
- Upstream jev-align is invoked for active-learning behavior.
- No semantic production value changes without explicit human approval and controlled rebuild.
