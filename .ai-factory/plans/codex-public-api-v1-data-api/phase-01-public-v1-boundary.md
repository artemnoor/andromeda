# Phase 1: Public API v1 boundary and route compatibility

Plan: [index.md](index.md)
Tasks: 1
Depends on: none

## Objective

Create an explicit, versioned client-facing route surface under `/api/v1` by reusing existing FastAPI endpoint handlers, request models, dependencies and application services. Preserve all existing unversioned routes for current clients and keep internal/admin operations out of the new public surface.

## Current-Code Evidence

| Path | Symbols / evidence | Why it matters |
|------|-------------------|----------------|
| `backend/src/andromeda/api/main.py` | `create_app`, `AndromedaFastAPI`, router registration | One FastAPI app currently registers public, university-admin, knowledge-review and ops routes together. Keep `/docs` and runtime `/openapi.json` as the full app documentation surface. |
| `backend/src/andromeda/api/routes/*.py` | existing routers and endpoint functions | Version aliases must delegate to these handlers, not copy application or domain behavior. Some route files mix public reads with admin actions. |
| `backend/src/andromeda/api/request_controls.py` | `rate_limit_policy` | Current rate-limit matching uses unversioned path strings and must also protect `/api/v1` aliases. |
| `backend/src/andromeda/api/schemas/common.py` | `ApiModel`, `ErrorResponse` response DTOs | Preserve existing strict DTOs, aliases, error envelope and status mapping. |
| `backend/tests/api/test_assistant_query.py` | deterministic metric-comparison test | Proves the assistant path is usable without live Jev or LLM. |
| `backend/tests/api/test_andromeda_api.py`, `test_compare_contract.py` | program, curriculum, admissions and comparison fixtures | Proves the deterministic API smoke path and canonical fixture IDs. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| `backend/src/andromeda/api/public_api_v1.py` | create | Explicit `(HTTP method, existing path)` allowlist and one route-alias registration helper; add `/api/v1` aliases with stable `public_v1_...` operation IDs and a surface/version extension. |
| `backend/src/andromeda/api/main.py` | modify | Register the aliases after the existing routes are composed; preserve the current `/docs`, `/redoc` and full `/openapi.json`. Add the missing documented 429 response using the existing `ErrorResponse`. |
| `backend/src/andromeda/api/request_controls.py` | modify | Normalize only the `/api/v1` prefix before applying the existing rate-limit policy, so auth/sensitive route limits remain equivalent. |
| `backend/tests/api/test_public_api_v1.py` | create | Assert exact allowlist coverage, compatibility paths, public aliases, dependency/response preservation and exclusion of internal/admin operations. |
| `backend/tests/api/test_request_controls.py` | modify | Assert a sensitive/auth route and `/api/v1` alias receive the same bounded rate-limit policy. |

## Task 1: Add a public-only `/api/v1` route surface

### Intent

Give MAX Bot, MAX Mini App/Web and other clients a stable URL version without changing the current API paths or creating a second app/backend. A checked allowlist is required because tags and routers mix public and administrative operations.

### Implementation Steps

1. In `api/public_api_v1.py`, define one explicit mapping from existing method/path pairs to the Public API v1 set. Include user-facing catalog/university reads, programs/curriculum/admissions, comparison, analytics query, assistant query, auth/session, DecisionContext commands/reads, current and deprecated proftest operations, recommendations, admission-fit/benefit reads and evaluation, events, campus, discipline areas, personal-route compatibility, and `/health/live`.
2. Exclude `/health/ready`, every `/ops/*`, every `/university-admin/*`, `GET /university-admin/memberships`, and any knowledge review/authoring operation. Do not use tag-only or prefix-only classification for mixed routers.
3. After normal router registration in `create_app`, find each allowlisted source `APIRoute`, register an additive alias at `/api/v1` + the existing path, and preserve its endpoint, methods, dependency graph, request/response models, status codes, response class, deprecation state, tags and response filters. Set a deterministic operation ID prefixed `public_v1_`; attach `x-andromeda-api-surface: public` and `x-andromeda-api-version: 1`.
4. Fail app construction with an actionable error if an allowlisted method/path is missing or duplicated. Do not expose a route merely because a new router was added.
5. Preserve legacy routes at their current paths. Do not add business logic or authorization exceptions in the alias layer; both paths must use the same dependencies and services.
6. Add `429: ErrorResponse` to the app-level OpenAPI response map because `request_controls` already returns a typed rate-limit error and `Retry-After` header. Do not change the runtime rate-limit policy itself.
7. Normalize `/api/v1` for the existing auth, ops and sensitive rate-limit path matching. Add no new limiter, in-memory store or auth mechanism.
8. Add tests proving the v1 alias calls the same fixture-backed handler, old path still responds, stateful guest routes retain their cookie/session/revision behavior, and no v1 alias exists for internal/admin routes. Confirm admin routes remain available only at their existing protected paths.

### Required Interfaces and Contracts

