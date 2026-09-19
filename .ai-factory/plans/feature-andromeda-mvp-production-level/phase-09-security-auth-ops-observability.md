# Phase 9: Security, auth, operations, and observability

Plan: [index.md](index.md)

Tasks: MVP-080, MVP-081, MVP-082, MVP-083

Depends on: MVP-020, MVP-023, MVP-041, MVP-042, MVP-050, MVP-071

Priority: P0 for public exposure; P1 for operational maturity

## Implementation status

Implemented. The baseline findings below describe the pre-implementation
state. Current code includes centralized origin/rate/error controls, auth
lifecycle cleanup/concurrency coverage, diagnosable Admin/Ops retry UX, health
and readiness checks, request timing/correlation logging, and bounded Telegram
retry behavior. A clean remote CI and production-like deployment drill remain
release evidence rather than unimplemented architecture.

## Objective

Complete an MVP security and operational baseline around the existing
Argon2/opaque-session architecture. Preserve anonymous profile scope,
account precedence, explicit transfer semantics, admin isolation, and
production-oriented ingestion operations.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| Password hashing | CONFIRMED good baseline | infrastructure/security/passwords.py uses Argon2id with explicit parameters; tests cover it |
| Opaque cookies/isolation | CONFIRMED good baseline | api/dependencies/profile_session.py and auth_session.py store hashes, use HttpOnly/SameSite/Secure policy, and define account/session scope |
| Anonymous to account precedence | CONFIRMED | AuthenticationService and auth/profile tests cover account profile wins and explicit guest import |
| Auth abuse controls | CONFIRMED GAP / future risk | auth services/repositories/API routes have no password/login/register rate limit or lockout |
| CSRF/trusted origin | PARTIALLY CONFIRMED | auth state-changing routes use trusted-origin policy; broader cookie-authenticated decision/proftest/profile mutations require explicit review |
| Admin API | PARTIALLY CONFIRMED | API-key compare_digest, disabled-by-default/safe 404, run detail and safe errors exist; retry is BMSTU-only and concurrency is weak |
| Ingestion diagnostics | PARTIALLY CONFIRMED | run IDs/stages/logs exist; optional gaps, stale runs, alerting, and crash recovery need improvement |
| Request correlation/timing | PARTIALLY CONFIRMED | api/main.py correlation middleware echoes/creates ID and security headers exist; no robust validation/timing/exception reporting/metrics baseline |
| Health/readiness | CONFIRMED GAP | health routes check process/DB/table presence but not migration head or external dependency status |
| SSRF/PDF | CONFIRMED GAP | adapter allowlists/fetch controls are incomplete for final redirects/private targets and parser resource limits |
| CORS | FALSE POSITIVE as blanket issue | explicit configured origins and credential policy exist; keep tests, verify production origin |

## Files to Change

| Future change | Path |
| --- | --- |
| Auth/security dependencies | backend/src/andromeda/api/dependencies/{auth_session,profile_session,request_context}.py |
| Auth domain/repository | backend/src/andromeda/modules/auth, backend/src/andromeda/infrastructure/repositories/auth.py |
| API middleware/routes | backend/src/andromeda/api/main.py and routes |
| Ingestion security | backend/src/andromeda/ingestion and Phase 3 paths |
| Admin ops | backend/src/andromeda/modules/admin_ops, api/routes/admin_ops.py, infrastructure/repositories/ingestion.py |
| Observability | backend/src/andromeda/infrastructure/logging, api/main.py, health routes, run services |
| Security tests/config | backend/tests/auth/, backend/tests/api/, backend/tests/security/ (new if required), CI |
| Telegram operational surface | telegram-bot/src/andromeda_telegram/{config.py,clients/backend.py}, deploy/yc/compose.yaml |

## Task MVP-080: Complete public security baseline

### Intent

Protect cookie-authenticated mutations, admin/source operations, parsers, and
deployment configuration against realistic MVP threats without building a
compliance platform.

### Implementation Steps

1. Trace every state-changing endpoint: auth, profile, proftest, decision,
   admin, analytics, and ingestion.
2. Apply a consistent trusted-origin/CSRF policy to browser cookie mutations.
   Decide whether Origin validation is sufficient for same-site deployment or
   a synchronizer token is required; document non-browser exceptions.
3. Add bounded rate limits/abuse controls for login, registration, password
   verification, session creation, proftest start/complete, and ops retry.
   Use a deployment-appropriate store or explicit single-replica limitation.
4. Add admin key rotation/operational policy, safe failure equivalence, and
   no key values in logs/response.
5. Complete SSRF/final redirect/private IP and PDF/file resource controls from
   MVP-020/MVP-024.
