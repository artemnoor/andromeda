# Phase 04 — Jev-align: reviewed semantic enrichment loop

Plan: [index.md](index.md)
Tasks: T09–T11
Depends on: Phase 03 / Tasks T06–T08

## Objective

Использовать jev-align как DEV/EVAL_TOOL для active-learning/review workflow semantic features. It must improve versioned classifier artifacts without making AI-derived values source facts or adding a runtime dependency.

## Task T09 — Export uncertain semantic items to a review queue

### Implementation steps

1. Extend backend/scripts/rebuild_semantics.py with --export-review-queue reading persisted semantic values and provenance.
2. Export only items with deterministic disagreement, low calibrated confidence, missing coverage or changed taxonomy definition.
3. Export to backend/evals/jev-align/queues/: canonical IDs; sanitized discipline context; current rule output; candidate feature values; source hash; semantic version; classifier version; review reason.
4. Never include student/profile/auth data or source credentials.
5. Generate stable row IDs from canonical ID + semantic version + source hash.

### Tests

- backend/tests/modules/semantic/test_review_queue.py;
- stable IDs;
- no missing-as-zero conversion;
- queue excludes already reviewed rows;
- provenance fields are complete.

### Acceptance criteria

- review queue is retryable/idempotent;
- every row links to canonical item and semantic version;
- no automatic promotion occurs.

### Dependencies, rollback and risks

Depends on T05–T08 and existing SemanticEnrichmentService. Rollback keeps RuleBasedSemanticClassifier active.

## Task T10 — Integrate jev-align review/export/import workflow

### Implementation steps

1. Add backend/scripts/jev_align_workflow.py around audited jev-align CLI/API, pinned in backend/evals/jev/TOOLS.lock.
2. Support explicit export, review, accept, reject, rewind; do not auto-accept GEPA proposals.
3. Store review manifest with reviewer/action/timestamp/tool version and proposal hash. Private registry publishing is forbidden.
4. Import only accepted mappings into versioned backend/config/semantic/feature-definitions.vN.yaml or equivalent canonical rule artifact.
5. Keep generated artifact separate from official source facts; mark classification_method=manual or jev and review_status=approved.
6. Require a diff report before changing active semantic classifier version.

### Failure behavior and logging

Corrupt proposal, unknown feature or missing evidence is rejected. Log queue ID, proposal hash, decision and artifact version, not raw rows.

### Tests

- fake jev-align workflow;
- accept/reject/rewind state machine;
- duplicate proposal and stale source hash;
- unknown feature rejection;
- approved artifact round-trip through RuleBasedSemanticClassifier.

### Acceptance criteria

- no unreviewed model output reaches active semantic values;
- classifier artifact is reproducible and versioned;
- previous artifact can be restored.

### Dependencies, rollback and risks

Depends on T09. Rollback activates previous semantic artifact; canonical ingestion remains unaffected.

## Task T11 — Add reviewed semantic artifact compatibility to enrichment

### Implementation steps

1. Update backend/src/andromeda/modules/semantic/services/classifier.py and enrichment.py to load a versioned reviewed mapping through an existing/new SemanticClassifierPort implementation.
2. Preserve precedence: official/canonical facts → manual reviewed mapping → deterministic rule → optional Jev candidate → unavailable.
3. Persist classification_method, classifier_version, semantic_version, confidence, review status and source hash for every derived value.
4. Rebuild only changed items/program projections; reuse existing idempotency and changed-only behavior.
5. Add dry-run and rollback artifact selection to backend/scripts/rebuild_semantics.py.

### Tests

- precedence and provenance;
- stale artifact rejection;
- rebuild unchanged count;
- projection refresh for affected programs only;
- canonical ingestion works while artifact/provider unavailable.

### Acceptance criteria

- semantic enrichments remain auditable;
- Jev-align can improve mappings without runtime Jev;
- no source-backed value is overwritten by inferred semantics;
- missing stays UNAVAILABLE, not zero.

### Dependencies, rollback and risks

Depends on T10. Rollback uses previous artifact and deterministic rules. Risk: semantic version change invalidates metrics; trigger explicit projection rebuild and cache invalidation.

## Commit checkpoint C3

After T09–T11: commit reviewed semantic workflow and enrichment compatibility. Keep Jev calls out of request-time classification by default.

## Phase Verification

- pytest backend/tests/modules/semantic -q
- python backend/scripts/rebuild_semantics.py --help
- python backend/scripts/check_eval_artifacts.py

Expected result: accepted review artifacts round-trip through enrichment, rejected/stale proposals cannot activate, and canonical ingestion remains provider-independent.
