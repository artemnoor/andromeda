# Phase 10 — Live acceptance remediation and evidence

Plan: [index.md](index.md)
Tasks: T27–T32
Depends on: completed Phases 00–09; real configured TypeSafe-compatible provider credentials are supplied only through the existing environment configuration.

## Objective

Довести фактические call paths до подтверждённого поведения на реальном Jev, не менять уже работающие bounded ports и не подменять детерминированные domain services. Существующий production artifact `next-action.v1` остаётся неприкосновенным baseline. Любая новая calibration считается production только если это подтверждают raw provider probabilities, upstream `jevcal`, held-out labels и текущий runtime callsite.

## Task T27 — Normalize live TypeSafe intent labels at the provider boundary

### Evidence and paths

- `backend/config/jev/question-definitions.v1.yaml` returns registry labels `catalog_search`, `comparison`, `admission_search`, `recommendation`, `unknown`.
- `ConversationIntent` in `backend/src/andromeda/modules/conversation/contracts/public.py` supports `analytics_query`, `compare_programs`, `admission_search`, `unknown`.
- `backend/src/andromeda/infrastructure/jev/typesafe_client.py::_payload_for` currently forwards the provider's raw label, so a valid `comparison` output fails typed validation in `JevDecisionModelAdapter.resolve_intent`.
- Do not edit the registry YAML: its content hash participates in the checked-in `next-action.v1` lock compatibility.

### Implementation

1. Add a closed provider-boundary mapping: `catalog_search → analytics_query`, `comparison → compare_programs`, `admission_search → admission_search`, `unknown → unknown`. Unsupported `recommendation` maps to `unknown` unless the current typed domain contract explicitly supports it; never expand product behavior implicitly.
2. Preserve raw answer and full probabilities in `JevAnswerEvidence`; the mapping affects only the typed payload, not calibration labels/evidence.
3. Add unit and adapter regression tests for every mapping, unsupported category, exact evidence preservation, and deterministic fallback on malformed/out-of-registry values.
4. Revalidate the existing next-action artifact and its manifest/corpus hashes byte-for-byte; do not regenerate these artifacts.

### Logging and errors

Log only operation, source, mapped outcome, fallback reason and model version; never log query text, key, headers, or full provider body. Unknown labels fail closed to `unknown`/deterministic policy.

### Tests and acceptance

- `backend/tests/infrastructure/test_typesafe_client.py`
- `backend/tests/infrastructure/test_jev_adapter.py`
- `backend/tests/evaluation/test_jevcal_artifacts.py`
- Prove a raw `comparison` result becomes typed `compare_programs` with `source=jev` only when the existing calibration gate accepts it.
- Prove all current checked-in next-action artifacts remain valid without content changes.

### Dependencies and rollback

No schema or migration change. Roll back only the mapping and its tests if the actual domain enum/callsite differs; deterministic fallback stays intact.

## Task T28 — Add bounded, explicitly curated live evaluation cases for registered operations

### Paths and contracts

- Extend `backend/evals/jev/` with synthetic, curated cases and labels; never use Jev output as ground truth.
- Reuse `QuestionRegistry`, `DecisionModelOperation`, and current corpus schemas.
- Add evaluation coverage for `intent.v1`, `metric.v1`, `presentation.v1`, and `olympiad-profile-resolution.v1`; semantic classification may be probed only as review/evaluation data, never source fact.

### Implementation

1. Curate test strata: ordinary wording, colloquial forms, typos, incomplete queries, boundary pairs, ambiguity, OOD/unsupported requests. Labels must be authored independently of Jev predictions and restricted to each definition's allow-list. A dataset that has not received independent human review must be labelled as fixture/evaluation evidence, not human-reviewed or production-distribution evidence.
2. For metric and Olympiad resolution, each case records its exact candidate set. Labels outside that set are invalid; dynamic candidates must come from the canonical metric registry or captured BMSTU 2026 Olympiad-profile records.
3. Build deterministic exporters that include registry/corpus hashes, split, definition version, case ID and source provenance for official Olympiad candidates. Do not persist arbitrary applicant text or personal facts.
4. Document which definitions have active product callsites: next-action and bounded Olympiad-profile resolution do; intent/metric/presentation remain evaluation-only unless a separate existing callsite is proven; semantic classification remains human-review-only.

### Logging and errors

Evaluation commands log counts, hashes, definition IDs, latency/cost summaries and sanitized failure classes. They must not print credentials or unrestricted corpus text. Invalid labels/candidates abort before provider calls.

### Tests and acceptance

