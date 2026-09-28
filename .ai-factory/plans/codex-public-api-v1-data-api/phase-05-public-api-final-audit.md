# Phase 5: Final Public API Operation Audit

Plan: [index.md](index.md)
Tasks: 6-7
Depends on: Phase 1-4 / Tasks 1-5

## Objective

Review every existing Public API operation using route definitions, call sites and user-facing UI ownership. Exclude only operations that are internal or explicitly deprecated from the stable client contract; keep their full FastAPI operations for compatibility.

## Current-Code Evidence

| Path | Symbols / behavior | Why it matters |
|------|--------------------|----------------|
| backend/src/andromeda/api/public_api_v1.py | PUBLIC_API_V1_OPERATIONS, project_public_api_v1_openapi | Exact current 61-operation manifest controls aliases and projection. |
| backend/tests/api/test_public_api_v1.py | exact allowlist, OpenAPI projection, full schema | Extend tests to assert exclusions while preserving source handlers. |
| backend/src/andromeda/api/routes/proftest.py | deprecated handlers and version-pinned sessions | Compatibility routes should remain in full FastAPI while excluded from v1. |
| frontend-next/src/app/og/analytics/route.tsx | server-side fetch to the v1 analytics query | Confirms the query operation is actively used through the versioned surface. |
| frontend-next/src/features/proftest/proftest-page.tsx | session API call sites | Confirms the canonical Web assessment workflow. |
| frontend-next/src/lib/api.ts and frontend features | auth, decision, event, campus and other clients | Evidence for retaining active user-facing endpoint families. |
| docs/api.md and openapi.json | published inventory and canonical contract | Must agree exactly after allowlist changes. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| backend/src/andromeda/api/public_api_v1.py | modify | Remove only three deprecated proftest tuples. |
| backend/tests/api/test_public_api_v1.py | modify | Assert three aliases are absent while corresponding full API paths remain and analytics query remains public. |
| docs/api.md | modify | Publish every retained method/path and concise exclusion reasons. |
| openapi.json | regenerate | Re-export canonical public snapshot after code changes. |
| frontend-next/src/lib/public-api.generated.ts | regenerate | Remove excluded operations through the existing generator. |

## Task 6: Audit the 61 Public Operations

### Intent

Avoid arbitrary deletion by checking endpoint consumers and intended client stability.

### Implementation Steps

1. Enumerate every method/path from PUBLIC_API_V1_OPERATIONS and map each to exactly one FastAPI route.
2. Record all current methods by workflow: health; catalog; admissions/benefits; assistant/comparison/decision; assessment/profile/recommendations; events/campus/taxonomy; account.
3. Check frontend call sites and route declarations for three deprecated proftest compatibility operations. Verify analytics query is a typed deterministic QuerySpec API used by the signed server-side OG analytics renderer through /api/v1.
4. Confirm Web uses version-pinned proftest sessions; generic events/campus, auth, decision, analytics query, admission benefits, recommendations, profile and user telemetry are active client capabilities.
5. Confirm every other operation is stable user API and internal/admin routes remain outside v1.

### Required Interfaces and Contracts

- Current inventory: 61 operations.
- Explicit exclusions: GET /proftest/questions; POST /proftest/preview; POST /proftest/results.
- Retained inventory: 58 operations.
- POST /analytics/query remains public because it is a typed, bounded, deterministic user analytics operation and an existing server-side renderer uses it through /api/v1.
- Source unversioned routes, schemas and behavior remain unchanged.

### Error Handling and Logging

- A route collision or missing route fails through existing allowlist validation.
- Do not suppress a missing operation by widening the public projection.
- Runtime logging does not change.

### Tests

- Analysis only: inspect the public API test, route definitions and UI call sites.
- Do not manually alter generated artifacts during inventory.

### Acceptance Criteria

- Every one of the 61 operations has one disposition and a route source.
- The three exclusions each have a deprecation/compatibility reason.
- No admin/review/ops route is added to the public surface.

### Verification

- rg -n 'PUBLIC_API_V1_OPERATIONS' backend/src backend/tests
- rg -n 'proftest/(questions|preview|results)|/analytics/query' frontend-next/src
- Expected: the proftest page uses sessions; the server-side OG route calls the typed analytics query through v1.

## Task 7: Publish the Supported Client Contract

### Intent

Keep compatibility support in the existing full FastAPI app while declaring only stable client-facing paths in Public API v1.

### Implementation Steps

1. Remove the three deprecated proftest method/path pairs from PUBLIC_API_V1_OPERATIONS. Do not alter source route decorators, schemas, services or router registration.
2. Extend the public API test to assert the versioned analytics query remains available and the three deprecated proftest aliases do not exist.
3. Assert the full FastAPI OpenAPI document still contains the three unversioned source operations.
4. Update docs/api.md with a complete operation list grouped by user workflow and labeled by method.
5. Explain that analytics query is a stable typed client operation and the old assessment routes are deprecated unversioned compatibility only.
6. Preserve root public OpenAPI generation, full-app snapshot, DATA-API checks and authentication/session contracts.

### Required Interfaces and Contracts

- Root public OpenAPI and public generated client contain exactly the 58 retained operations.
- frontend-next/openapi.json remains the full FastAPI contract.
- No actual FastAPI endpoint is removed.
- DATA-API operations retain their current request/response mapping.

### Error Handling and Logging

- Alias registration still requires each retained source route exactly once.
- Legacy route errors and response behavior remain unchanged.
- Error envelope and authentication behavior do not change.

### Tests

- backend/tests/api/test_public_api_v1.py: projection-negative and full schema positive assertions.
- Run python -m pytest -q tests/api/test_public_api_v1.py from backend.

### Acceptance Criteria

- Manifest and projection contain 58 operations.
- Root OpenAPI retains the analytics query and contains no three deprecated versioned aliases.
- Full FastAPI OpenAPI retains all three legacy source routes.
- Documented inventory exactly matches public OpenAPI methods and paths.

### Verification

- python -m pytest -q tests/api/test_public_api_v1.py
- python scripts/andromeda.py openapi
- Expected: public contract matches allowlist and generated client; full snapshot retains legacy endpoints.

## Phase Risks and Mitigations

- Risk: compatibility path is inadvertently removed. Mitigation: test positive presence in full-app OpenAPI and do not edit source routes.
- Risk: generated list drifts from docs. Mitigation: compare the final operation count and sorted method/path set.

## Phase Completion Checklist

- Task 6 and Task 7 acceptance criteria pass.
- Update completion status only in index.md.
