# Phase 06 — jev-tree: bounded hierarchical entity resolution

Plan: [index.md](index.md)
Tasks: T15–T17
Depends on: Phase 01 / Tasks T02–T03 and existing entity resolver

## Objective

Использовать jev-tree только для масштабной неоднозначности entity/metric resolution после deterministic narrowing. It is an ISOLATED_OPTIONAL_RUNTIME, not a replacement for existing EntityResolver or a second NLP stack.

## Task T15 — Define hierarchical selection port

### Implementation steps

1. Add HierarchicalSelectionPort in the resolution/application boundary with typed SelectionTree, SelectionNode, SelectionRequest, SelectionResult and SelectionFailure.
2. Input contains only already candidate-resolved canonical IDs, sanitized labels/aliases and bounded user intent; no database query or arbitrary code.
3. Port preserves ambiguity and timeout as states; it must not invent a leaf on failure.
4. Policy: deterministic exact/alias/context resolution first; jev-tree is eligible only when candidate count exceeds a measured threshold and ambiguity remains materially unresolved. Normal comparisons, including a set of 20 programs, must never invoke jev-tree.
5. Define max depth, fanout, calls, input bytes and timeout per operation. Store the threshold and reason code in the resolution evidence.

### Tests

- candidate tree construction;
- stable ordering and canonical IDs;
- threshold routing;
- explicit no-call assertion for candidate sets at or below the threshold, including 20-program comparison;
- timeout/empty selection;
- no invented leaf;
- not_found and ambiguous compatibility with existing resolver contracts.

### Acceptance criteria

- existing resolver behavior unchanged under disabled flag;
- hierarchical selection is bounded and explainable;
- selected entity remains a canonical repository ID.

### Dependencies, rollback and risks

Depends on T02–T03 and current resolver. Rollback is deterministic resolver only.

## Task T16 — Add isolated jev-tree adapter

### Implementation steps

1. Create backend/src/andromeda/infrastructure/jev_tree/ adapter around audited createJevTree/parseShape API through a separately deployed Node runtime or internal service only when the threshold gate has selected the capability.
2. Pin Node >=22 and jev-tree version in backend/evals/jev/TOOLS.lock/deployment manifest; do not add Node dependency to Python core.
3. Implement protocol bridge with request ID, candidate hash, definition version, timeout, max calls/depth/fanout and redaction.
4. Validate returned path against candidate IDs; reject arbitrary/new IDs.
5. Return typed failure on provider timeout, model error, max depth/calls or malformed shape.
6. Include no fallback model call inside adapter; fallback belongs to application policy.

### Logging and security

Log candidate count/hash, depth, calls, latency and failure reason. Do not log raw labels in production unless explicitly safe. Reject oversized input and non-allow-listed endpoints.

### Tests

- Node bridge protocol fixture;
- returned path validation;
- candidate tampering;
- max depth/calls;
- timeout and no invented leaf;
- Windows local mode without Node service.

### Acceptance criteria

- jev-tree remains out of Python domain/application imports;
- jev-tree is not called for ordinary small candidate sets;
- adapter cannot select non-canonical entity;
- failure returns ambiguity/unavailable, not a guessed entity.

### Dependencies, rollback and risks

Depends on T15. Rollback is disable flag. Risk: runtime process availability; use deterministic resolver for all normal catalog sizes.

## Task T17 — Integrate hierarchical resolution into QueryFrame without polluting user facts

### Implementation steps

1. Add a resolution strategy field to existing resolver result, not to DecisionContext.
2. Persist only selected canonical entity and resolution evidence in QueryFrame; model candidates remain inferred/model-origin values until user confirmation where ambiguity is material.
3. If jev-tree selects below calibrated threshold, ask clarification with top candidates.
4. Include resolver evidence in AnalyticsResult and ResponseEnvelope metadata.
5. Do not rerun same tree for unchanged candidate hash/definition version within a session revision. A candidate set at or below the deterministic threshold is always resolved without jev-tree.

### Tests

- conversation branch with >255 candidates;
- 20-program comparison proves zero jev-tree calls;
- ambiguous university/program;
- explicit user correction;
- session revision/candidate-hash cache;
- fallback to deterministic alias resolver;
- no redundant question when user supplied exact canonical alias.

### Acceptance criteria

- resolution never silently upgrades model guess to explicit fact;
- user can correct selection;
- downstream analytics use canonical IDs only.

### Dependencies, rollback and risks

Depends on T16 and existing QueryFrame/QuerySession. Rollback keeps current resolver and candidate list.

## Commit checkpoint C5

After T15–T17: commit bounded hierarchical resolution seam and disabled adapter. No production traffic should depend on Node service availability.

## Phase Verification

- pytest backend/tests/modules/conversation backend/tests/modules/entity_resolution -q
- pytest backend/tests/infrastructure/jev_tree -q
- python backend/scripts/check_architecture.py

Expected result: canonical IDs and ambiguity states are preserved, malformed/timeout selection never invents a leaf, and deterministic resolver works without Node.
