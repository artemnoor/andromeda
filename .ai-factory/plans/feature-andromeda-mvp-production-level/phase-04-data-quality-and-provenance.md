# Phase 4: Taxonomy, data quality, and provenance

Plan: [index.md](index.md)

Tasks: MVP-030, MVP-031, MVP-032, MVP-033

Depends on: MVP-020, MVP-021, MVP-022

Priority: P0 for recommendation trust; P1 for scalable ingestion

## Objective

Make the 22-area discipline taxonomy auditable and make missing data useful
rather than either silently universal or product-blocking. Preserve
fail-closed behavior where a missing fact can cause a false admission or
ranking conclusion, while allowing degradable evidence to support a helpful
partial product.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| 22-area model | CONFIRMED | backend/src/andromeda/modules/disciplines/domain/areas.py defines 22 DisciplineAreaCode values; area vectors validate normalization |
| Deterministic BMSTU mappings | PARTIALLY CONFIRMED | ingestion/universities/bmstu/mappings/discipline_areas.py has exact overrides and conflict checks; keyword rules and fallback remain |
| Unknown classification outcome | CONFIRMED GAP | RuleBasedDisciplineClassifier returns Universal/default_area_weights with debug logging; no persisted unknown queue or explicit outcome |
| HSE classification | PARTIALLY CONFIRMED | HSE has adapter mapping plus generic fallback; coverage of unknowns is not an executable metric |
| Claimed live audit | OUTDATED / UNVERIFIED | docs/architecture.md and docs/testing.md claim 2,582 unique disciplines and fallback_unclassified = 0; no source metric/model exists, and research notes say a full live audit is still needed |
| Provenance | PARTIALLY CONFIRMED | raw snapshots/source hashes and sourceGaps exist; recommendation suggestion path can expose source_hashes but does not consistently populate them |
| Blocking vs degradable gaps | PARTIALLY CONFIRMED | DecisionCandidatePipeline reports missing/max tuition/location source gaps; optional parser gaps are not uniformly structured as RawSourceGap |

## Files to Change

