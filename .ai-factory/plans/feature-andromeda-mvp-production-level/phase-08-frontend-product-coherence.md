# Phase 8: Frontend product coherence and user-state quality

Plan: [index.md](index.md)

Tasks: MVP-070, MVP-071, MVP-072, MVP-073

Depends on: MVP-001, MVP-050, MVP-051, MVP-052, MVP-060, MVP-062

Priority: P1

## Implementation status

Implemented. The baseline findings below are retained as audit evidence; the
current implementation is covered by `frontend-next/tests/`, typed client
tests, `npx tsc --noEmit`, lint/build, OpenAPI drift, and the canonical browser
flow. Product-visible gaps now have explicit loading/error/empty/partial
states; remaining release evidence is deployment/CI execution, not a planned
frontend rewrite.

## Objective

Turn existing frontend screens into one coherent applicant funnel:

interest/source data → initial candidates → shortlist → comparison →
detailed explanation → admission reality → decision.

Keep the frontend as a consumer of public typed contracts. Do not leak
backend bounded-context vocabulary into user copy and do not create a new
frontend/backend context merely to connect screens.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| Route coverage | CONFIRMED | frontend-next/src/app/page.tsx routes catalog, program, decision, compare, proftest, admission, recommendations, events, personal route, account, ops |
| Typed client boundary | PARTIALLY CONFIRMED | src/lib/generated.ts and openapi.json exist; src/lib/api.ts has manual mappers, Record<string, any>, no runtime schema validation, and can drop provenance/details |
| Shared loading/error components | CONFIRMED baseline | src/components/shared.tsx exposes Loading, ErrorState, EmptyState; catalog/decision/compare use them unevenly |
| Program detail partial data | CONFIRMED gap | features/program/program-page.tsx loads program, curriculum, and admissions via Promise.all; any missing part fails whole screen; empty curriculum/admissions are weakly explained |
| Misleading program source/fit copy | CONFIRMED | program-page.tsx says sources are BMSTU, labels Admission Fit as chance calculator, and initializes scores 85/82/88 |
| Recommendation fallback | CONFIRMED gap | recommendations-page.tsx falls back to legacy endpoint when decision suggestions fail; a service error can appear as profile absence; “no contraindications” can be shown without evidence |
| Compare inconsistency | PARTIALLY CONFIRMED | ComparePage supports 2–3 in summary but detail API is A/B; summary has retry while detail error does not retry; C is not represented in detail |
| Product test coverage | PARTIALLY CONFIRMED | 13 frontend unit tests and multiple E2E files exist; docs mention admissions.spec.ts/recommendations.spec.ts/admission-fit.spec.ts but those exact files are not all present |
| Responsive/accessibility | PARTIALLY CONFIRMED | several viewport E2E checks and aria labels exist; full keyboard/screen-reader/partial-state matrix is not demonstrated |

## Files to Change

| Future change | Path |
| --- | --- |
| API boundary | frontend-next/src/lib/api.ts, types.ts, generated.ts/openapi.json |
| Global routing/state | frontend-next/src/app/page.tsx, features/decision/decision-context.tsx |
| Product pages | frontend-next/src/features/{catalog,program,decision,compare,admission,recommendations,proftest} |
| UI primitives/copy | frontend-next/src/components/shared.tsx, src/lib/labels.ts |
| Browser/unit tests | frontend-next/tests/, src/**/*.test.ts(x) |
| Documentation | docs/testing.md, docs/mvp-capability-matrix.md, README.md |

## Task MVP-070: Implement the coherent funnel over existing contexts

### Intent

Make the user experience feel like one decision product while leaving domain
ownership in decision, recommendation, admission_fit, comparison, programs,
and proftest modules.

### Implementation Steps

1. Define route transitions and data preconditions for the five user flows.
2. Make catalog/program detail the source-backed exploration entrypoint.
3. Make proftest optional refinement, not mandatory for catalog/admission.
4. Make decision context the owner of explicit shortlist, roles, final choice,
   revisions, and account transfer.
5. Make recommendations show derived candidates with accept/reject actions,
   not auto-mutation.
6. Make comparison accept shortlist/program IDs consistently and represent
   the selected set honestly.
7. Make admission view use the same program/offering identity and link back to
   explanation, shortlist, and comparison.
8. Add explicit breadcrumb/back/funnel links without duplicating API state.