6. Review CORS, cookie, HSTS, CSP, trusted origins, and Telegram internal
   endpoints for staging/production configuration.
7. Run dependency vulnerability scans for backend, frontend, Telegram, and
   system parser/browser dependencies; triage rather than blindly upgrade.
8. Verify SQL is parameterized through repositories and user inputs are
   schema/range validated.

### Required Interfaces and Contracts

- Security policy is centralized/configured, not duplicated in routes.
- Auth isolation and account precedence remain unchanged.
- Rate-limit response is a safe 429 with Retry-After where appropriate.
- No user-provided URL can control arbitrary ingestion target.

### Error Handling and Logging

- Log security event class, safe subject hash/session scope, route, and
  correlation ID; never password, token, cookie, raw profile, or API key.
- Do not reveal whether an email/account exists in auth error responses.
- SSRF/block/parser errors are safe public errors plus operator details.

### Tests

- backend/tests/auth/
- backend/tests/api/test_auth_api.py
- backend/tests/api/test_admin_ops_api.py
- backend/tests/api/test_proftest_sessions_api.py
- decision/profile mutation API tests
- New security tests for CSRF/origin, rate limits, lockout, cookie flags,
  CORS, SSRF redirects/private IP, PDF limits, sensitive log redaction,
  SQL input validation, and ops key brute-force behavior.

### Acceptance Criteria

- Browser cookie mutations cannot be forged cross-site under supported
  deployment modes.
- Sensitive endpoints have bounded abuse protection or an explicit,
  documented single-replica limitation with compensating control.
- SSRF, oversized/malformed PDF, secret logging, and admin-key paths are
  covered by negative tests.
- Existing Argon2, opaque session, isolation, and transfer behavior remains
  green.

### Verification

- Run security tests on test and staging-like configuration.
- Inspect response headers/cookies with a browser/API client.
- Run dependency audit and record accepted/mitigated findings.

## Task MVP-081: Verify auth lifecycle and privilege boundaries

### Intent

Turn the existing good auth model into a fully tested lifecycle:
anonymous → account registration/login → explicit transfer/bind → logout/
expiration/concurrency, with no cross-scope data leak.

### Implementation Steps

1. Document lifecycle state transitions for anonymous profile, auth session,
   account profile, decision context, proftest session, and Telegram scope.
2. Test account precedence, no implicit merge, explicit guest import, logout,
   expiration, revoked session, concurrent sessions, and malformed cookies.
3. Review registration/login transaction boundaries for duplicate account,
   session binding, and partial failure.
4. Define retention/cleanup for expired sessions, profiles, proftest answers,
   and ingestion run detail.
5. Add privilege matrix for public, authenticated account, operator, and
   internal Telegram calls.
6. Ensure frontend copy explains transfer outcome and does not imply anonymous
   state was merged when account state won.

### Required Interfaces and Contracts

- ProfileScope and account identity remain separate typed concepts.
- Account state precedence is deterministic and visible in AuthSession response.
- Admin/operator access never derives from a user account cookie.
- Telegram transport scope does not grant admin privileges.

### Error Handling and Logging

- Log lifecycle transition class and correlation ID only.
- Expired/revoked/malformed session returns safe unauthenticated state and
  rotates/clears cookies as designed.
- Never log account email, password, tokens, or full profile.

### Tests

- backend/tests/auth/
- backend/tests/api/test_auth_api.py
- backend/tests/integration/test_postgresql_user_profile.py
- backend/tests/integration/test_account_transfer.py if present/new
- frontend-next/tests/auth-guest.spec.ts
- Add two-browser-context and concurrent-session scenarios.

### Acceptance Criteria

- Anonymous and authenticated data are isolated and transfer semantics are
  explicit.
- Logout/expiration/revocation are effective for API access.
- Duplicate/concurrent registration/login cannot bind wrong profile.
- Operator and Telegram privilege boundaries are tested.

### Verification

- Run SQLite fast tests and PostgreSQL lifecycle tests.
- Inspect database rows only in disposable test DB, with secrets excluded
  from artifacts.

## Task MVP-082: Complete admin/ops ingestion control plane

### Intent

Preserve production-oriented operations architecture while making every run
diagnosable for BMSTU and HSE and removing UI/backend contract drift.

### Implementation Steps

1. Align admin API schemas, UI, docs, and actual retry profiles.
2. Add HSE support or explicitly mark it unavailable with an operator reason;
   do not show a generic retry control that only handles BMSTU.
3. Add run list/detail fields for source profile, stage, quality decision,
   gaps, counts, hashes, previous-good run, retry ancestry, and recovery.
4. Add operator confirmation for mutating retry and explicit conflict/error
   handling in frontend-next/src/features/ops/ops-page.tsx.