- Prefix: `/api/v1`.
- Public manifest: exact method/path pairs in `PUBLIC_API_V1_OPERATIONS`; implementation must match source `APIRoute` objects, not operation tags.
- Manifest method/path set:
  - `GET /admission-benefits/olympiads/{olympiad_id}/programs`; `GET /universities/{university_id}/admission-benefits`; `GET /programs/{program_id}/admission-benefits`; `POST /programs/{program_id}/admission-eligibility`.
  - `POST /analytics/query`; `POST /assistant/query`.
  - `POST /auth/decision/import-guest`; `POST /auth/login`; `POST /auth/logout`; `POST /auth/register`; `GET /auth/session`.
  - `GET /campus/points`; `GET /campus/points/{id}`; `GET /campus/points/{id}/events`; `GET /campus/recommendations`.
  - `GET /compare`; `GET /compare/summary`; `GET /discipline-areas`.
  - `POST /decision/analytics`; `POST /decision/considered`; `PUT /decision/constraints`; `GET /decision/context`; `POST|DELETE /decision/final-choice`; `POST|DELETE /decision/programs/{program_id}/exclude`; `POST /decision/programs/{program_id}/restore`; `POST /decision/refinement/answer`; `POST /decision/shortlist`; `PATCH|DELETE /decision/shortlist/{program_id}`; `GET /decision/suggestions`; `POST /decision/suggestions/{program_id}/accept`; `POST /decision/suggestions/{program_id}/reject`.
  - `GET /events`; `GET /events/{id}`; `GET /health/live`; `GET /personal-route`.
  - `POST /proftest/analytics`; `POST /proftest/preview`; `GET|POST|PUT /proftest/profile`; `GET /proftest/questions`; `POST /proftest/results`; `POST /proftest/sessions`; `GET|PATCH /proftest/sessions/current`; `POST /proftest/sessions/current/complete`; `POST /proftest/sessions/current/next`.
  - `GET /programs`; `GET /programs/{id}`; `POST /programs/{id}/admission-fit`; `GET /programs/{id}/admissions`; `GET /programs/{id}/curriculum`; `POST /recommendations`; `GET /recommendations/current`.
  - `GET /universities`; `GET /universities/{university_id}/catalog`; `GET /universities/{university_id}/events`; `GET /universities/{university_id}/events/{event_id}`.
- Exclude `/health/ready`, `/ops/*`, `/university-admin/*`, `GET /university-admin/memberships`, and all internal knowledge/review routes.
- New OpenAPI operation IDs: `public_v1_<stable-source-operation-id>`.
- Additive compatibility: existing unversioned endpoints continue to behave identically.
- Readiness boundary: only `/health/live` is part of Public API v1; DB/schema readiness remains operational.
- Error envelope: reuse `ErrorResponse`; 429 includes the existing `Retry-After` response header behavior.
- Authentication: retain opaque `andromeda_profile_session` / configured auth cookie semantics and guest access. Never treat MAX/Telegram platform user IDs or ops API keys as a public identity token.
- Pagination: preserve existing DTOs. `/universities` and `/programs` are currently unpaginated item collections; document that behavior rather than adding a new pagination feature in this phase.

### Error Handling and Logging

- Missing or duplicate manifest routes are startup/configuration defects; fail closed with the missing method/path in the exception.
- Alias execution goes through the current middleware, trusted-origin validation, correlation ID, rate limiting, exception mapping and security headers.
- Never log request cookies, assistant text, applicant data, auth tokens or raw headers.

### Tests

- `backend/tests/api/test_public_api_v1.py`: public manifest is fully registered; no internal/admin path is exported as v1; representative public GET and assistant POST aliases have the same result contracts as legacy routes; `/docs` and `/openapi.json` remain reachable and full.
- `backend/tests/api/test_request_controls.py`: auth/sensitive alias receives the same policy as its source path.
- Existing assistant, program, curriculum, admissions, comparison, auth/session, DecisionContext and proftest API tests remain green.

### Acceptance Criteria

- Every manifest operation is registered once under `/api/v1` and has a stable unique operation ID.
- No `/ops`, knowledge-review, university-admin or readiness operation is registered under `/api/v1`.
- Existing route behavior is unchanged and remains tested.
- Rate limits, cookies, CORS/trusted origin checks, structured errors and correlation headers apply to v1 aliases.

### Verification

- `cd backend; python -m pytest -q tests/api/test_public_api_v1.py tests/api/test_request_controls.py tests/api/test_assistant_query.py tests/api/test_andromeda_api.py tests/api/test_compare_contract.py`
- Expected result: all tests pass; v1 requests traverse the same service/dependency path as their existing equivalents.

## Phase Risks and Mitigations

- Risk: manually cloning a FastAPI route can omit a response/dependency setting. Mitigation: keep the helper small, copy all supported `APIRoute` metadata, assert representative dependencies and response schemas in tests, and keep legacy operations registered normally.
- Risk: alias paths skip existing rate-limit matching. Mitigation: normalize prefix before current matching and test source/alias equivalence.
- Risk: future route additions accidentally become public. Mitigation: fail on manifest drift only for explicitly listed routes; do not infer public membership from router or tag names.

## Phase Completion Checklist

- Task 1 satisfies all acceptance criteria.
- Required verification commands pass.
- `index.md` Task 1 checkbox is updated immediately after verification.