### Required Interfaces and Contracts

- Route state contains canonical program IDs; no display names are used as
  identity.
- DecisionContext remains the only client owner of shortlist state.
- APIs are called through typed src/lib/api.ts functions.
- Flow transitions preserve profile/decision revision and source state.

### Error Handling and Logging

- A failed derived recommendation refresh does not erase or replace a valid
  explicit decision context.
- Navigation after a partial API response preserves the user-visible source
  gap.
- Analytics event names remain typed/allowlisted and exclude free-form
  profile data.

### Tests

- frontend-next/tests/catalog-programs.spec.ts
- frontend-next/tests/decision-analytics.spec.ts
- frontend-next/tests/proftest-decision-integration.spec.ts
- frontend-next/tests/legacy-flow-compat.spec.ts
- Add one end-to-end funnel test from catalog or proftest to final choice.

### Acceptance Criteria

- A user can complete discover → shortlist → compare → final choice without
  proftest.
- A user can use proftest to refine suggestions without silent shortlist
  mutation.
- Every screen has an obvious next action and a path to recover from missing
  data.
- UI copy speaks in applicant terms, not repository module names.

### Verification

- Run desktop/mobile E2E with anonymous and authenticated/account-transfer
  scenarios.
- Review network calls to confirm no endpoint bypasses typed API boundary.
- Compare explicit state before/after derived refresh.

## Task MVP-071: Normalize loading, error, empty, stale, and partial states

### Intent

Prevent a network error from looking like no profile, and prevent an empty
source-backed result from looking like a broken UI.

### Implementation Steps

1. Define a typed screen state model: loading, loaded, empty-valid,
   partial-with-gaps, unavailable-retryable, unavailable-terminal,
   stale-with-refresh, and conflict.
2. Apply it to catalog, program detail, recommendations, decision,
   comparison, admission, proftest, events, campus/personal route, and ops.
3. Replace Promise.all failure coupling in program detail with independent
   program/curriculum/admission states; a missing curriculum must not hide
   program facts.
4. Preserve stale data while a refresh is in progress, with a visible
   freshness indicator and retry.
5. Ensure every error state has a safe message, retry or next action, and
   accessible live-region behavior.
6. Distinguish not_available, no records, source gap, and API failure.
7. Remove legacy fallback that maps decision service failure to ProfileRequired
   unless the API explicitly returns no profile.

### Required Interfaces and Contracts

- State mapping uses typed ApiError/status and response status/sourceGaps.
- Null/unknown values remain distinct from numeric zero.
- Backend error codes are mapped in one boundary helper, not per component.

### Error Handling and Logging

- User-visible messages do not include stack traces or internal paths.
- Client diagnostics use request/correlation ID when provided and never
  persist cookies or profile answers.
- A retry does not duplicate mutation; reads may be deduplicated.

### Tests

- Unit tests for API error/state mappers in frontend-next/src/lib.
- E2E negative cases for 404/422/409/500/timeout and empty/partial fixture.
- Program detail tests for program-only, curriculum-only missing,
  admissions-only missing, all-empty, and retry.
- Recommendation tests for decision endpoint failure vs no profile.

### Acceptance Criteria

- Every critical screen has explicit loading, error, empty, and partial
  behavior.
- API/service failure never masquerades as a missing user profile.
- Source gaps and unavailable metrics are understandable and actionable.
- Stale data is never silently presented as freshly ingested.

### Verification

- Use an API mock/server that returns each status and a partial fixture.
- Run browser assertions for visible copy, retry, no data loss, and ARIA live
  regions.
- Test refresh during navigation and on mobile.

## Task MVP-072: Fix semantics, accessibility, responsive layout, and copy

### Intent

Make product claims accurate and the interface usable by an applicant on
mobile/keyboard/screen-reader paths.

### Implementation Steps

1. Apply MVP-051 terminology and remove hardcoded input defaults.
2. Fix university/source labels using response metadata rather than BMSTU
   constants.
3. Render provenance/source gap details with human-readable labels and
   expandable detail, without exposing raw source payload.
4. Audit every interactive control for label, focus, keyboard order, disabled
   reason, live status, and error association.
5. Test small screens for tables, comparison charts, forms, and long program
   names; keep no-horizontal-overflow assertions.
6. Add visible freshness/source timestamp where stale data matters.
7. Ensure color is not the only Admission/quality status signal.

