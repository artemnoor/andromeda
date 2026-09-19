# Phase 6: Recommendation and decision trust

Plan: [index.md](index.md)

Tasks: MVP-050, MVP-051, MVP-052, MVP-053

Depends on: MVP-004, MVP-031, MVP-033, MVP-040, MVP-041

Priority: P0

## Objective

Make recommendations useful, deterministic, honest about evidence, and
separate from the user's explicit decision. The existing Content Fit engine
and Admission Fit boundary are preserved. The work closes contract and UX
gaps; it does not introduce ML ranking or merge independent fit dimensions.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| Content Fit scoring | CONFIRMED | modules/recommendations/services/scoring.py uses subject .55, activity .25, distinctive .20, anti-interest penalty .60 with clamp/round |
| Deterministic ranking | CONFIRMED | modules/recommendations/services/ranking.py sorts by content fit, subject fit, program code, program ID |
| Admission separation in backend | CONFIRMED | modules/decision/services/candidates.py and admission_fit services keep Admission Fit separate from Content ranking; ineligible/insufficient partitions are explicit |
| Confidence output | PARTIALLY CONFIRMED | UserProfile confidence/confidence_by_dimension exists and affects adaptive selection, but recommendation output/ranking does not expose or use a result reliability contract |
| Provenance | CONFIRMED GAP | Recommendation contracts have source/evidence fields and decision response source_hashes, but suggestion mapping and frontend mapping can leave hashes/provenance absent |
| Missing data | PARTIALLY CONFIRMED | Decision pipeline reports missing tuition/location/constraints and source gaps; program/recommendation paths do not consistently explain excluded curriculum or unavailable metrics |
| Admission terminology | CONFIRMED UI issue | frontend-next/src/features/program/program-page.tsx labels Admission Fit as “Калькулятор шансов поступления” and seeds scores 85/82/88; backend policy says readiness/risk, not probability |
| Constraint effectiveness | CONFIRMED PARTIAL | DecisionCandidatePipeline marks max tuition and location as not applied when source data is absent, while frontend collects these as user constraints |
| Derived suggestions vs shortlist | CONFIRMED good boundary | DecisionContext and candidate pipeline keep explicit shortlist separate and use optimistic revision; preserve this behavior |

## Files to Change

| Future change | Path |
| --- | --- |
| Recommendation domain/contracts | backend/src/andromeda/modules/recommendations/{domain,contracts,services} |
| Decision candidate/explanation services | backend/src/andromeda/modules/decision/services/{candidates,explanations}.py |
| Admission fit contracts/mapper | backend/src/andromeda/modules/admission_fit and backend/src/andromeda/api/schemas |
| API mappings | backend/src/andromeda/api/routes/{recommendations,decision,admission_fit,programs}.py and schemas |
| Frontend mappers/types | frontend-next/src/lib/{api.ts,types.ts,generated.ts} |
| Recommendation/decision UI | frontend-next/src/features/{recommendations,decision,program,admission}; frontend-next/src/app/og/chances/route.tsx |
| Tests | backend/tests/modules/recommendations/, backend/tests/api/, frontend-next/tests/ |

## Task MVP-050: Define recommendation evidence, confidence, and provenance

### Intent

Ensure every recommendation can answer:

- why it ranked;
- which profile/catalog signals were used;
- which signals were inferred;
- what data was missing;
- how reliable the result is;
- which source run/hash supports the program facts.

### Implementation Steps

1. Extend the existing Recommendation/DecisionSuggestion public contracts
   additively with a typed evidence envelope rather than a generic dictionary.
2. Separate score components from evidence:
   subject fit, activity fit, distinctive fit, anti-interest penalty,
   profile confidence, catalog completeness, and source freshness.
3. Define a deterministic reliability calculation that does not silently
   change ranking unless product decision explicitly approves it. Initially
   expose reliability and use it for explanation/partition or tie policy only.
4. Carry source references from ProgramFingerprint and catalog reader through
   RecommendationService, DecisionCandidatePipeline, API mappers, and
   generated frontend types.
5. Mark activity signals as direct source evidence or inferred taxonomy
   mapping. Do not present inferred mapping as a curriculum fact.
6. Return structured missing-data items with blocking/degradable/
   informational severity.
7. Preserve stable ranking tie-breaks and one-cycle compatibility fields for
   existing clients.

### Required Interfaces and Contracts

- Content Fit score remains distinct from confidence/reliability.
- Admission Fit remains a separate OptionalMetric/status contract.
- Provenance fields are immutable references to source/run/hash, not raw
  content.
- Deterministic behavior holds for identical profile, catalog snapshot,
  taxonomy version, policy version, and source state.

### Error Handling and Logging

- If a claimed source-backed evidence field has no source reference, mark it
  unavailable and emit a validation diagnostic.
