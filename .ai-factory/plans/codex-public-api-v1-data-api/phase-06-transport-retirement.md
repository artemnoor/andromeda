# Phase 6: Telegram Transport Retirement

Plan: [index.md](index.md)
Tasks: 8-9
Depends on: Phase 5 / Task 6

## Objective

Delete the standalone Telegram product transport and every active operational hook without removing shared backend, Web, OpenAPI or presentation capabilities.

## Current-Code Evidence

| Path | Symbols / behavior | Why it matters |
|------|--------------------|----------------|
| telegram-bot/ | 40 tracked package, source, Docker, config and test files | Self-contained transport package to remove after checking worktree contents. |
| .github/workflows/andromeda-ci.yml | bot CI job, image/token environment and build step | Must not refer to deleted package. |
| deploy/yc/compose.yaml | bot service and telegram_bot_data volume | Runtime unit and local state mount to remove. |
| scripts/andromeda.py | bot path, command target, full target list | Canonical test runner currently has a dead target. |
| scripts/check_deployment_artifacts.py | reads bot env sample | Must validate surviving deployment instead. |
| frontend-next/src/app/og and frontend-next/src/lib/server-api.ts | signed server-side OG render | Active Web consumer; preserve. |
| backend/src/andromeda/modules/presentation/contracts | ResponseEnvelope/ResponsePlan used by assistant; unused transport module | Preserve response contracts; remove only the unused channel adapter seam. |
| backend/src/andromeda/modules/decision/contracts/analytics.py | DecisionAnalyticsSource | Remove the retired source value; storage is opaque JSON. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| telegram-bot/ | delete | Remove the verified 40-file standalone transport package, including dependencies, callbacks, keyboard, session storage, renderer client, env sample and tests. |
| .github/workflows/andromeda-ci.yml | modify | Remove only bot CI, image, token and Docker build configuration. |
| deploy/yc/compose.yaml and deploy/yc/README.md | modify | Remove bot service/volume/secrets/instructions; retain database, backend, frontend and Caddy. |
| scripts/andromeda.py | modify | Remove bot path, target and full gate member. |
| scripts/check_deployment_artifacts.py | modify | Validate backend/frontend/Caddy routing without bot config. |
| backend/src/andromeda/modules/decision/contracts/analytics.py | modify | Remove retired telemetry source. |
| backend/src/andromeda/modules/presentation/contracts/transport.py and contracts/__init__.py | delete/modify | Remove unused adapter protocol and exports only. |
| active docs, tests and architecture scans | modify | Remove current bot claims and stale path/namespace guards. |
| docs/telegram-bot.md | delete | Remove dedicated product guide and navigation links. |

## Task 8: Remove the Product Transport

### Intent

Remove the standalone delivery process and all build/deployment/test coupling to it.

### Implementation Steps

1. Verify the absolute target resolves to this worktree's telegram-bot directory; list tracked and untracked contents. Preserve anything not tracked or pre-existing.
2. Remove only the reviewed tracked files in telegram-bot.
3. Remove the GitHub Actions transport job, install/test/type steps, packaging image/token env and Docker build.
4. Remove the compose service, service-only environment and persistent volume. Keep shared frontend rendering HMAC configuration because the current Next server uses it.
5. Remove the bot test path and command from scripts/andromeda.py, including the full gate.
6. Change deployment contract validation to check the surviving backend/frontend images, ports and public API reverse proxy without reading the deleted env sample.
7. Update deployment docs to describe only backend, frontend, database and Caddy units.
8. Do not add MAX placeholders, runtime modules, auth schemes or database migrations.

### Required Interfaces and Contracts

- scripts/andromeda.py --help has no bot command.
- Compose contains no Telegram service, dependency, environment or volume.
- CI packaging builds only tracked backend/frontend images.
- Public API reverse proxy and frontend's internal backend URL remain.

### Error Handling and Logging

- Deployment contract checker fails explicitly if a surviving backend/frontend/proxy contract is missing.
- Do not print secrets or inject real credentials during Compose validation.
- No replacement transport logs or settings are introduced.

