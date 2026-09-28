# Phase 2: Canonical Public OpenAPI and generated client

Plan: [index.md](index.md)
Tasks: 2-3
Depends on: Phase 1 / Task 1

## Objective

Export one canonical root OpenAPI document containing only `/api/v1` operations, generate a typed client from it, retain separate generated contracts for the existing internal/admin frontend, and make backend/spec/client drift fail CI.

## Current-Code Evidence

| Path | Symbols / evidence | Why it matters |
|------|-------------------|----------------|
| `backend/scripts/export_openapi.py` | `main` | Currently writes `create_app().openapi()` only, which contains all operations. |
| `backend/src/andromeda/api/main.py` | `AndromedaFastAPI.openapi` | Must continue serving the full docs/OpenAPI for existing internal operations. |
| `frontend-next/openapi.json` | generated full application snapshot | Existing frontend client depends on internal/admin operation types; do not replace it with Public-only OpenAPI. |
| `frontend-next/scripts/generate-api.mjs` | `openapi-typescript` invocation | Currently writes one full `generated.ts`. |
| `frontend-next/scripts/check-api-drift.mjs` | generated type comparison | Currently checks only one generated file and does not verify the checked-in OpenAPI snapshot. |
| `.github/workflows/andromeda-ci.yml` | `frontend-next` job | Exports full OpenAPI to a temporary path and checks generated TypeScript. |
| `scripts/andromeda.py` | `_openapi` gate | Local gate currently checks the same full-schema client path. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| `backend/src/andromeda/api/public_api_v1.py` | modify | Add deterministic public document projection from the app's full schema; select only `/api/v1` operations and rewrite title/version metadata. |
| `backend/scripts/export_openapi.py` | modify | Add `--surface full|public-v1` while preserving default full export; emit deterministic JSON to requested path. |
| `openapi.json` | create | Canonical checked-in OpenAPI 3.1 document for Public API v1. |
| `frontend-next/openapi.json` | modify | Refresh the full app/internal OpenAPI snapshot; retain this distinct from the public canonical document. |
| `frontend-next/scripts/generate-api.mjs` | modify | Support explicit input/output paths and deterministically generate either internal or public TypeScript types. |
| `frontend-next/scripts/check-api-drift.mjs` | modify | Accept explicit input/output paths and check each generated type artifact against its spec. |
| `frontend-next/src/lib/public-api.generated.ts` | create | `openapi-typescript` generated `paths`/`components` for Public API v1; generated file is not edited manually. |
| `frontend-next/src/lib/public-api-client.ts` | create | Small `openapi-fetch` client factory using the generated public `paths`, explicit base URL and browser cookie credentials; no business behavior. |
| `frontend-next/package.json`, `frontend-next/package-lock.json` | modify | Add pinned `openapi-fetch` runtime dependency and scripts for public/internal generation and drift checks. |
| `.github/workflows/andromeda-ci.yml` | modify | Compare fresh full export with frontend full snapshot, compare fresh public export with canonical root `openapi.json`, and check both generated TS artifacts. |
| `scripts/andromeda.py` | modify | Extend `openapi` command to run both public and internal artifact/type drift checks. |
| `backend/tests/api/test_public_api_v1.py` | modify | Validate public projection paths, security/error metadata, no internal path leakage, and stable `info`/operation IDs. |

## Task 2: Export the canonical Public API v1 OpenAPI document

### Intent

Separate the client contract from `/ops`, review and university-admin routes without hiding them from FastAPI's `/docs` or `/openapi.json`.

### Implementation Steps