- Add contract/schema/export tests under `backend/tests/evaluation/`.
- Cases validate against the exact registry output values and candidate set.
- Include ambiguous and unresolved Olympiad wording. Labels are source-derived or explicitly human-owned; no pseudo-labeling from model predictions. Record whether cases were independently human-reviewed and whether typo/abbreviation strata actually exist; do not imply coverage that the corpus does not contain.

### Dependencies and rollback

No runtime behavior changes. If official fixture parsing cannot resolve a profile, retain a review-required case; do not invent an ID/alias.

## Task T29 — Extend live capture/calibration tooling without changing the existing next-action artifact

### Paths and upstream boundary

- `backend/scripts/jevcal_capture_production.py`
- `backend/scripts/jevcal_calibrate.py`
- `backend/evals/jev/exporters.py`
- `backend/tests/evaluation/test_jevcal_capture_production.py`
- `backend/tests/evaluation/test_jevcal_artifacts.py`
- Use the existing pinned upstream `jevcal` package and `jevcal.runtime.Cascade`; keep Andromeda code to capture/export/validation/wiring.

### Implementation

1. Add explicit registry, definition, cases, observations, lock and manifest path parameters (or a sibling CLI wrapper calling the same script functions) so new definitions produce independent artifacts. Defaults must continue to validate the existing next-action files unchanged.
2. Capture only synthetic/curated cases through the official SDK; run health and model identity checks first; apply existing bounded timeout, endpoint allow-list, request budget and no-secret logging.
3. Require full probability distribution for every expected option. For dynamic-choice operations validate exact per-case candidate identities; never silently fill missing probabilities or normalize malformed output into evidence.
4. Let upstream `jevcal` choose threshold and produce lock/report. Preserve human labels, deterministic split, provider/model identity and all evidence hashes.
5. Production gates remain explicit and configurable but not weaker than current gates: at least 100 total observations, 30 held-out, 30 accepted fit support, upstream quality status and observed model compatibility. If any criterion fails, artifact status is not production-ready.

### Logging and errors

Fail before network calls on bad inputs/insufficient heldout. On provider errors, record only safe exception classes and leave incomplete observations clearly incomplete; never mislabel them as live success. Refuse overwriting existing artifacts.

### Tests and acceptance

- CLI argument, budget, redaction, probability completeness, hash, split, upstream invocation and fail-closed tests.
- Golden regression validates current `next-action.v1` lock, manifest and corpus without rewriting them.
- Offline CI uses fixtures only and never needs provider secrets.

### Dependencies and rollback

No runtime or DB change. New artifacts are separate files and may be disabled/removed independently; the established next-action lock is not rollback material and must not be changed.

## Task T30 — Capture and evaluate the wired Olympiad-profile resolver with official candidates

### Evidence and paths

- Source candidate universe comes from the existing captured BMSTU 2026 ingestion fixture and parser under `backend/tests/ingestion/fixtures/bmstu/admission_benefits/` and `backend/src/andromeda/ingestion/universities/bmstu/`.
- Runtime path is `build_admission_candidate_selector` → `JevAdmissionCandidateSelector` → existing bounded `EntityResolverService`; benefit facts remain in `admission_benefits` repositories/evaluator.
- Keep the separate admission registry and current lock setting. Do not place Olympiad benefit facts or user documents in Jev input.

### Implementation

1. Build candidate sets from parsed source-backed profile records, including all currently resolved profiles across cases while respecting the existing 2–8 candidate runtime limit. Every expected canonical ID must be supplied in that case.
2. Capture a bounded live corpus (target 120; production gate still requires minimum support/heldout and adequate per-profile/ambiguity coverage) with independently reviewed labels before claiming production-grade ground truth, exact candidate IDs, synthetic query wording, model identity and complete probabilities. If the capture uses authored templates and source-derived labels without independent review, report that limitation and keep the capability opt-in/evaluation-only.
3. Run the existing upstream Jevcal compiler and runtime `Cascade` compatibility validation. Generate a separate admission lock/manifest only if quality, support, registry hash, observed model and profile coverage pass; otherwise keep capability disabled and report shadow/evaluation-only.
4. Exercise the actual composition root so candidate sets of 2–8 invoke the selector only after deterministic narrowing; zero/one/>8 candidates bypass it. Any unresolved Jev choice, calibration rejection, invalid candidate or provider failure returns unresolved/clarification.

### Logging and errors

Log candidate count, source, accepted/unresolved and artifact ID; not query text, IDs of applicant records, or provider payload. No profile may be auto-created and no eligibility is inferred at this layer.

### Tests and acceptance