### Tests

- python scripts/check_deployment_artifacts.py
- python scripts/andromeda.py --help
- docker compose --file deploy/yc/compose.yaml config --quiet with test placeholders for required deployment values
- Inspect CI job dependencies for references to the removed bot job.

### Acceptance Criteria

- The Telegram package is deleted.
- CI, deployment, test runner, configuration and secrets no longer require it.
- Remaining deployment artifacts are valid with only shared product services.

### Verification

- git diff --check
- python scripts/check_deployment_artifacts.py
- python scripts/andromeda.py --help
- rg -n -i 'telegram-bot|aiogram|andromeda_telegram|TELEGRAM_BOT' deploy scripts .github
- Expected: no active transport/package/deployment references remain.

## Task 9: Retain Neutral Infrastructure and Update Docs

### Intent

Remove misleading bot and placeholder channel-adapter concepts without discarding current assistant, Web or rendering behavior.

### Implementation Steps

1. Remove DecisionAnalyticsSource.TELEGRAM from the decision contract. Persisted event payloads are opaque JSON and aggregate readers use only event type and selected count fields.
2. Delete unused presentation/contracts/transport.py and its exports. Keep ResponseEnvelope, ResponsePlan, presentation policy, evidence and verbalization contracts.
3. Generalize the assistant endpoint docstring and stale decision revision comment. Rename the integration test that describes transport independence.
4. Remove boundary scanner entries for the deleted bot source root and namespace; preserve actual module and Jev boundary checks.
5. Delete docs/telegram-bot.md and update README, API, architecture, query flow, integration seams, analytics, MVP, testing, test matrix, security, configuration, deployment, release evidence and relevant research docs.
6. Describe Web and future MAX as clients of Public API v1. Do not claim a bot runs or add a MAX package/configuration.
7. Preserve frontend-next/src/app/og/*, server-api.ts, render HMAC validation, image/render handlers, /assistant/query, ResponseEnvelope, DecisionContext, sessions, comparison, recommendations and admissions.
8. Do not change immutable university source snapshots or historical AIF Original Request records solely to remove text; classify any remaining hits as external evidence/history rather than product dependency.

### Required Interfaces and Contracts

- Public API response/session schemas remain unchanged except the removed telemetry enum member.
- ResponseEnvelope, ResponsePlan and Web OG rendering remain active.
- No SQL schema or migration depends on the telemetry source enum.

### Error Handling and Logging

- Removed enum values are rejected for new validated payloads.
- Historical opaque source strings are neither interpreted nor migrated.
- Existing OG HMAC verification remains fail-closed.

### Tests

- Run analytics contract/infrastructure tests.
- Run backend architecture tests including Jev and module boundary suites.
- Run docs/link and deployment contract checks.
- Search active source/docs for case variants, env prefix, dependency and deleted namespace.

### Acceptance Criteria

- No active transport implementation/configuration/docs/test/deploy/CI dependency remains.
- Shared response, Web, API and rendering functionality remains intact and testable.
- MAX appears only as a future client direction in documentation, not executable code.

### Verification

- python -m pytest -q tests/architecture tests/modules/decision/test_analytics.py tests/infrastructure/test_decision_analytics.py
- python scripts/check_docs.py
- rg -n -i 'telegram|TELEGRAM_|aiogram|andromeda_telegram' backend/src scripts .github deploy README.md docs SECURITY.md
- Expected: no live product integration dependency; classify immutable history/source evidence separately.

## Phase Risks and Mitigations

- Risk: removing a renderer breaks Web. Mitigation: preserve all frontend OG routes/HMAC flow and run frontend tests/build.
- Risk: removing a presentation export breaks assistant dependencies. Mitigation: remove only the unreferenced transport module and verify import sites/typing.
- Risk: old analytics payloads break readers. Mitigation: confirm source is opaque and never deserialized by aggregate readers.

## Phase Completion Checklist

- Task 8 and Task 9 acceptance criteria pass.
- Update completion status only in index.md.