### Required Interfaces and Contracts

- Copy is driven by typed status/metric labels.
- External provenance links are safe, target-blank policy is consistent, and
  unsafe/redirected URLs are not rendered blindly.
- Accessibility attributes remain valid after loading/partial transitions.

### Error Handling and Logging

- Client-side validation messages do not expose server internals.
- Analytics records action/error class, not input values or answer text.
- External link failures do not crash the detail screen.

### Tests

- Add component tests for status labels, source links, gaps, and metric
  unknowns.
- E2E at 390px and desktop for catalog, program, admission, recommendation,
  comparison, and proftest.
- Add keyboard-only smoke and axe/accessibility check if toolchain permits.

### Acceptance Criteria

- No product-visible placeholder is phrased as a completed capability.
- No hardcoded applicant score is submitted without user action.
- Critical user paths are keyboard reachable and responsive.
- Unknown/partial states remain distinguishable visually and textually.

### Verification

- Run frontend lint, build, unit, and browser checks.
- Inspect rendered screens with accessibility tooling and manual keyboard
  traversal.
- Confirm source URL rendering cannot become an open redirect/unsafe target.

## Task MVP-073: Harden generated OpenAPI/client boundary

### Intent

Prevent contract fields such as provenance, confidence, gaps, and status from
being lost in manual mapping and prevent permissive any types from hiding
schema drift.

### Implementation Steps

1. Make one canonical OpenAPI export/check command that works either against
   a started backend or a tracked generated specification.
2. Generate/update frontend-next/openapi.json and src/lib/generated.ts only
   from the backend export.
3. Replace Record<string, any> mappers with typed generated input/output or
   narrow unknown parsing.
4. Add runtime validation at the network boundary only if it can reuse
   generated schemas without creating a second contract source.
5. Add contract tests for all critical fields and null/unknown semantics.
6. Version/additively migrate new recommendation/provenance fields.
7. Ensure Telegram/client consumers use the same API status/error semantics.

### Required Interfaces and Contracts

- OpenAPI is the public wire contract.
- Generated client/types are derived artifacts with a drift check.
- Manual adapters cannot drop fields silently.
- JSON wire compatibility is tested separately from Python model construction:
  accepted string enum values remain accepted at the HTTP boundary and invalid
  values remain rejected.

### Error Handling and Logging

- Schema mismatch identifies operation and field, not raw response body.
- Network errors preserve status/correlation metadata safely.
- Debug API logging remains disabled by default in production.

### Tests

- frontend-next/scripts/check-api-drift.mjs
- frontend-next/src/lib/api.test.ts
- backend/tests/api/ contract suites
- Add generated-field preservation tests for recommendation, decision,
  admission, comparison, proftest, and program detail.
- Add wire-level JSON regressions for representative string enum values in
  proftest answer status and decision/analytics/admission contracts; valid
  JSON strings must be accepted through the HTTP boundary, while invalid
  values still return 422. Exercise at least one case through the generated
  client or a real JSON payload.
- Run npm run check-api-drift with OPENAPI_FILE=openapi.json and with a live
  backend as separate checks; document prerequisites.

### Acceptance Criteria

- Drift check is runnable from a clean checkout with documented setup.
- Critical response fields survive backend → generated types → api.ts →
  component.
- No broad any mapper remains on critical flows without explicit justification.
- A backend schema change fails CI until the generated client is updated.

### Verification

- Export OpenAPI, run drift, typecheck/build, unit, and E2E.
- Test a server returning additional/missing/unknown fields.
- Inspect generated diff for secrets or internal implementation details.

## Phase Risks and Mitigations

- **Risk:** richer evidence overloads users. **Mitigation:** summary-first
  cards, expandable evidence, clear severity, and source links.
- **Risk:** independent partial states cause inconsistent screen combinations.
  **Mitigation:** typed screen-state helpers and scenario tests.
- **Risk:** generated runtime validation adds bundle cost. **Mitigation:**
  scope validation to API boundary/critical routes and measure build impact.

## Phase Completion Checklist

1. Five flows read as one user journey while context ownership remains intact.
2. All critical screens distinguish loading/error/empty/partial/stale states.
3. Admission and recommendation copy matches actual contracts.
4. Mobile/accessibility behavior is tested, not assumed.
5. Generated OpenAPI/client boundary preserves critical fields.
