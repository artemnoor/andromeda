<!-- aif:plan-mode:ultra -->
# Ultra Implementation Plan: Andromeda Public API v1 and DATA-API

Mode: ultra
Branch: codex/public-api-v1-data-api
Created: 2026-09-28
Baseline: `origin/main` at `19c5a8312e3e11864fbb8841caa4ede7594d1160`

## Original Request

Используя полный цикл аи фактори выполни

Работаем с текущим репозиторием Andromeda. Сначала глубоко изучи актуальный main, особенно backend API, OpenAPI generation, frontend generated client, CI contract-drift checks, /assistant/query, DecisionContext, comparison, admissions и существующий Telegram transport.

Дополнительно обязательно изучи репозиторий организаторов хакатона:
https://gitverse.ru/stasnorman/example-data-api

Используй skills/best practices при проектировании и реализации. Не делай механических изменений — сначала составь архитектурный план, проверь существующие решения и максимально переиспользуй то, что уже есть.

Цель этапа: подготовить Andromeda к подключению MAX и одновременно полностью выполнить требования организаторов к собственному API.

Нужно:

1. Сформировать и зафиксировать стабильный Public API v1 для пользовательских клиентов Andromeda: MAX Bot, MAX Mini App/Web и других transport-клиентов.
2. Не создавать второй backend и не дублировать бизнес-логику.
3. Отделить public/client-facing контракт от /ops, knowledge-review и других внутренних/admin API, если это необходимо.
4. Проверить все request/response DTO, ошибки, enum, pagination, revisions, session semantics и authentication boundary.
5. Сохранить FastAPI /docs, но сделать один канонический экспортируемый OpenAPI-контракт Public API.
6. Организовать генерацию клиентских типов/SDK из этого OpenAPI вместо ручного дублирования DTO.
7. Сохранить и усилить CI drift-check: изменение backend-контракта должно обнаруживаться автоматически.
8. Подготовить в корне проекта DATA-API.yaml строго по официальной DATA-API 1.0 schema из репозитория организаторов.
9. При необходимости подготовить рядом canonical openapi.yaml/openapi.json в том виде, который ожидает DATA-API.
10. В DATA-API.yaml описать небольшой, но репрезентативный и детерминированный сценарий технической проверки Andromeda. Предпочтительно использовать стабильные операции вроде health → universities/programs → program details/curriculum → comparison → /assistant/query и, если безопасно, DecisionContext. Не делай проверку зависимой от живого Jev, LLM, внешнего парсинга или нестабильных внешних сайтов.
11. Использовать возможности DATA-API для передачи значений между checks, если формат это позволяет.
12. Скачать/использовать официальный validator из репозитория организаторов и добиться реального PASS.
13. Добавить проверку DATA-API в CI, если это разумно.
14. Обновить документацию так, чтобы было однозначно понятно:

* какой OpenAPI является canonical;
* что является Public API v1;
* как обновлять generated clients;
* как запускать DATA-API validator;
* какие endpoints предназначены для MAX.

15. Не реализовывать пока самого MAX-бота. Этот этап заканчивается на полностью готовой и проверенной API-boundary, поверх которой следующим этапом будет писаться MAX transport.

Особенно проверь текущие:

* backend/src/andromeda/api/main.py
* backend/scripts/export_openapi.py
* frontend-next/openapi.json
* frontend-next/scripts/generate-api.mjs
* frontend-next/scripts/check-api-drift.mjs
* .github/workflows/andromeda-ci.yml
* docs/api.md
* docs/telegram-bot.md
* telegram-bot/

Telegram используй как доказательство правильной transport-архитектуры, но не копируй его специфичные aiogram/Telegram детали в Public API.

Ключевой архитектурный принцип:

MAX Bot / MAX Mini App / Web → Public API v1 → Andromeda backend → domain/services/data.

Jev, policy resolver, analytics, ingestion и БД должны оставаться скрыты за API boundary.

В конце:

* выполни все необходимые тесты;
* запусти официальный DATA-API validator;
* проверь OpenAPI drift;
* покажи конкретный список изменённых файлов;
* дай список Public API v1 endpoints;
* укажи, остались ли какие-либо blockers перед началом разработки MAX;
* если всё прошло — явно напиши READY FOR MAX TRANSPORT DEVELOPMENT.