1. In `api/public_api_v1.py`, build Public OpenAPI from `create_app().openapi()` by filtering to exact `/api/v1` paths and HTTP operations. Remove empty/non-operation path items; preserve all schemas referenced by selected operations and all current standard structured error responses.
2. Set `info.title` to `Andromeda Public API`, `info.version` to `1.0.0`, and a description naming this as the v1 contract. Add a vendor extension describing cookie/session semantics, unpaginated list DTOs and the public surface. Do not rename DTO properties or alter runtime responses in this phase.
3. Add OpenAPI cookie security schemes only with the exact cookie names from `Settings` defaults; represent guest access as optional security on session-scoped user operations. If names are deployment-configurable, document the configured cookie boundary without falsely requiring credentials on guest calls.
4. Include the `ErrorResponse` schema and operation error response models for the statuses the app actually maps (`400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`). Document `Retry-After` for `429`. Avoid claiming a pagination contract that the routes do not provide.
5. The current assistant request model accepts `interactive`, but `/assistant/query` does not forward or consume it. Keep legacy runtime acceptance unchanged; omit this no-op property from the Public v1 assistant request schema so new clients cannot mistake it for a working control. Add a contract test for the omission and document the legacy compatibility behavior.
6. Extend `backend/scripts/export_openapi.py` with `--surface full|public-v1`, default `full`, and deterministic UTF-8 JSON output. `--surface public-v1 --out openapi.json` is the canonical generation command. Leave `/docs` and runtime full OpenAPI unchanged.
7. Generate the root `openapi.json` and refresh `frontend-next/openapi.json` from full surface. The latter remains an internal app snapshot because the current Web admin console consumes protected API DTOs.
8. Add contract tests asserting the exact public path set, version metadata, common error envelope, no `/ops/*` or `/university-admin/*` routes, no `/health/ready` leak, and no inert `interactive` property in the public assistant request.

### Required Interfaces and Contracts

- Canonical Public API v1 file: repository root `openapi.json`.
- Runtime public paths: `/api/v1/...`; operation IDs begin with `public_v1_`.
- Full FastAPI docs: `/docs` and `/openapi.json` continue describing the whole backend, including protected admin/ops APIs.
- `frontend-next/openapi.json` is explicitly the full app/internal snapshot, not a second Public API source of truth.
- Version: OpenAPI 3.1.0 and `info.version: 1.0.0`.
- Error schema: current `ErrorResponse`; no new error model or HTTP behavior.
- Assistant: public v1 request omits the currently inert `interactive` flag; legacy path remains unchanged and continues accepting its current DTO.
- List pagination: absent on current `universities`/`programs`; remain unpaginated for v1 and document that fact.
- No new API database schema, Alembic revision, LLM/Jev capability, or transport-specific DTO.

### Error Handling and Logging

- Export failures for unknown surfaces or missing public routes return a non-zero CLI result and a precise stderr message.
- Do not log environment values, auth/session cookies, or request bodies.

### Tests

- Unit/contract tests in `backend/tests/api/test_public_api_v1.py` compare the generated public operation set with the route allowlist and assert all paths resolve to valid operations.
- Test `/health/ready` and each internal/admin path is absent from public spec while present in full docs where applicable.
- Test all public operations expose the existing `ErrorResponse` model for declared error codes and rate-limited operations describe `Retry-After`.
- Test the Public v1 assistant request does not advertise `interactive`; its functional fields and response DTO remain sourced from the backend schemas.
- Verify exporter output is stable across two runs and can be parsed as OpenAPI 3.1 JSON.

### Acceptance Criteria

- Root `openapi.json` is generated from backend code and contains exactly the Public API v1 surface.
- Existing FastAPI docs and full frontend admin type source still contain protected route contracts.
- Exported Public API documents request/response schemas, enums, revisions, sessions, cookie boundary and error responses without adding unsupported pagination.

### Verification

- `cd backend; python scripts/export_openapi.py --surface public-v1 --out ../openapi.json`
- `cd backend; python -m pytest -q tests/api/test_public_api_v1.py tests/contracts/test_openapi_jsonschema.py`
- Expected result: canonical artifact is deterministic and contract tests pass.

## Task 3: Generate public client types/SDK and strengthen drift checks

### Intent

Make Public API consumers derive request/response types from the canonical contract while preserving current internal frontend types required by the admin UI.

### Implementation Steps

