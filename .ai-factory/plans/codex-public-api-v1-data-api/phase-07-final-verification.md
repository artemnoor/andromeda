# Phase 7: Final Contract and Repository Verification

Plan: [index.md](index.md)
Tasks: 10
Depends on: Phase 5 / Task 7 and Phase 6 / Tasks 8-9

## Objective

Prove the final backend contract, generated artifacts, frontend, deployment, docs and DATA-API remain valid. Report unavailable external checks honestly and leave all modifications uncommitted.

## Current-Code Evidence

| Path | Symbols / behavior | Why it matters |
|------|--------------------|----------------|
| backend/scripts/export_openapi.py | public-v1 and full export modes | Authoritative generation path for public and full snapshots. |
| openapi.json and frontend-next/openapi.json | checked-in snapshots | They serve different API surfaces and both need drift checks. |
| frontend-next/scripts/generate-api.mjs and drift scripts | generated type/client artifacts | Must be regenerated, not hand-maintained. |
| DATA-API.yaml and scripts/data_api/validate_data_api.py | pinned official validator | Organizer schema and operation references need real validation. |
| scripts/andromeda.py | canonical test targets | Repository verification entry points. |
| git status | includes pre-existing Public API v1 work | Do not discard prior uncommitted deliverables. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| openapi.json and frontend-next/openapi.json | regenerate | Public allowlist and full application schema. |
| frontend-next/src/lib/public-api.generated.ts and frontend-next/src/lib/generated.ts | regenerate | Match respective public/full contracts. |
| DATA-API.yaml and scripts/data_api/* | preserve/verify | Change only for a demonstrated validator mismatch. |
| tests/docs | update only for evidence-backed drift | Confirm operation inventory, command matrix and no bot dependency. |

## Task 10: Run Final Verification

### Intent

Finish with reproducible evidence and an uncommitted, understood diff.

### Implementation Steps

1. Export Public OpenAPI to root openapi.json and full FastAPI OpenAPI to frontend-next/openapi.json.
2. Regenerate public and internal clients using existing npm scripts.
3. Run focused backend tests for Public API v1, analytics source, architecture and migration metadata.
4. Run full backend tests, strict typing, architecture tests, frontend unit tests, lint and production build.
5. Run OpenAPI snapshot/client drift, official DATA-API validator, migration suite, deployment artifact check, documentation audit and API inventory comparison.
6. Run the full and PostgreSQL targets if configured. Report exact skipped gates when a DSN or external service is unavailable; do not report skipped as passing.
7. Run Playwright/production smoke when local browser tooling supports them and record exact outcomes.
8. Search the repository for telegram, Telegram, TELEGRAM_, aiogram and andromeda_telegram. Classify immutable university-source and historical planning matches; verify none is a product/runtime dependency.
9. Run git diff --check; record branch, HEAD, status and changed/deleted files. Confirm current prior Public API v1/DATA-API files remain and no secrets were added.
10. Do not stage, commit, push, create a PR, merge or deploy.

### Required Interfaces and Contracts

- Root OpenAPI contains exactly 58 retained method/path operations.
- Full snapshot retains the complete app including unversioned legacy handlers.
- Generated clients reproduce from checked-in snapshots.
- DATA-API remains schema-valid and maps only supported public operations.
- Alembic head remains unchanged because no database migration is required.

### Error Handling and Logging

- Do not conceal skipped tests or report external system availability as green.
- Do not print secrets while validating deployment configuration.
- Contract, generated-client, or official-validator mismatch blocks a READY result.

### Tests

- git diff --check
- python scripts/andromeda.py fast
- python scripts/andromeda.py backend
- python scripts/andromeda.py frontend
- python scripts/andromeda.py openapi
- python scripts/andromeda.py data-api
- python scripts/andromeda.py migrations
- python scripts/andromeda.py docs
- python scripts/andromeda.py deployment
- python scripts/andromeda.py full
- python scripts/andromeda.py postgres only with ANDROMEDA_POSTGRES_TEST_URL configured
- python scripts/andromeda.py playwright if browser runtime is provisioned

### Acceptance Criteria

- All locally available required checks pass.
- PostgreSQL/browser tests unavailable due environment are explicitly reported as limitations.
- Whole-repository search confirms no active product dependency on the retired transport.
- Worktree remains uncommitted and unpushed.

### Verification

- Run all checks listed above.
- Inspect Git status and changed-file inventory from the active worktree.
- Expected: public/full contract drift is clear, DATA-API validator passes, docs/deployment have no dangling current instructions, final report distinguishes all skips.

## Phase Risks and Mitigations

- Risk: unavailable PostgreSQL service is mistaken for green integration coverage. Mitigation: separate DSN-dependent checks from local gates.
- Risk: broad search finds external or historical occurrences. Mitigation: identify exact paths and distinguish immutable source evidence/plan history from executable product dependencies.

## Phase Completion Checklist

- Task 10 evidence is complete and included in the final report.
- No commit/push occurs.
- Update completion status only in index.md.
