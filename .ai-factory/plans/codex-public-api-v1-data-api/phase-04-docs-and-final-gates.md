# Phase 4: Transport documentation and release verification

Plan: [index.md](index.md)
Tasks: 5
Depends on: Phase 1 / Task 1, Phase 2 / Tasks 2-3, Phase 3 / Task 4

## Objective

Document the stable public/client API boundary and transport integration rules, then run all relevant deterministic checks needed to hand off API work for a later MAX transport implementation.

## Current-Code Evidence

| Path | Symbols / evidence | Why it matters |
|------|-------------------|----------------|
| `docs/api.md` | current endpoints, cookies, `ErrorResponse`, analytics and assistant | Extend existing source of API truth rather than creating a parallel guide. |
| `docs/telegram-bot.md` | cookie transport, session state, channel-neutral assistant, Telegram-only callbacks/rendering | Demonstrates how a transport adapts platform state without owning domain logic. |
| `README.md` | project entrypoint and links | Add concise links to Public API v1 and DATA-API artifacts. |
| `.github/workflows/andromeda-ci.yml` | backend/frontend/Telegram/fullstack/packaging jobs | Keep public contract checks within the existing CI flow, not a new runtime service. |
| `scripts/andromeda.py` | canonical local gate | Integrate repeatable OpenAPI and DATA-API verification commands. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| `docs/api.md` | modify | Name root `openapi.json` as canonical Public API v1; explain `/api/v1`, full `/docs`, internal/admin exclusion, auth/session/error/revision and pagination semantics; list the supported MAX-facing endpoint groups. |
| `docs/telegram-bot.md` | modify | Explain that Telegram is an independent transport client to the same `/api/v1` business endpoints; identify transport-only aiogram/callback/render concerns that MAX must not copy into API. |
| `docs/testing.md` | modify | Document public/internal generation, drift checks, and official DATA-API validator command. |
| `README.md` | modify | Link to public API, OpenAPI and DATA-API guide without duplicating full schemas. |
| `.github/workflows/andromeda-ci.yml` | modify | Ensure DATA-API and both OpenAPI/client drift jobs are required for successful CI. |
| `scripts/andromeda.py` | modify | Add the `openapi` and `data-api` checks into `full` command sequence without hiding failures. |
| `frontend-next/src/lib/api.ts` | modify | Route user-facing calls through `/api/v1` while leaving `/ops/*` and `/university-admin/*` calls on the protected legacy surface. |
| `frontend-next/src/lib/api.test.ts` | modify | Assert public paths are versioned and protected admin paths retain existing URLs. |
| `telegram-bot/src/andromeda_telegram/clients/backend.py` | modify | Prefix the HTTP transport's existing public calls with `/api/v1`; keep its per-user cookie/session state behavior. |
| `backend/tests/api/test_public_api_v1.py` | modify | Add final regression assertions for deterministic health/catalog/comparison/assistant contract and protected-route separation. |
| `frontend-next/src/lib/public-api-client.test.ts` | create/modify | Verify browser credential behavior and generated typed-client boundary if a runtime test is required by the build. |
| `telegram-bot/tests/test_backend_client.py` | modify | Prove the transport calls versioned public routes and still persists opaque profile/session state, with no Telegram-specific identifiers passed as trusted identity. |

## Task 5: Document transport boundary and prove readiness for MAX development

### Intent

Make the next MAX implementation consume an explicit supported HTTP contract while keeping all assistant, DecisionContext, admissions, comparison, Jev and persistence behavior in Andromeda.

### Implementation Steps

