# Phase 09 — Rollout gates, security, documentation and handoff

Plan: [index.md](index.md)
Tasks: T25–T26
Depends on: Phases 01–08 and all open-question decisions

## Objective

Закрыть production-readiness только при наличии реальных lock artifacts, provider/runtime ownership, isolated-service deployment и evidence. До этого deterministic path остаётся production behavior.

## Task T25 — Security review and architecture boundary enforcement

### Implementation steps

1. Review external AI boundary against OWASP-style risks: secret storage/redaction; prompt/data leakage; SSRF and user-controlled endpoints; oversized input/cost abuse; retry storms; malicious model output; cache sensitivity; process/service isolation.
2. Add architecture checks that fail if modules import upstream packages; model output reaches raw SQL/repository; Telegram/Web/MAX imports Jev adapters; optional services are required in default test composition.
3. Add rate limits and per-request budgets at API/service boundary using existing infrastructure conventions.
4. Verify no external endpoint comes from user input and provider responses are schema-validated.
5. Review licenses/notices and dependency vulnerabilities in core and isolated images.

### Tests

- backend/tests/architecture/test_jev_boundaries.py;
- API abuse/oversized input tests;
- SSRF endpoint validation;
- model-output fuzz/schema tests;
- dependency/license/security CI.

### Acceptance criteria

- all model output is untrusted;
- security failures degrade closed;
- no secret/private payload in logs/artifacts;
- optional services cannot widen core authority.

### Dependencies, rollback and risks

Depends on all previous phases. Rollback keeps all live flags off and deterministic behavior. Production enablement is blocked on unresolved security findings.

## Task T26 — Update documentation and final implementation/verification gates

### Implementation steps

1. Update README.md, docs/architecture.md, docs/architecture/integration-seams.md, docs/architecture/jev-ecosystem.md, current docs/operations location and API/OpenAPI docs for capability/degraded metadata.
2. Document source facts vs inferred semantic features; MetricRegistry/QuerySpec; QuerySession vs DecisionContext; Question Registry; Jevcal lock generation; Jev-align review; System One baseline; jevQL/jev-tree isolation; shadow mode/rollout; ResponsePlan/MAX seam; troubleshooting/rollback.
3. Add release checklist requiring current corpus/labels and heldout split; valid lock; provider ownership/key rotation; isolated service health; benchmark evidence; shadow quality threshold; rollback test.
4. Run verification in order: git diff --check; backend unit/integration/evaluation/architecture/mypy; Alembic heads/history (no migration expected unless separately approved telemetry need); frontend lint/unit/build/Playwright; Telegram tests; PostgreSQL integration; package/license/security checks.
5. Record final status with changed files, commands and results. Do not mark Jev production-ready if any gate is missing.

### Acceptance criteria

- docs describe actual implemented boundaries, not planned capabilities;
- existing CI is green with optional integrations disabled;
- canonical scenarios pass;
- deterministic fallback is proven;
- production enablement decision is explicit and evidence-backed;
- no code implementation is performed as part of this planning task.

### Dependencies, rollback and risks

Depends on T25 and all previous checkpoints. Rollback is documentation/release gate rollback; runtime remains disabled until future approved rollout.

## Final checkpoint C8

After T25–T26: final review/verification commit only after all previous checkpoints are independently green. If provider, heldout labels or Linux isolated runtime are unavailable, hand off as architecture/evaluation ready, production Jev disabled.

## Phase Verification

- git diff --check
- full backend unit/integration/architecture/mypy suite
- Alembic heads/history check
- frontend lint/unit/build/Playwright
- Telegram tests and PostgreSQL integration
- dependency/license/security audit

Expected result: existing CI remains green with optional integrations disabled, security/boundary checks pass, docs match actual implementation, and unresolved production inputs keep Jev disabled.