- Source fixture → BMSTU parser → canonical profiles → bounded selector tests.
- Live capture metadata verifies endpoint host, requested/observed model, SDK and Jevcal versions, latency, tokens, probability coverage and heldout split, without secret values.
- Jev-selected profile is then passed to the existing deterministic eligibility/service path; benefit outcome is asserted from persisted/source-backed rules, not model response.

### Dependencies and rollback

Depends on T28–T29. Keep the selector off if capture/evidence is insufficient or source candidate coverage is incomplete. Do not weaken runtime's fail-closed behavior to improve coverage.

## Task T31 — Verify live/deterministic/fallback vertical slices and operation-specific readiness

### Implementation

1. Run the real admission candidate-resolution + deterministic benefit lookup path and at least one existing `/assistant/query` path through the active composition. Include the user-approved admission clarification policy: ask budget vs paid; default to latest published year and full-time only where existing behavior defines those defaults.
2. Verify source-backed analytics comparison and admission calculation remain deterministic. Jev must not author program lists, benefits, SQL, thresholds, scores, or factual response text.
3. Execute the fallback matrix using existing fake transport/clock seams: provider timeout/5xx/auth failure, model mismatch, missing/stale/hash-mismatched lock, low probability, malformed/out-of-candidate output, circuit open, and optional dependency unavailable. These are failure tests, not claimed live-provider observations.
4. Verify shadow mode does not alter user-facing results and operations without product callsites do not become production-enabled.
5. Record per-operation disposition from evidence: production-calibrated and wired; live-evaluated but shadow-only; evaluation-only; deterministic-only; or blocked external. Distinguish live request counts from unit/fake calls.

### Logging and tests

- Run focused Jev infrastructure, calibration, e2e, admission-resolution, assistant API, and analytics tests.
- Assert no secrets or raw private profile data in caplog/artifacts.
- Every scenario records typed outcome, decision source/fallback reason, evidence source and latency where actually measured.

### Acceptance

- Jev unavailable never produces a 500 or an unsupported factual answer.
- A valid selected Olympiad/profile can only affect an outcome through deterministic persisted policy evaluation.
- All unsupported operations stay in their existing safe mode.

### Rollback

Disable the operation-specific feature flag/lock path. Never roll back deterministic facts or remove safety tests.

## Task T32 — Publish detailed acceptance evidence, commit, push and verify hosted CI

### Documentation

Create a dated Russian Markdown report under `docs/operations/` with per-operation live status, live dataset sizes and hashes, held-out/support, observed accuracy/coverage/threshold exactly as jevcal reports them, runtime wiring, provider host/model/package versions, latency/token summary, E2E outcomes, fallback matrix, known gaps and exact reproduction commands. Mark any unavailable/failed live run `BLOCKED_EXTERNAL`/`NOT_RUN`; never substitute mocks. Exclude keys, headers, raw personal text and private provider payloads.

### Verification and delivery

1. Run `git diff --check`, ruff, mypy, focused tests, full backend suite, OpenAPI/architecture/docs checks, PostgreSQL integration where available, and CI-equivalent workflow locally where practical.
2. Inspect staged file list and secret scan before committing. Create ordinary reviewable commits at C9 and C10; do not rebase, reset or force-push.
3. Push only `feature/jev-ecosystem-stage-2`; verify remote SHA equals local final HEAD.
4. Observe the GitHub Actions run for that exact SHA until all required jobs complete successfully. If any job fails, fix root cause on the same branch, commit, push and re-verify the new SHA.

### Acceptance and limitations

- Report contains separate `OFFLINE VERIFIED`, `LIVE VERIFIED`, and `NOT VERIFIED` sections.
- Each operation verdict matches actual callsite and upstream calibration evidence; unsupported operations are explicitly not production-ready.
- Final handoff includes final SHA, branch URL, report link, CI run URL/job results, tests and any honest external blockers.

### Risks and rollback

No runtime enablement is required to complete the evidence report. If hosted CI is red or unavailable, do not claim completion; retain the pushed checkpoint and report exact blocker. Revert only new operation-specific changes through a normal corrective commit; preserve prior Stage 2 history and the dirty sibling worktree.

## Verification commands

From `backend/`: `uv run --locked --extra evaluation --extra dev pytest tests/infrastructure/test_typesafe_client.py tests/infrastructure/test_jev_adapter.py tests/infrastructure/test_jevcal_cascade.py tests/infrastructure/test_jev_runtime.py tests/evaluation tests/e2e/test_jev_ecosystem_scenarios.py tests/api/test_assistant_query.py`; then the repository's full `uv run --locked --extra dev pytest` and lint/type commands discovered from CI. Hosted CI is the final authority for the pushed SHA.