1. Update `docs/api.md` with canonical artifact names and generation commands. State that root `openapi.json` is the only canonical Public API v1 spec, `frontend-next/openapi.json` is an internal full-app snapshot, and `/docs`/runtime `/openapi.json` are full operator documentation.
2. Document `/api/v1` path prefix, guest `andromeda_profile_session` cookie, configured account auth cookie, `credentials: include`, opaque session IDs/revisions and `409` stale revisions. Do not expose cookies as manually constructed bearer credentials.
3. Document `ErrorResponse` and status mapping including 429/`Retry-After`; document current list endpoints as unpaginated. Explain that all `/ops`, university-admin authoring and knowledge-review APIs are excluded from Public v1 and remain separately protected.
4. Add a method/path endpoint index grouped by university/program/curriculum, comparison, analytics/assistant, DecisionContext, proftest/profile/recommendations, admission facts/fit/benefits, auth, events/campus and health. Include deprecated proftest compatibility operations as deprecated.
5. Update `docs/telegram-bot.md` to show the public route prefix and clarify its encrypted per-platform-user state store is a Telegram transport implementation only. MAX should call Public API v1 and must not embed aiogram callbacks, Telegram IDs or renderer protocol into Andromeda contracts.
6. Update `docs/testing.md`/README with exact public and internal type generation/check commands, official validator command, pinned upstream SHA, and note that the example API base URL is a placeholder until a real HTTPS deployment URL is supplied.
7. Add a fixture-backed API smoke test spanning health, university list, program list, details, curriculum, admissions, comparison and deterministic assistant query through `/api/v1`. Avoid auth secrets and external provider calls.
8. Update the Next public API path helper and Telegram backend client to call `/api/v1`; preserve direct paths only for protected admin/ops UI calls. Preserve Telegram's opaque cookie/query-session/revision handling and assert bot user ID never becomes backend identity.
9. Run the repository OpenAPI/DATA-API commands, targeted backend/Telegram/frontend checks, then the repository full check. Inspect `git diff --check`, route count, generated artifact diff, no migrations, no Jev flags, no secrets and worktree scope.

### Required Interfaces and Contracts

- Documentation distinguishes public client API from full runtime docs and private operator APIs.
- Telegram and future MAX Bot/Mini App communicate through `/api/v1` and channel-neutral DTOs; all business decisions remain in backend services.
- Cookie state is browser-managed or securely persisted by a server transport; platform IDs are not trusted identity.
- No MAX bot implementation, MAX SDK, new app feature, ingestion integration or LLM/Jev activation is part of this task.
- The official validator is pinned to `8504a6d9b39e6f652bce689d96e88538d7541c6b`.

### Error Handling and Logging

- Docs explain stable errors and client recovery for validation/auth/not-found/conflict/rate-limit responses.
- Smoke tests report response bodies only on failure and use synthetic fixtures; never log session cookies or personal data.
- An absent configured organizer deployment URL is a setup note, not a reason to invent a hostname or weaken offline contract checks.

### Tests

- Backend public API contract and deterministic flow tests.
- Telegram Bot client unit tests and strict mypy.
- Frontend unit tests, lint, TypeScript/build, public client typecheck and both OpenAPI drift gates.
- Official DATA-API validator.
- Architecture boundary tests proving no transport imports from subject modules and no public OpenAPI leakage of internal APIs.
- Repository full gate via `python scripts/andromeda.py full`; report any environment-limited checks rather than marking them green.

### Acceptance Criteria

- A MAX implementer can identify the canonical spec, supported endpoints, cookie/session flow, error/revision contract and generated client without reading backend internals.
- Telegram remains a thin transport adapter using `/api/v1`; no Telegram-specific DTO or identity rule enters the public contract.
- All Public OpenAPI, generated clients, DATA-API and documentation checks pass with a clean diff check.
- No Max runtime, migration, business feature or Jev/LLM runtime flag is added/enabled.

### Verification

- `python scripts/andromeda.py openapi`
- `python scripts/andromeda.py data-api`
- `python scripts/andromeda.py full`
- `cd telegram-bot; python -m pytest -q; python -m mypy src`
- `cd frontend-next; npm run test:unit; npm run lint; npm run build; npm run check-api-drift; npm run check-public-api-drift`
- `git diff --check`
- Expected result: all available gates pass; any unavailable external Postgres/browser tool is called out explicitly.

## Phase Risks and Mitigations

- Risk: API docs accidentally imply that `/docs` is the public API spec. Mitigation: explicitly name root `openapi.json` and full runtime docs separately.
- Risk: MAX implementation duplicates assistant/session/business rules from Telegram. Mitigation: document only HTTP contracts and transport-specific boundaries.
- Risk: aggregate verification exceeds the local environment. Mitigation: run targeted gates, run full gate once, and report each blocked check with exact environment reason.

## Phase Completion Checklist

- Task 5 satisfies all acceptance criteria.
- All requested checks have evidence.
- `index.md` Task 5 checkbox is updated immediately after verification.