- Log policy version, taxonomy version, profile revision, catalog/run version,
  and result count; do not log full profile answers.
- Public errors must not expose source parser stack traces.

### Tests

- backend/tests/modules/recommendations/test_scoring.py
- backend/tests/modules/recommendations/test_ranking.py
- backend/tests/modules/recommendations/test_explanations.py
- backend/tests/modules/recommendations/test_reader_contract.py
- backend/tests/api/test_recommendations_contract.py
- backend/tests/api/test_decision_routes.py
- Add deterministic replay, confidence/provenance propagation, inferred
  activity labeling, missing-field severity, and no-source rejection tests.
- frontend-next/src/lib/api.test.ts must assert mappers preserve new fields;
  extend the existing API unit boundary rather than creating a duplicate
  frontend-next/tests/.

### Acceptance Criteria

- An API consumer receives score breakdown, explanation evidence, confidence/
  reliability, missing data, and provenance for each displayed candidate.
- No recommendation claims a reliability level that is not calculated from
  explicit signals.
- Same inputs produce byte-equivalent ordering and equivalent evidence.
- Existing Content Fit ranking remains unchanged unless a versioned policy
  decision says otherwise.

### Verification

- Replay BMSTU and HSE fixture catalogs with the same profile and compare
  outputs.
- Remove one signal/source at a time and verify only intended evidence,
  confidence, and missing-data fields change.
- Inspect generated OpenAPI and frontend type drift.

## Task MVP-051: Make fit semantics and product claims truthful

### Intent

Remove misleading placeholders and terminology while retaining useful
source-backed evidence. Career Fit and validated Workload Readiness remain
out of MVP unless the product scope is explicitly changed.

### Implementation Steps

1. Rename Admission Fit UI from “chance/probability” to readiness/risk/status
   language matching backend contracts and docs across every public/shareable
   surface, including frontend-next/src/features/program/program-page.tsx,
   frontend-next/src/features/recommendations/recommendations-page.tsx, and
   frontend-next/src/app/og/chances/route.tsx.
2. Remove hardcoded default EGE scores from
   frontend-next/src/features/program/program-page.tsx. Require explicit
   user input or show an untouched form state.
3. Validate subject score range, duplicate subjects, required offering, and
   empty/unknown score behavior in the UI and API.
4. Display not_available as “данных недостаточно” with reason/provenance,
   never as an empty score or a probable admission chance.
5. Separate workload evidence from Workload Readiness. Show curriculum
   semester evidence only when present and label unavailable semester data.
6. Make explanation fallback honest: “доказательств недостаточно” instead
   of “no contraindications” when no anti-fit evidence was computed.
7. Correct source copy from hardcoded BMSTU to the actual university label and
   source provenance.
8. Keep Career Fit/ML/guaranteed prediction outside the public capability
   matrix until real signals and validation exist.

### Required Interfaces and Contracts

- Existing AdmissionFitStatus values and risk/reason fields remain canonical.
- Missing/unknown is not a numeric zero.
- UI vocabulary is derived from typed status labels, not inferred by route.

### Error Handling and Logging

- Validation errors are local and accessible; server calculation errors show
  safe retryable state.
- Record no applicant score values in ordinary logs or analytics payloads.
- Analytics distinguishes user input validation, unavailable source, and
  calculation failure.

### Tests

- frontend-next/src/features/program/program-page.tsx tests or component
  tests for untouched defaults, validation, no offering, loading, error,
  insufficient data, and successful status.
- frontend-next/tests/admission-fit.spec.ts (create/update if the
  documented path is currently absent).
- backend/tests/api/test_admission_fit_contract.py and
  backend/tests/api/test_admission_fit_api.py.
- Add rendered/component and public/OG route regression coverage that no
  public text contains “chance/probability” for the readiness-only contract;
  include recommendation cards and the shareable OG route, not only the
  program page.

### Acceptance Criteria

- User never sees invented scores or a probability claim.
- Program, recommendation, and OG/share surfaces use the same truthful
  readiness/risk/status vocabulary; no stale probability copy remains.
- Admission Fit status/risk is explainable and separate from Content Fit.
- Missing data is useful and actionable.
- Product wording matches docs/mvp.md and the capability matrix.

### Verification

- Run mobile and desktop browser scenarios.
- Use BMSTU source-backed offering, HSE missing passing score, no-offering,
  and malformed input fixtures.
- Review rendered copy with a domain owner.

## Task MVP-052: Make decision constraints honest and effective

### Intent

Avoid collecting constraints that are silently ignored. Either implement a
source-backed comparison/filter or make the limitation explicit before the
user treats a candidate as satisfying it.

### Implementation Steps

1. Inventory DecisionConstraints fields and trace each through
   DecisionCandidatePipeline, admissions reader, canonical models, API, and
   frontend.