5. Remove demo-key fallback from the ops UI and require configured key flow.
6. Add audit trail for operator action/result without raw body or secret.
7. Define retention and safe redaction for run details.

### Required Interfaces and Contracts

- Admin API exposes safe run state machine and typed errors.
- Retry request remains allowlisted and idempotent.
- Public users never see operator raw source or credentials.

### Error Handling and Logging

- Each run stage/error has stable code/message and run ID.
- Operator actions log source profile and outcome; no API key.
- UI distinguishes unavailable ops, wrong key, conflict, failed run, and
  retry accepted.

### Tests

- backend/tests/api/test_admin_ops_api.py
- backend/tests/integration/test_admin_ops_vertical_slice.py
- frontend-next/src/features/ops/ops-page.tsx tests and browser scenario
- Add BMSTU/HSE retry, confirmation, wrong key, stale run, and safe detail
  tests.

### Acceptance Criteria

- Any ingestion run can be diagnosed from admin detail and logs.
- Retry behavior matches backend/docs/UI for every supported profile.
- Failed runs preserve safe error and quality context.
- No operator UI default secret/key is present.

### Verification

- Run a successful, failed, rejected, concurrent, and retried run.
- Inspect admin payload/log artifacts for safe disclosure.
- Execute through staging-like deployment with configured key only.

## Task MVP-083: Establish minimal observability baseline

### Intent

Make MVP failures diagnosable without building enterprise observability:
structured request logs, run IDs, timing, safe exception reports, health/
readiness, DB/migration state, and external source failures.

### Implementation Steps

1. Define structured log fields:
   timestamp, level, service, environment, correlation ID, request method/
   route, status, duration, run ID, university, stage, error code, and
   migration revision where relevant.
2. Validate/sanitize incoming correlation IDs before echoing; generate one
   when absent.
3. Add bounded request timing and service/ingestion stage durations.
4. Add exception reporting hook or structured error event with redaction.
   Avoid sending sensitive payloads to external systems by default.
5. Expand health readiness to report DB connectivity, migration compatibility,
   and safe required runtime dependency status; keep live independent.
6. Add source failure metrics/alerts or durable artifacts for scheduled
   source health.
7. Define log retention, sampling, and correlation lookup runbook.
8. Add Telegram backend health/retry/backoff and align ports/env names.

### Required Interfaces and Contracts

- Correlation ID is safe opaque bounded string and returned consistently.
- Health response distinguishes live, ready, dependency degraded, and
  source-health status.
- Ingestion run ID is stable across API/log/admin artifacts.
- Observability adapters remain outer infrastructure concerns.

### Error Handling and Logging

- Structured logs are machine-readable; no raw request/response body,
  cookies, password, API key, DB URL, or profile answer.
- Error events preserve root cause class and safe code.
- Timing instrumentation cannot block request or ingestion completion.

### Tests

- new backend/tests/api/test_health.py
- backend/tests/api/test_request_context.py or new middleware tests
- backend/tests/integration/test_admin_ops_vertical_slice.py
- Add correlation validation, timing presence/bounds, exception redaction,
  migration-behind readiness, DB-unavailable readiness, source failure
  artifact, and Telegram retry/port tests.
- Add CI artifact upload for safe logs/results.

### Acceptance Criteria

- An operator can correlate a user request, recommendation result, or
  ingestion failure across API logs, run detail, and UI error.
- Readiness cannot pass on stale schema or unavailable database.
- External source failures produce durable diagnostic evidence.
- Logs are structured, redacted, and bounded.

### Verification

- Inject API 4xx/5xx, DB disconnect, source timeout/parser failure, and
  migration mismatch.
- Inspect logs and health responses in staging-like deployment.
- Run a restore/smoke sequence using the operations runbook.

## Phase Risks and Mitigations

- **Risk:** rate limiting requires shared state in multi-replica deployment.
  **Mitigation:** keep single-replica constraint explicit for MVP or add a
  small shared store only when deployment requires it.
- **Risk:** observability leaks profile data. **Mitigation:** allowlist fields,
  redaction tests, and review artifacts.
- **Risk:** health checks create false external dependency outages.
  **Mitigation:** keep live/ready/source health separate and define timeouts.

## Phase Completion Checklist

1. Realistic MVP threats are covered by controls and negative tests.
2. Auth lifecycle/isolation/transfer/privilege boundaries are proven.
3. Admin can diagnose and safely retry BMSTU/HSE supported runs.
4. Correlation, timing, run IDs, health, readiness, and source failures are
   operationally visible without sensitive logging.
5. Telegram internal contract is consistent and has bounded retry behavior.
