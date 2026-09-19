# Phase 7: Adaptive proftest production slice

Plan: [index.md](index.md)

Tasks: MVP-060, MVP-061, MVP-062, MVP-063

Depends on: MVP-003, MVP-050, MVP-053

Priority: P1

## Objective

Make the current compact adaptive proftest one coherent production path. Keep
the existing v3 design, typed session model, deterministic selection,
optimistic revision, stale question handling, and profile persistence. Migrate
legacy non-session endpoints deliberately instead of creating another test.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| Compact adaptive session | CONFIRMED backend | modules/proftest/services/session.py, adaptive.py, questions.py; v3 has five core questions and up to four bounded adaptive questions |
| Stop policy | CONFIRMED backend | AdaptiveQuestionSelector uses spread/stability/low-impact rules and typed stop reasons |
| Session persistence | CONFIRMED backend | ProftestAnswerSession model/repository has revision, expiry, status, staleQuestionIds, adaptive state, and bounded interaction count |
| Stale answer handling | CONFIRMED backend | ProftestSessionService clears/rebuilds adaptive answers after earlier core edit and tracks stale IDs |
| Legacy split | PARTIALLY CONFIRMED / tracer risk | modules/proftest/services/service.py and api/routes/proftest.py still expose non-session questions/preview/results alongside v3 session APIs |
| Frontend error/negative states | PARTIALLY CONFIRMED | frontend-next/src/features/proftest/proftest-page.tsx has happy-path loading/error text but no retry for restore/start/complete and no coverage for 409/expiry/malformed localStorage |
| Profile signal quality | PARTIALLY CONFIRMED | UserProfileBuilder creates deterministic dimensions/confidence, but no outcome/evaluation dataset proves signal usefulness beyond recommendation fixtures |
| Local draft | FUTURE RISK | frontend stores answer objects in localStorage and filters keys by prefix; malformed/stale payload recovery is only shallow |

## Files to Change

| Future change | Path |
| --- | --- |
| Session/domain policies | backend/src/andromeda/modules/proftest/{domain,contracts,services} |
| Proftest API schemas/routes | backend/src/andromeda/api/{schemas, routes}/proftest.py |
| Persistence | backend/src/andromeda/infrastructure/repositories/proftest_sessions.py and models |
| Recommendation handoff | backend/src/andromeda/modules/proftest/services/recommendation.py and decision projection |
| Frontend session UX | frontend-next/src/features/proftest/proftest-page.tsx |
| Tests | backend/tests/modules/proftest/, backend/tests/api/test_proftest*, backend/tests/integration/test_proftest*, frontend-next/tests/proftest*.spec.ts |

## Task MVP-060: Make the session path canonical and migrate legacy endpoints

### Intent

Prevent two proftest implementations from diverging in question semantics,
scoring, profile persistence, and recommendation mapping.

### Implementation Steps

1. Inventory consumers of /proftest/questions, /preview, /results and all
   /proftest/sessions endpoints, including frontend, Telegram, tests, and
   documented URLs.
2. Decide whether legacy endpoints become thin adapters over the v3 session
   service or remain explicitly compatibility-only for one release.
3. If adapting, map old request/response contracts without reimplementing
   profile scoring or ranking.
4. Keep v2 session rows readable during the migration; pin question-set
   version and make any rebuild behavior explicit.
5. Add deprecation metadata and a removal date/condition for old endpoints.
6. Update frontend and docs to start/resume only the canonical session flow.

### Required Interfaces and Contracts

- One UserProfileBuilder and one ranking/recommendation handoff owns scoring.
- Session version and question set version are explicit.
- Existing clients receive stable safe errors during the transition.
- Restart creates a new session or explicit reset; it must not mutate a
  completed historical session unexpectedly.

### Error Handling and Logging

- Compatibility requests log endpoint version and migration mapping without
  logging answers.
- Unknown question-set versions fail closed with a user-retryable message and
  operator diagnostics.