| Future change | Path |
| --- | --- |
| Classification outcome and taxonomy contracts | backend/src/andromeda/modules/disciplines/{domain,contracts,services} |
| University overrides | backend/src/andromeda/ingestion/universities/{bmstu,hse}/mappings |
| Source gaps/provenance | backend/src/andromeda/ingestion/contracts/raw.py, source.py, modules/*/contracts/public |
| Quality metrics/reporting | backend/src/andromeda/modules/admin_ops and backend/src/andromeda/infrastructure/repositories/ingestion.py |
| Regression dataset | backend/tests/fixtures/taxonomy/, backend/tests/ingestion/test_*taxonomy.py |
| Product documentation | docs/architecture.md, docs/testing.md, docs/mvp.md, docs/mvp-capability-matrix.md |

## Task MVP-030: Introduce explicit classification outcomes

### Intent

Stop treating an unknown discipline as indistinguishable from an intentional
Universal-area classification. The core still receives a normalized area
vector, but the ingestion/audit contract records how that vector was derived.

### Implementation Steps

1. Define a typed ClassificationOutcome with source name, normalized name,
   method (exact override, alias, keyword rule, fallback, unresolved),
   rule/override identifier, area weights, and review status.
2. Keep the existing deterministic area vector contract for downstream
   comparison/recommendation consumers.
3. Return unresolved/fallback metadata from
   RuleBasedDisciplineClassifier instead of only logging debug text.
4. Keep university-specific overrides in adapter mappings; do not move BMSTU
   aliases into generic domain code.
5. Define canonical normalization for whitespace, punctuation, case, common
   historical aliases, and safe Cyrillic/Latin variants.
6. Treat “Universal” as a legitimate explicit classification only when the
   rule says so; otherwise record unresolved.
7. Version taxonomy rules so a re-ingestion can explain why a vector changed.

### Required Interfaces and Contracts

- Area vectors remain normalized and typed.
- ClassificationOutcome is ingestion/audit data, not a new dependency from
  recommendation services into university adapters.
- Existing program/curriculum public contracts remain backward-compatible for
  one migration cycle; new fields are additive or have explicit defaults.

### Error Handling and Logging

- Log method, rule ID, and taxonomy version, never only “fallback”.
- Aggregate unresolved names by canonical normalized value and source run.
- Do not log a full source row if it may contain personal or sensitive data.

### Tests

- backend/tests/modules/test_discipline_classifier.py
- backend/tests/ingestion/test_bmstu_taxonomy.py
- backend/tests/ingestion/test_hse_parser.py
- Add tests for exact override, alias, keyword, explicit Universal,
  unresolved, conflicting override, normalization, and vector sum.

### Acceptance Criteria

- Every classified discipline has a machine-readable method and taxonomy
  version.
- Unknown/fallback classifications are countable and reviewable.
- Downstream consumers remain independent of university-specific mappings.
- Existing deterministic vectors remain stable unless an intentional rule
  change is recorded.

### Verification

- Run the full taxonomy and curriculum aggregation suites.
- Compare old and new area vectors for the frozen fixture baseline.
- Review any changed ranking/recommendation result as an intentional data
  change, not a test snapshot update.

## Task MVP-031: Build an auditable override and unknown workflow

### Intent

Allow a new university to add bounded, reviewable corrections without
requiring uncontrolled manual classification of thousands of strings.

### Implementation Steps

1. Define an override source format with canonical normalized key, university
   scope, optional source alias, target area vector, reason, owner, created
   date, taxonomy version, and review state.
2. Validate duplicate/conflicting overrides at import time.
3. Produce an unknown queue grouped by normalized name, university, source
   count, affected programs, and first/last observed run.
4. Add a deterministic review/apply workflow that produces a new mapping
   artifact and regression cases; do not edit runtime data manually.
5. Permit safe alias chains only when they terminate in a canonical key and
   are cycle-checked.
6. Require approval/review metadata for overrides affecting a high-volume
   classification or blocking quality gate.

### Required Interfaces and Contracts

- Override files are adapter-owned and do not change shared subject
  boundaries.
- Unknown queue is an operational artifact; it does not become a hidden
  recommendation signal.
- Applying an override is idempotent and tied to an ingestion run/taxonomy
  version.

### Error Handling and Logging

- Conflicting/invalid override fails the adapter validation stage with
  actionable key/rule IDs.
- Unknown queue output contains names and counts, not raw source documents.
- All override changes have audit identity and diffable artifact hash.

### Tests

- backend/tests/ingestion/test_bmstu_taxonomy.py
- new backend/tests/ingestion/test_taxonomy_overrides.py
- new backend/tests/ingestion/test_unknown_queue.py
- Add fixture with conflicting duplicate mappings and alias cycle.

### Acceptance Criteria

- Adding a third adapter requires an adapter mapping/override artifact and
  regression cases, not changes to generic recommendation/domain code.
- Unknown classifications are visible to operators and never silently
  counted as reviewed Universal.
- Re-running the same override is idempotent.

### Verification

- Apply the workflow twice to BMSTU/HSE fixture data.
- Inspect output for stable counts, hashes, and review metadata.
- Run strict mypy and adapter tests.

## Task MVP-032: Add coverage metrics and taxonomy regression dataset

### Intent

Replace the unsupported prose claim fallback_unclassified = 0 with executable
metrics and a small but meaningful regression dataset. Coverage percentage is
an input to quality, not the only quality metric.

### Implementation Steps

1. Define metrics by university and run:
   classification coverage, unresolved count, fallback count, explicit
   Universal count, area usage, conflicting mappings, duplicate normalized
   keys, and programs/curricula affected.
2. Add a committed regression corpus containing representative disciplines,
   historical aliases, ambiguous terms, each area, and known unknowns.
3. Add thresholds only for blocking categories; avoid requiring arbitrary
   area distribution.
4. Store metric summary in ingestion run metadata and expose safe operator
   detail.
5. Update docs/testing.md and docs/architecture.md to cite the executable
   metric and remove stale 2,582 claim until a reproducible live audit exists.
6. Track metric changes across source runs and require review for large
   regressions.

### Required Interfaces and Contracts

- Metrics are versioned and tied to source hash/run ID/taxonomy version.
- Public user responses expose a useful source-gap summary, not all operator
  counters.
- No metric should be used to claim Career Fit or Workload Readiness.

### Error Handling and Logging

- Metric calculation failure blocks publication if the metric is a blocking
  quality gate.
- Log count summaries and threshold decisions; avoid item-level log floods.

### Tests

- backend/tests/ingestion/test_bmstu_taxonomy.py
- new backend/tests/ingestion/test_taxonomy_metrics.py
- backend/tests/integration/test_bmstu_full_ingestion.py
- backend/tests/integration/test_hse_full_ingestion.py
- Add a regression test that detects a large unexplained coverage drop.

### Acceptance Criteria

- A release can cite exact taxonomy coverage from a reproducible run.
- The old documentation claim is either proven by the new metric or removed.
- Both positive coverage and unknown queue are tested.
- Quality gate distinguishes critical admission/curriculum absence from
  non-blocking unknown discipline names.

### Verification

- Run fixture metrics for BMSTU and HSE.
- Compare against baseline and document differences.
- Run one synthetic third-university dataset to ensure metrics are generic.

## Task MVP-033: Carry field-level provenance and gap severity

### Intent

Make every user-visible recommendation, admission status, comparison fact, and
program detail explain what source evidence was used and what was missing.

### Implementation Steps

1. Define a compact provenance reference: university, source kind, canonical
   URL if safe, captured-at, content hash, source revision/run ID, and field
   or record scope.
2. Link parser warnings and optional failures to RawSourceGap records rather
   than only logger text.
3. Carry provenance through canonical repository readers into recommendation,
   decision suggestion, admission, comparison, and program detail contracts.
4. Define gap severity:
   blocking (cannot safely calculate), degradable (result available with
   warning), informational (optional source missing).
5. Ensure source hashes and reason evidence are populated before API mapping;
   a missing optional value must not cause silent empty arrays.
6. Add a safe user-facing summary and a richer admin detail without exposing
   raw source bodies.

### Required Interfaces and Contracts

- Provenance remains a typed public contract, not an unstructured dictionary.
- Content Fit provenance is separate from Admission Fit provenance.
- Inferred activity signals must be marked inferred and cannot be displayed
  as direct source facts.
- UserProfile and account/session scope must not be included in source
  provenance.

### Error Handling and Logging

- Missing provenance on a claimed source-backed field is a validation error
  in the publication path.
- Public errors use safe code/message; admin logs include run/stage/source
  identifiers.
- Never include cookies, profile answers, or raw PDF/HTML in provenance.

### Tests

- backend/tests/api/test_recommendations_contract.py
- backend/tests/api/test_admission_fit_contract.py
- backend/tests/api/test_compare_contract.py
- backend/tests/modules/test_programs.py
- backend/tests/ingestion/test_raw_canonical_contract.py
- Add field-level provenance and missing-gap contract tests.
- Add frontend-next/src/lib/api.test.ts assertions that mappers do not drop
  provenance, source hashes, or confidence metadata; extend this existing API
  boundary suite rather than creating a duplicate test location under
  frontend-next/tests/.

### Acceptance Criteria

- A recommendation can answer why it was ranked, which evidence was used,
  what was inferred, what was missing, and how reliable the result is.
- Admission and Content Fit evidence cannot be conflated.
- Source gaps are observable and actionable rather than a generic empty
  result.

### Verification

- Trace a BMSTU and HSE program through raw snapshot, canonical row, API
  response, and frontend rendering.
- Test a missing optional source, missing curriculum, missing admission
  passing score, and parser failure.
- Inspect both public and admin responses for safe disclosure.

## Phase Risks and Mitigations

- **Risk:** adding provenance bloats every response. **Mitigation:** use
  compact references and field/record scoping; offer detail only where useful.
- **Risk:** unknown queue becomes manual bottleneck. **Mitigation:** group,
  prioritize by affected programs, and retain deterministic keyword/alias
  rules for low-risk known patterns.
- **Risk:** stricter taxonomy gate harms partial product. **Mitigation:**
  separate blocking curriculum/admission facts from degradable classification
  uncertainty and expose the uncertainty.

## Phase Completion Checklist

1. Classification method and taxonomy version are explicit.
2. Unknowns and overrides are auditable and regression-tested.
3. Coverage metrics are reproducible and no unsupported live-audit claim
   remains.
4. Provenance and gap severity survive raw → canonical → API → UI.
5. Fail-closed behavior is retained for safety-critical missing facts.