2. For tuition, normalize offering price/year/currency/form/funding into a
   comparable fact where source supports it. Apply max tuition only when
   comparable; otherwise classify as not evaluated with a clear action.
3. For location, use university/campus canonical location only where the
   source is authoritative. Do not infer commute or geography from free text.
4. For study form/funding/year, validate that filters are applied to the same
   offering identity used by Admission Fit.
5. Make each candidate explanation state applied, not applicable, or
   insufficient constraint data.
6. Preserve no-silent-prune policy: explicit shortlist is not removed when
   constraints or suggestions refresh.

### Required Interfaces and Contracts

- Constraint applicability is a typed decision outcome.
- Admission eligibility remains separate from Content Fit ranking.
- Source gaps preserve program visibility where the candidate can still be
  useful, but mark it as insufficient/ineligible rather than silently pass.

### Error Handling and Logging

- Invalid constraint combinations return typed 422 without leaking profile
  data.
- Log constraint version and applicability counts, not raw location strings
  if sensitive.
- A source inconsistency produces a safe source gap and operator diagnostic.

### Tests

- backend/tests/modules/decision/
- backend/tests/api/test_decision_routes.py and new decision contract tests
- backend/tests/integration/test_decision_persistence.py
- Add tuition/location/applicability, form/funding/year, no-silent-prune,
  and partial-source candidate tests.
- frontend-next/tests/decision-analytics.spec.ts and new constraints
  negative-state scenario.

### Acceptance Criteria

- Every user-entered constraint is either applied to a comparable fact or
  shown as not evaluated with a reason.
- Candidate partitions and Admission Fit statuses remain deterministic.
- Explicit shortlist/final choice cannot be changed by derived recomputation.

### Verification

- Run with BMSTU tuition/location facts, HSE partial facts, and no-source
  fixtures.
- Compare candidate sets and explanations before/after refresh and reload.
- Test anonymous and account-bound DecisionContext.

## Task MVP-053: Add recommendation regression and product-quality evaluation

### Intent

Prove that the recommendation contract is not elaborate decoration over too
few signals. Use deterministic fixtures and human-reviewable evidence without
claiming scientific validity from a small dataset.

### Implementation Steps

1. Define a versioned evaluation corpus with representative profiles,
   expected top-level thematic fit, anti-interest exclusions, source gaps,
   and admission separation.
2. Test invariants:
   deterministic ordering, no anti-interest violation, stable tie-break,
   admission does not alter Content ranking, no missing data becomes zero,
   and every reason references an actual signal/evidence or says unknown.
3. Add metamorphic tests: changing one profile answer changes only expected
   axes; removing a curriculum source reduces evidence/confidence rather than
   fabricating a reason.
4. Add a small manually reviewed explanation set with reviewer rationale.
5. Report coverage of critical business rules, not only line percentage.

### Required Interfaces and Contracts

- Evaluation cases reference canonical IDs and taxonomy/policy versions.
- Expected output tolerates intentional wording changes but asserts semantic
  evidence and partition.
- No ML or external career outcome claim is introduced.

### Error Handling and Logging

- Evaluation failure reports case ID, policy/source version, and mismatch
  class; no profile free text.
- Do not log full candidate catalogs in CI unless fixture-safe.

### Tests

- backend/tests/modules/recommendations/test_personas.py,
  test_penalties.py, test_candidate_ranking.py, test_empty_catalog.py,
  test_explanations.py
- backend/tests/modules/decision/test_proftest_projection.py
- Add recommendation regression corpus and replay test.

### Acceptance Criteria

- Critical ranking/explanation invariants are regression-tested.
- Confidence/provenance/missing-data behavior has negative cases.
- Evaluation can detect a complex contract being driven by an insufficient
  signal set.

### Verification

- Run on BMSTU and HSE fixture data.
- Review changed outputs with domain owner before changing policy weights.
- Record policy version and known limits in docs.

## Phase Risks and Mitigations

- **Risk:** confidence is mistaken for predictive accuracy. **Mitigation:**
  name it evidence reliability/completeness until validated outcomes exist.
- **Risk:** applying new constraints shrinks candidates unexpectedly.
  **Mitigation:** show applicability and preserve explicit shortlist.
- **Risk:** UI contract changes break Telegram/legacy clients. **Mitigation:**
  additive schema, generated-client drift gate, and one-cycle compatibility.

## Phase Completion Checklist

1. Recommendation output is explainable, deterministic, provenance-aware, and
   explicit about missing data.
2. Admission Fit is readiness/risk, not probability, and does not affect
   Content Fit ranking.
3. Collected decision constraints are applied or honestly marked unavailable.
4. Regression corpus covers critical scoring and explanation rules.
5. No Career Fit/Workload Readiness placeholder is presented as production
   capability.