- Deprecated endpoint use is sampled/bounded to avoid log floods.

### Tests

- backend/tests/api/test_proftest_contract.py
- backend/tests/api/test_proftest_sessions_api.py
- backend/tests/api/test_proftest_profile_contract.py
- backend/tests/integration/test_proftest_vertical_slice.py
- Existing legacy compatibility tests and new adapter parity tests.

### Acceptance Criteria

- There is one scoring/profile/recommendation implementation.
- Legacy endpoint behavior is either parity-proven or explicitly labeled
  compatibility with a bounded removal condition.
- Current and completed sessions remain readable through the migration.

### Verification

- Replay frozen v2/v3 session fixtures and compare profiles/recommendation
  semantics.
- Run API and frontend legacy-flow compatibility tests.
- Run strict mypy.

## Task MVP-061: Validate signal usefulness and adaptive determinism

### Intent

Ensure the short test collects enough signal for a responsible first
recommendation, while removing complexity that does not improve evidence.

### Implementation Steps

1. Define signal coverage per core/adaptive question: dimensions affected,
   profile fields, score components, and explanation evidence.
2. Build a versioned persona corpus with clear expected broad preferences,
   anti-preferences, uncertainty, and catalog-sparse cases.
3. Add deterministic tests for question order, tie-breaking, answer edit,
   stability threshold, minimum spread, insufficient candidates, source gap,
   and maximum interactions.
4. Measure whether adaptive questions change ranking/evidence enough to
   justify being asked; do not optimize solely for fewer questions.
5. Keep stop reasons user-visible and map them to evidence state.
6. Verify confidence is a bounded completeness/reliability signal, not an
   unsupported psychological or career claim.

### Required Interfaces and Contracts

- Same session state and catalog snapshot produce same next question/result.
- Adaptive selection reads typed profile/catalog ports only.
- Questions carry component, dimension, stage, version, and evidence effect.

### Error Handling and Logging

- Log session ID hash, question-set version, selection reason, and stop reason;
  never answer text or personal free-form input.
- If catalog is insufficient, return a useful preliminary profile plus explicit
  source gap rather than fabricate adaptive confidence.

### Tests

- backend/tests/modules/proftest/test_adaptive.py
- backend/tests/modules/proftest/test_session_policy.py
- backend/tests/modules/proftest/test_questions.py
- backend/tests/modules/proftest/test_user_profile.py
- backend/tests/modules/proftest/test_recommendation_delegation.py
- Add persona/regression/metamorphic tests and result evidence assertions.

### Acceptance Criteria

- Test length is bounded by the documented product copy.
- Adaptive questions are selected only when they can affect a known decision.
- Stop reason and profile confidence are deterministic and explainable.
- Sparse/unknown source state never appears as false certainty.

### Verification

- Run the persona corpus with BMSTU, HSE, mixed, empty, and partial catalogs.
- Compare recommendations before/after one controlled answer change.
- Review output with the recommendation contract from MVP-050.

## Task MVP-062: Harden persistence, resume, restart, and frontend UX

### Intent

Make session recovery reliable for real users and multiple tabs, not only the
happy path covered by current tests.

### Implementation Steps

1. Add explicit frontend states for intro, loading, unavailable session,
   expired session, conflict, stale answer, save failure, complete failure,
   and successful result.
2. Add retry/refresh actions for restore/start/complete failures and preserve
   only validated local draft data.
3. Handle 409 by fetching authoritative session state and clearly explaining
   which answer state was retained.
4. Clear or migrate localStorage draft when question-set version or session
   scope changes; never persist profile/session secrets.
5. Add expiration handling and safe restart/resume semantics.
6. Ensure account transfer behavior is visible after completion and does not
   silently mutate explicit shortlist.
7. Keep question history/stale IDs consistent across browser reload and
   backward navigation.

### Required Interfaces and Contracts