1. Generalize `frontend-next/scripts/generate-api.mjs` and `check-api-drift.mjs` to accept explicit spec and output paths (environment variables or command arguments) while preserving the existing full-app defaults.
2. Add scripts `generate-public-api` and `check-public-api-drift` that use `../openapi.json` and `src/lib/public-api.generated.ts`. Keep current `generate-api` and `check-api-drift` for full internal types in `src/lib/generated.ts`.
3. Add `openapi-fetch` as a pinned direct dependency. In `public-api-client.ts`, export a factory accepting a required API base URL and optional `fetch`; create the generated `paths`-typed client with `credentials: "include"` for browser session cookies. Do not put tokens in source or configure MAX-specific transport callbacks here.
4. Keep generated files machine-written. Preserve genuinely UI-specific view models in `types.ts`; replace no unrelated UI types and do not rewrite the current API adapter wholesale.
5. In `.github/workflows/andromeda-ci.yml`, export full and public schemas from the checked-out backend. Fail if full export differs from `frontend-next/openapi.json`, public export differs from root `openapi.json`, or either generated TS file is stale.
6. Update `scripts/andromeda.py openapi` to execute the same two comparisons locally. Use temporary paths under the system temp directory and clean only those exact temporary files.
7. Add TypeScript test/typecheck coverage proving the public client factory accepts Public API v1 operations and rejects internal `/ops` paths at compile time; preserve current internal generated types for admin API calls.

### Required Interfaces and Contracts

- Internal type artifact: `frontend-next/src/lib/generated.ts`, generated from full FastAPI OpenAPI.
- Public type artifact: `frontend-next/src/lib/public-api.generated.ts`, generated from root `openapi.json`.
- Public client factory: `createAndromedaPublicClient({ baseUrl, fetch? })` (exact name may follow existing TS naming, but parameters and behavior above are fixed).
- `credentials: "include"` is the browser default so HttpOnly guest/auth cookies use the existing backend identity boundary.
- CI's public drift gate checks all three representations: backend export, root canonical JSON, generated public TypeScript. Full app drift gate checks backend full export, frontend full OpenAPI snapshot, generated internal TypeScript.

### Error Handling and Logging

- Generator and drift scripts fail with non-zero status naming the stale spec/output paths; no silent fetch fallback in CI.
- Public client returns `openapi-fetch`'s typed `data`/`error`/`response`; it does not swallow status errors or verbalize server errors.
- Never log cookies or body content from client calls.

### Tests

- `frontend-next/scripts` drift checks for both surfaces.
- `frontend-next/src/lib/public-api-client.test.ts` (or type-level test) uses a stub `fetch` to verify base URL/path, method, cookie credentials and typed response contract.
- Existing frontend unit/lint/build checks verify the internal API and admin types remain intact.
- CI contract job must fail under deliberate local stale-artifact simulation; do not commit intentionally stale files.

### Acceptance Criteria

- Public API TypeScript path/request/response types come only from root `openapi.json`.
- A Public client consumer cannot address `/ops/*` or `/university-admin/*` through the typed public client.
- Current frontend admin calls still typecheck against the full generated artifact.
- Every backend contract change affecting either surface fails CI until canonical/generated artifacts are refreshed.

### Verification

- `cd frontend-next; npm run generate-api; npm run check-api-drift; npm run generate-public-api; npm run check-public-api-drift; npm run test:unit; npm run lint; npm run build`
- `python scripts/andromeda.py openapi`
- Expected result: both public and internal generated contracts are synchronized and frontend gates pass.

## Phase Risks and Mitigations

- Risk: replacing full generated types breaks admin UI imports. Mitigation: retain a distinct full/internal artifact and generate the Public API client separately.
- Risk: repeated OpenAPI artifacts become competing sources. Mitigation: root `openapi.json` is the only Public v1 canonical source; `frontend-next/openapi.json` is explicitly full/internal, both drift-checked.
- Risk: client cookies are silently omitted. Mitigation: default browser client to credentialed fetch and test it; document secure cookie storage for non-browser transports.

## Phase Completion Checklist

- Tasks 2-3 satisfy acceptance criteria.
- Required verification commands pass.
- `index.md` task checkboxes are updated immediately after verification.