Не считай задачу завершённой только потому, что YAML синтаксически валиден. Нужны реальные контракты, реальный validator PASS и отсутствие рассинхронизации между backend, OpenAPI и generated clients.

## Settings

- Testing: yes
- Logging: standard
- Docs: yes
- Roadmap linkage: none
- Branch base: clean `origin/main` at the baseline SHA above

## Architecture and Decisions

- Andromeda remains one modular-monolith backend, one FastAPI application, one database boundary and existing application services. No second backend, MAX runtime, new bounded context, data migration, Jev integration or business evaluator is introduced.
- Public API v1 is additive at `/api/v1`. It re-registers only an explicit allowlist of existing `APIRoute` endpoints against the same endpoint functions, dependencies and services. Existing unversioned paths remain as compatibility routes; Web user calls use v1 while protected internal/admin calls remain on the current boundary. The former Telegram package has been retired; future clients such as MAX use the same public contract.
- Allowlist is per method/path because university catalog/events and knowledge routers contain mixed public/admin operations. Tags and whole-router inclusion are insufficient.
- `/docs`, `/redoc` and runtime `/openapi.json` remain the full FastAPI application documentation. The sole canonical exported Public API v1 contract is repository root `openapi.json`. `frontend-next/openapi.json` remains a separately labelled full/internal snapshot because the existing web admin client consumes protected API types.
- Public API OpenAPI is projected from the same app schema and contains only `/api/v1` operations. Export and CI drift checks compare backend output → root canonical file → generated public client types. Full app export → `frontend-next/openapi.json` → existing generated types is checked independently.
- `openapi-typescript` supplies generated public wire types; the thin `openapi-fetch` wrapper supplies a typed HTTP client with browser credential forwarding. UI view models remain UI-owned; no handwritten copy of the public wire DTOs is added.
- Existing `ErrorResponse`, canonical IDs, camel-case request aliases, current response DTO field casing, error status mapping, guest profile cookie, configured auth cookie, owner-bound sessions, optimistic revisions and `409` conflict semantics are preserved. The actual unpaginated list response contract is documented; pagination is not added in this task.
- The public v1 assistant schema omits the current no-op `interactive` request flag; the legacy route/DTO remains unchanged for compatibility. Assistant session ID/revision remain typed. Public clients use only the deterministic supported query path; no Jev or LLM is required.
- The deterministic DATA-API flow uses health, university/program listing, program detail/curriculum/admissions, comparison and one explicitly non-repeatable assistant query. It extracts program IDs between checks. DecisionContext is excluded because first access creates a persisted owner context. The official validator is pinned to GitVerse commit `8504a6d9b39e6f652bce689d96e88538d7541c6b`, with upstream attribution and schema retained.
- Root DATA-API base URL uses an HTTPS `.example` placeholder until an actual organizer-accessible deployment hostname is provided. The validator checks schema, semantics and OpenAPI mapping; it does not make the placeholder a live HTTP endpoint.
- No changes to admission/business behavior, response prose, source ingestion, Jev flags/calibration, policy resolution, databases or migrations.

## Phase Index

1. [Phase 1: Public API v1 boundary and route compatibility](phase-01-public-v1-boundary.md) — Task 1
2. [Phase 2: Canonical Public OpenAPI and generated client](phase-02-openapi-client-generation.md) — Tasks 2-3
3. [Phase 3: DATA-API 1.0 and official validator](phase-03-data-api-validator-and-ci.md) — Task 4
4. [Phase 4: Transport documentation and release verification](phase-04-docs-and-final-gates.md) — Task 5
5. [Phase 5: Final Public API operation audit](phase-05-public-api-final-audit.md) — Tasks 6-7
6. [Phase 6: Telegram transport retirement](phase-06-transport-retirement.md) — Tasks 8-9
7. [Phase 7: Final contract and repository verification](phase-07-final-verification.md) — Task 10

## Cross-Phase Dependencies

- Task 6 audits the current 61 operations before Task 7 changes the Public API allowlist.
- Tasks 8-9 use the audit's dependency findings; Task 10 runs only after contract and transport changes are complete.