- Revision is required on writes and stale writes return typed conflict.
- Session expiry is distinct from no current session.
- Local draft is a UX cache, not authoritative persistence.
- Completed profile/recommendation handoff uses profile revision and decision
  context revision.

### Error Handling and Logging

- User-facing messages distinguish retryable transport, session conflict,
  expired session, and invalid answer.
- Log only hashed/session-safe identifier, revision, endpoint stage, and safe
  status.
- Do not send raw localStorage payload or answer text to analytics.

### Tests

- frontend-next/tests/proftest.spec.ts
- frontend-next/tests/proftest-decision-integration.spec.ts
- frontend-next/tests/auth-guest.spec.ts
- Add cases for 409, expiry, timeout, malformed localStorage, refresh during
  save, failed complete, restart, mobile viewport, and screen-reader labels.
- backend/tests/infrastructure/test_proftest_sessions_repository.py
- Add API tests for expired/revision/stale/duplicate start.

### Acceptance Criteria

- User can reload, resume, recover from conflict, or restart without losing
  authoritative answers unexpectedly.
- Every failed write has a retry or explicit safe recovery path.
- No stale local draft can overwrite a newer server session.
- Mobile and keyboard flows remain usable.

### Verification

- Run Chromium E2E on desktop and 390px mobile.
- Run two browser contexts against the same anonymous session for conflict.
- Inspect browser storage and network logs for secret leakage.

## Task MVP-063: Connect proftest evidence to recommendation and decision

### Intent

Ensure the user can understand how proftest answers influenced the profile
and candidate explanations without treating a quiz as a validated diagnosis.

### Implementation Steps

1. Carry profile revision, question-set/policy version, and signal evidence
   references into recommendation context.
2. Show changed dimensions and confidence/completeness in results, not raw
   answer text unless explicitly intended by product copy.
3. Link each result reason to a profile signal and catalog evidence.
4. Show missing data/source gaps that limited adaptive selection or result.
5. Keep explicit shortlist and final choice unchanged by profile completion.
6. Track safe analytics for test started, completed, stopped, conflict,
   retry, and handoff, with bounded IDs.

### Required Interfaces and Contracts

- Proftest profile is input to recommendation, not a new decision owner.
- Decision context owns explicit choice; proftest only refines derived
  suggestions.
- Provenance and confidence remain separate fields.

### Error Handling and Logging

- Handoff failure must show profile saved vs recommendations unavailable as
  two distinct states.
- Analytics must not contain answers or sensitive free text.
- Log profile revision and recommendation run version only.

### Tests

- backend/tests/modules/decision/test_proftest_projection.py
- backend/tests/api/test_proftest_profile_api.py
- frontend-next/tests/proftest-decision-integration.spec.ts
- Add no-shortlist-mutation and evidence-link tests.

### Acceptance Criteria

- Results explain which profile dimensions affected candidate evidence.
- Missing source/catalog data is visible and not confused with low user
  confidence.
- Completion never changes explicit shortlist automatically.

### Verification

- Complete sessions with each persona and partial catalog fixture.
- Compare decision context before/after completion.
- Validate generated OpenAPI/client mappings.

## Phase Risks and Mitigations

- **Risk:** legacy clients depend on old response shapes. **Mitigation:**
  adapter facade and contract tests for one release.
- **Risk:** more UX states increase frontend complexity. **Mitigation:** use
  typed state machine/centralized API error mapping, not duplicated flags.
- **Risk:** users overinterpret confidence. **Mitigation:** label it profile
  evidence completeness and document limitations.

## Phase Completion Checklist

1. Session path is canonical and old endpoints have bounded compatibility.
2. Adaptive behavior is short, deterministic, and signal-evaluated.
3. Resume/restart/stale/expiry/conflict flows are production-usable.
4. Proftest evidence reaches recommendations without mutating decisions.
5. Browser tests cover negative states and mobile/accessibility basics.