- Task 1 establishes the exact runtime v1 alias set and must precede Public OpenAPI projection.
- Task 2 uses Task 1's aliases/manifest to produce canonical root `openapi.json`.
- Task 3 generates public SDK types and enforces drift for both public and full/internal contracts; it depends on Task 2.
- Task 4's DATA-API operations are valid only against canonical root `openapi.json`, so it depends on Tasks 2-3.
- Task 5 integrated the frontend client and docs with the frozen contract. Tasks 8-9 retire the former Telegram transport and supersede Telegram-specific assertions in the completed Task 5 artifacts.

## Scope Boundaries

- In scope: Public API v1 boundary, version aliases, canonical export, client code generation, drift checks, DATA-API file, official validator, CI gate, docs and client route adoption.
- Out of scope: MAX bot/Mini App implementation, new product use cases, new domain DTO semantics except omitting one inert request control from public documentation, new pagination feature, new authentication mechanism, backend split, migrations, Jev runtime/provider changes, hosted deployment or live organizer endpoint probing.
- Existing dirty worktrees are not implementation inputs. Work starts from a new clean worktree at the actual `origin/main` SHA shown above.

## Tasks

### Phase 1: Public API v1 boundary and route compatibility

- [x] Task 1: Add allowlisted `/api/v1` aliases and preserve rate-limit/security behavior ([details](phase-01-public-v1-boundary.md#task-1-add-a-public-only-api-v1-route-surface))

### Phase 2: Canonical Public OpenAPI and generated client

- [x] Task 2: Export and test the canonical Public API v1 OpenAPI ([details](phase-02-openapi-client-generation.md#task-2-export-the-canonical-public-api-v1-openapi-document))
- [x] Task 3: Generate public client types/SDK and enforce two-surface drift checks ([details](phase-02-openapi-client-generation.md#task-3-generate-public-client-types-sdk-and-strengthen-drift-checks)) (depends on 2)

### Phase 3: DATA-API 1.0 and official validator

- [x] Task 4: Add deterministic DATA-API checks and run the pinned official validator ([details](phase-03-data-api-validator-and-ci.md#task-4-add-and-validate-deterministic-data-api-checks)) (depends on 2, 3)

### Phase 4: Transport documentation and release verification

- [x] Task 5: Document the transport boundary and prove readiness for MAX development ([details](phase-04-docs-and-final-gates.md#task-5-document-transport-boundary-and-prove-readiness-for-max-development)) (depends on 1-4)

### Phase 5: Final Public API operation audit

- [x] Task 6: Audit all 61 operations and record evidence-backed retain/exclude decisions ([details](phase-05-public-api-final-audit.md#task-6-audit-the-61-public-operations)) (depends on 1-5)
- [x] Task 7: Exclude only deprecated operations and publish the exact 58-operation inventory ([details](phase-05-public-api-final-audit.md#task-7-publish-the-supported-client-contract)) (depends on 6)

### Phase 6: Telegram transport retirement

- [x] Task 8: Remove Telegram package, command, CI job, compose service, deployment variables and test targets ([details](phase-06-transport-retirement.md#task-8-remove-the-product-transport)) (depends on 6)
- [x] Task 9: Remove stale integration contracts/references while retaining active channel-neutral infrastructure ([details](phase-06-transport-retirement.md#task-9-retain-neutral-infrastructure-and-update-docs)) (depends on 6, 8)

### Phase 7: Final contract and repository verification

- [ ] Task 10: Regenerate snapshots/clients and run the full verification matrix without commit/push ([details](phase-07-final-verification.md#task-10-run-final-verification)) (depends on 7-9)

## Final Execution Evidence

Verification attempt on 2026-09-28 in the isolated `codex/public-api-v1-data-api` worktree, based on `origin/main` `19c5a8312e3e11864fbb8841caa4ede7594d1160`:

- `python scripts/andromeda.py fast` — passed after both OpenAPI snapshots and clients were regenerated with the locked `uv` environment.
- Full backend suite and backend coverage suite — each reported 1110 passed, 9 skipped; the nine skips are PostgreSQL-only tests because `ANDROMEDA_POSTGRES_TEST_URL` is unset.
- Backend strict typing — no issues in 680 source files.
- Frontend unit tests and lint — passed before the production build step.
- Frontend production build — blocked by `ENOSPC` while copying Next output into `frontend-next/.next/standalone`; C: had 0 bytes free. The test-generated `.next` and `artifacts/coverage/backend` paths are ignored build outputs. An attempted cleanup was blocked by the command safety review, so those outputs were preserved.
- Migration suite — 28 passed; fresh SQLite migration upgrade to `0056_exact_conflict_participant_uniqueness` and `alembic check` passed.
- Fixture ingestion — BMSTU and HSE fixture runs passed.
- Public API inventory — 58 method/path operations. The full snapshot retains unversioned compatibility routes; Public OpenAPI excludes only the three deprecated Proftest aliases.
- Public/full OpenAPI snapshots and generated client drift checks passed. The official pinned DATA-API 1.0 validator passed. Documentation-link and deployment-artifact checks passed.
- Hosted GitHub CI, PostgreSQL integrations and Playwright/production smoke are not verified in this run: no push was authorized, the PostgreSQL DSN is unset, and the full local command stopped at the disk-full frontend build before later targets.
- The DATA-API base URL remains `https://andromeda.example.org`; replace it with the organizer-accessible HTTPS deployment URL before live HTTP checks.

## Commit Plan

- **Commit 1** (after Task 1): `feat(api): add allowlisted Public API v1 routes`
- **Commit 2** (after Tasks 2-3): `feat(api): publish canonical OpenAPI and generated client`
- **Commit 3** (after Task 4): `chore(data-api): add official validator and deterministic checks`
- **Commit 4** (after Task 5): `docs(api): document Public API v1 and MAX boundary`

Commit execution remains subject to the user's Git workflow; this plan does not authorize push, PR creation, merge or deployment.

## Definition of Done

- A separate clean implementation worktree was based on `origin/main` SHA `19c5a8312e3e11864fbb8841caa4ede7594d1160`; existing dirty worktrees remain untouched.
- Same backend app serves legacy routes and explicit `/api/v1` aliases through existing endpoint/business logic. Internal/admin routes are not in the public allowlist.
- `/docs` remains full, root `openapi.json` is the sole canonical Public API v1 export, and generated public/internal client artifacts pass drift checks.
- Web uses public v1 paths for user endpoints; future MAX clients will use the same contract, while protected admin calls remain protected and unversioned. No Telegram runtime remains.
- DATA-API YAML passes the exact pinned official validator and every described operation exists in canonical Public API OpenAPI.
- Documentation answers which API/spec MAX should use, how to generate/check clients, session/auth/revision/error semantics, and how to validate DATA-API.
- Backend, architecture, frontend, OpenAPI drift, official DATA-API, deployment/docs and `git diff --check` gates are reported accurately, including the build blocker and PostgreSQL skips. Telegram-specific runtime/test targets have been removed.
- No MAX runtime, migrations, product features, Jev flags or secrets were added by Tasks 1-5.

## Follow-up Scope: Final API Audit and Telegram Retirement

Tasks 6-9 are complete; Task 10 remains incomplete because the local frontend production build ran out of space on C:. Work remains on codex/public-api-v1-data-api and must not be committed or pushed.

Research evidence before editing:

- The pre-audit explicit allowlist contained 61 operations; the canonical public allowlist now contains 58.
- POST /analytics/query is a stable typed QuerySpec client capability and the server-side frontend OG analytics renderer consumes its /api/v1 alias. Retain it.
- GET /proftest/questions, POST /proftest/preview and POST /proftest/results are deprecated. Active Web proftest uses version-pinned session endpoints and has no call sites for the legacy helpers. Keep their unversioned compatibility routes; remove only Public API aliases.
- Campus/events and auth have active Web call sites. Decision, assistant, analytics, admission-benefit, catalog, recommendations, profile, session and telemetry APIs remain client-facing. The three deprecated proftest exclusions leave 58 operations.
- The 40-file telegram-bot package, its CI job, compose service/volume, command-runner target, deployment contract references, env sample and tests are isolated. Frontend OG routes and HMAC have active Web dependencies.
- ResponseEnvelope and ResponsePlan are used by assistant/query. The separate unimplemented channel adapter protocol is unused and can be removed; do not add a MAX replacement.
- Decision analytics payloads are opaque JSON and aggregate readers never deserialize the source field; removing the retired source enum needs no migration.
- Root openapi.json, DATA-API.yaml, validator, generated client and drift CI are existing deliverables and must stay synchronized.
