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

### Closeout baseline audited 2026-09-24

- Repository: `artemnoor/andromeda`; required branch `feature/jev-ecosystem-stage-2`; HEAD and `origin/feature/jev-ecosystem-stage-2` both equal `b1fff0a60b0a3c88b9dde15d24d784ea24194804`; worktree clean.
- `origin/main` is `626c28a663c37d3313198ac7d06b8c4d9fe0c708`; `main...HEAD` is `0 40` (0 behind, 40 ahead). Do not switch branches, rebase, or rewrite history.
- Active progress: T00–T29 checked; T30 and T31 unchecked. T32's baseline CI is verified, but the final delivery gate must run again against the post-T30/T31 SHA.
- Current report: `docs/operations/jev-stage2-live-acceptance-2026-09-24.md`. It records the Olympiad pilot as 120 observations / 62 held-out, 120/120 total and 62/62 held-out accuracy, complete probabilities, candidate threshold about 0.99, ECE 0.0001667, observed model `jev-1.13.0`. These are synthetic/source-fixture-derived observations, not production evidence; the corpus lacks independent human review and realistic wording strata.
- Locks to preserve byte-for-byte: `backend/config/jev/locks/next-action.typesafe-jev.v2.lock.json` and `.meta.json`. The active `next-action.v1` production artifact has 120 rows, 56 held-out, 100% accepted accuracy/coverage, threshold `0.64` on `top_prob`, ECE `0.0439166667`, requested `typesafe/jev`, observed `jev-1.13.0`. Preserve its registry/corpus/manifest compatibility. The v1 next-action lock is historical and has a different registry/definition version; do not promote it. `decisions.v1` is fixture-only. There is no active Olympiad resolver production lock.
- Baseline hosted Actions run [35973207398](https://github.com/artemnoor/andromeda/actions/runs/35973207398) is success on the exact baseline HEAD and shows all required jobs green. Local `gh run list` returned HTTP 401; for the final SHA, use the public Actions run page if CLI authentication remains unavailable, and verify commit SHA and every required job rather than trusting the earlier run.

### Evidence and paths

- Source candidate universe comes from the existing captured BMSTU 2026 ingestion fixture and parser under `backend/tests/ingestion/fixtures/bmstu/admission_benefits/` and `backend/src/andromeda/ingestion/universities/bmstu/`.
- Runtime path is `build_admission_candidate_selector` → `JevAdmissionCandidateSelector` → existing bounded `EntityResolverService`; benefit facts remain in `admission_benefits` repositories/evaluator.
- Keep the separate admission registry and current lock setting. Do not place Olympiad benefit facts or user documents in Jev input.
- Reuse `backend/config/jev/question-definitions.admission.v1.yaml`, `backend/evals/jev/corpus/operation-captures/`, `backend/scripts/jev_operation_evaluation.py`, `backend/scripts/jevcal_calibrate.py`, `backend/src/andromeda/infrastructure/jev/runtime.py`, and the official TypeSafe SDK transport. Do not introduce another resolver, calibration algorithm, runtime port, or database model.

### Implementation

1. Freeze a pre-run evidence manifest (HEAD, registry hash, source-fixture/document hashes, existing lock hashes and current flag state). Verify the next-action v2 lock with existing checks and assert its files are unchanged at the end.
2. Prepare a separate reviewed corpus, e.g. `backend/evals/jev/corpus/operation-captures/olympiad-profile-resolution.reviewed.v3.cases.jsonl`; keep v2 cases/observations immutable. Build every candidate ID only from successfully parsed official BMSTU 2026 Olympiad/profile records. Each case's expected answer is one supplied canonical profile ID or the literal `unresolved`; never include free-form model-generated identities.
3. Cover, with independently authored/reviewed expected labels: official full names, official abbreviations, conversational aliases, typos, word-order variants, Olympiad-only and profile-only mentions, near-neighbor profiles, ambiguous wording, short realistic phrases, unrelated/foreign Olympiads, and unresolved requests. Include only cases where the intended ID is present in its bounded 2–8 candidate set; ambiguous/out-of-source cases label `unresolved`. A deterministic narrowing result of zero, one, or more than eight candidates bypasses the Jev selector exactly as today.
4. Keep review provenance separate from model observations (prefer a companion review manifest if the existing case schema cannot express it). Reviewers must inspect expected IDs against official source-backed records without seeing Jev predictions; record adjudication for disagreements. Do not mark examples independently reviewed merely because an agent/script generated them. Split train/held-out by wording family or template family so paraphrase leakage cannot put near-duplicates on both sides; satisfy all existing Jevcal minimum total, held-out, support and per-label gates without lowering them.
5. If independent human review cannot be obtained, stop before calling Jev for calibration on the new corpus. Record `BLOCKED_EXTERNAL_REVIEW`, do not fabricate review or metrics, do not create/promote an Olympiad production lock, and leave `JEV_ADMISSION_RESOLUTION_ENABLED=false`/the current safe fallback. Existing v2 live numbers remain historical pilot evidence only.
6. Once review is complete, perform provider health check before capture; record requested model and observed model separately and require the observed model to match the configured/approved identity. Use the official TypeSafe SDK; capture complete per-option probabilities, allow-list outcome, provider/model/version, elapsed latency and token usage. Never print credentials, headers, raw applicant text, or provider payloads. Do not overwrite existing captures.
7. Run the pinned upstream Jevcal evaluation/compile/check and `jevcal.runtime.Cascade` compatibility validation. Store new cases, raw observations, Jevcal output, hashes and any candidate lock outside the active runtime lock directory first. Report total/held-out samples, exact total and held-out accuracy, probability coverage, Jevcal threshold and ECE, p50/p95 latency and token usage from the real capture. Do not round a failed gate into a pass, infer missing probabilities, reuse old observations, or invent a quality threshold.
8. Create/promote a separate admission lock and wire it through the existing composition only if the reviewed corpus, existing sample/support gates, upstream quality status, candidate coverage, registry/definition hashes, model compatibility and runtime `Cascade` all pass. Then prove that the active composition invokes Jev only after deterministic narrowing and that any low-confidence/unresolved/out-of-set/model/provider failure safely returns unresolved/clarification. Otherwise leave the feature disabled or shadow/evaluation-only and report the failed gate.

### Logging and errors

Log only operation ID, candidate count, source, accepted/unresolved, safe failure class, artifact ID, latency and observed model. Do not log query text, raw candidate labels when they reveal private context, applicant identifiers or provider payload. No profile may be auto-created and no eligibility is inferred at this layer.

### Tests and acceptance

- Update/reuse `backend/tests/evaluation/test_jev_operation_evaluation.py`, `backend/tests/evaluation/test_jevcal_artifacts.py`, `backend/tests/evaluation/test_jevcal_exporter.py`, `backend/tests/infrastructure/test_jev_runtime.py`, `backend/tests/infrastructure/test_jev_adapter.py`, `backend/tests/integration/test_bmstu_admission_benefits_ingestion.py`, `backend/tests/vertical/test_bmstu_admission_benefits_vertical_slice.py`, and `backend/tests/modules/entity_resolution/test_services.py` only where evidence identifies a gap.
- Corpus validation proves each label is independently reviewed, official-source-backed, present in the exact candidate set (or `unresolved`), held-out is group-separated, and all required wording strata are present. It rejects model-derived labels and invented IDs.
- Live report records health result, endpoint host, requested/observed model, SDK/Jevcal versions, exact sample counts/hashes, complete-probability coverage, accuracy, threshold/ECE, latency percentiles and token usage; secrets and raw request text are absent.
- Vertical proof separates `LIVE_SELECTION` from `DETERMINISTIC_ELIGIBILITY`: the selected canonical ID may reach `AdmissionBenefitEvaluator`, but the resulting benefit, scope, confirmation and provenance must come only from persisted/source-backed rules. A live capture replay that bypasses a production lock is explicitly evaluation-only, not production runtime proof.
- Production status is permitted only with real independent review, sufficient held-out evidence under existing gates, successful upstream Jevcal/Cascade validation, active composition evidence and source-backed vertical success. Otherwise T30 stays open/blocked or explicitly evaluation-only; no production-ready label or active lock is allowed.

### Dependencies and rollback

Depends on T28–T29 and external human review plus provider credentials for a genuine live capture. No migration is expected. Roll back only newly introduced Olympiad-specific corpus/calibration/flag artifacts through a normal commit; preserve v2 pilot evidence, the working next-action v2 lock, and all Jev Stage 2 paths. Keep the selector off if any external or statistical gate is missing.

## Task T31 — Verify live/deterministic/fallback vertical slices and operation-specific readiness

### Closeout evidence recorded 2026-09-24

- T31 verified the supported deterministic/API paths and deliberately recorded unsupported or externally blocked product capabilities rather than widening scope. Detailed per-scenario statuses and live metrics are in `docs/operations/jev-stage2-live-acceptance-2026-09-24.md`.
- A one-request live shadow call traversed the real `/assistant/query` composition and official TypeSafe SDK: Polza endpoint, requested `typesafe/jev`, observed `jev-1.13.0`, `choose_next_action`, 1031 ms, 535 input / 73 output tokens. It returned HTTP 200 with the deterministic EGE clarification. The temporary process settings did not change production flags or locks.
- Added tests cover model invocation plus exact deterministic-result identity in shadow, safe telemetry redaction, provider-timeout non-500 at the assistant API, canonical comparison evidence/basis, and safe clarification/no invented IDs for similar-program, vague “better”, missing comparison context, and unresolved `ИУ5/ИУ7` department phrases.
- The department labels `ИУ5/ИУ7` are not canonical programs in the current analytics contract and no source-backed department-to-curriculum mapping was found in this closeout. The exact user wording is therefore `UNSUPPORTED` pending scope clarification; canonical program-ID comparison is `OFFLINE_VERIFIED`.
- T30 is `BLOCKED_EXTERNAL_REVIEW`: no independent reviewer/adjudicator or reviewed corpus was available. No new Olympiad-resolution live capture, Jevcal output, candidate lock, or production enablement was fabricated. The prior v2 pilot remains historical evaluation evidence only.
- Targeted suite passed: 142 tests, 31 warnings. The next-action v2 lock and manifest hashes match the pre-run values. No schema/migration changes.

### Implementation

1. Run the following fixed acceptance matrix without adding product capabilities:

   | Case | Current path to verify | Pass evidence / safe outcome |
   |---|---|---|
   | A — “Куда я прохожу с 270 баллами?” | `/assistant/query` → `QuerySession` → active `choose_next_action` policy → deterministic admission services | Live Jev call is recorded only if credentials/health are available; required missing EGE/scope/funding slots are asked without repetition; budget vs paid is explicitly asked; completed result is computed by current admissions data. If live credentials are absent, record `LIVE_JEV_NOT_RUN` and separately pass deterministic/API tests. |
   | B — “Где больше математики: ИУ5 или ИУ7?” | Existing resolver/typed analytics query → analytics execution → response envelope | Exact canonical programs, metric, projection/source evidence and missing-data behavior are asserted. Intent/metric Jev operations remain evaluation-only unless an already-existing production callsite and compatible lock are proven; do not add one here. |
   | C — “Какие программы похожи?” | Existing supported query/clarification boundary only | This is not to be implemented as a new similarity feature in this closeout. Return clarification/unsupported safely and assert that no program IDs or similarity claims are fabricated. Report `UNSUPPORTED`/`NOT_RUN` for the product capability rather than marking similarity as delivered. |
   | D — “Что даёт Шаг в будущее по инженерному делу?” | Deterministic narrowing → bounded Olympiad candidate selector → canonical profile → `AdmissionBenefitEvaluator` / persisted source policy | If T30 has a validated lock, prove the active live composition path. Without it, test disabled/fallback behavior and, if a real live capture exists, label any capture-to-evaluator replay `LIVE_EVALUATION + DETERMINISTIC_EVALUATION`, never active-runtime acceptance. Benefit type, scope, confirmation and source locator come exclusively from official persisted rules. |
   | E — “Есть ли у меня БВИ?” | Existing admission-benefit service/API | Requires canonical Olympiad/profile, result type and year as needed; BVI is granted only by applicable active source-backed policy. Historical BVI observations never establish eligibility. |
   | F — “Сколько дают за индивидуальные достижения?” | Existing persisted `IndividualAchievementPolicy` and deterministic calculator | Show only current applicable rules and source-backed points/caps; review-required/unknown rules do not award invented points. Jev is not used for scoring. |
   | G — “Сравни эти две программы” | `QuerySession` → analytics/comparison → `ResponsePlan`/`ResponseEnvelope` | Assert typed inputs, source-backed result/evidence, presentation type and deterministic facts; no model-generated score or program list. |
   | H — “А где лучше?” | Existing intent/entity/query clarification path | Ask a material clarification (programs and/or comparison dimension); do not silently resolve “better” to an unsupported score or recommendation. |

2. Run fallback acceptance through the existing fake transport/clock/artifact seams for invalid API key, timeout, provider 5xx, unavailable/mismatched model, malformed response, out-of-allow-list answer, absent/stale/hash-mismatched or model/definition-incompatible calibration, low probability, missing optional SDK and open circuit. Assert deterministic continuation/clarification and no Jev-induced HTTP 500. These are offline failure simulations, never label them live provider outages.
3. Strengthen `backend/tests/modules/conversation/test_shadow_policy.py` if needed: a spy proves the shadow model is actually invoked, the returned user-facing decision is exactly the deterministic decision, and safe telemetry contains no raw query/session/profile/secrets. Run a live shadow smoke only when the existing runtime credentials and health check permit; record actual model, operation, latency and outcome, otherwise `LIVE_SHADOW_NOT_RUN`.
4. Preserve the user-approved admission clarification behavior already in `backend/tests/api/test_assistant_query.py`: ask funding type; use latest published admission year and full-time only where current code already defines those defaults. Do not add new defaults or alter admissions policy.
5. For each case and operation, record separate statuses `LIVE_VERIFIED`, `OFFLINE_VERIFIED`, `NOT_RUN`, `UNSUPPORTED`, or `BLOCKED_EXTERNAL`, plus runtime callsite, decision source, fallback reason, source evidence and measured latency where applicable. A fake, fixture replay, or evaluation-only adapter call never counts as live production runtime evidence.

### Logging and tests

- Run focused tests: `backend/tests/infrastructure/test_typesafe_client.py`, `test_jev_adapter.py`, `test_jevcal_cascade.py`, `test_jev_runtime.py`; `backend/tests/evaluation/`; `backend/tests/e2e/test_jev_ecosystem_scenarios.py`; `backend/tests/api/test_assistant_query.py`, `test_analytics_api.py`, `test_admission_benefits_api.py`; `backend/tests/integration/test_analytics_engine.py`, `test_andromeda_comparison.py`, `test_bmstu_admission_benefits_ingestion.py`; `backend/tests/vertical/test_bmstu_admission_benefits_vertical_slice.py`; `backend/tests/modules/conversation/test_shadow_policy.py`; and relevant admission-benefits evaluator tests.
- Add only regression tests for demonstrated gaps; retain all existing compatibility and architecture checks. No DB schema/migration or public API change is expected.
- Verify `backend/config/jev/locks/next-action.typesafe-jev.v2.lock.json` and manifest hashes/content remain unchanged and valid. Assert `JEV_ADMISSION_RESOLUTION_ENABLED` stays false unless T30's production gate passed.
- Redaction tests assert no keys, headers, raw private profile/query text, or provider bodies appear in logs/reports/artifacts. Store only safe synthetic query IDs and aggregate latency/token data.

### Acceptance

- A, B, D–H each have truthful live/offline/not-run status and a passing applicable deterministic/fallback assertion; unsupported C explicitly remains unsupported and produces no hallucinated programs.
- Invalid credentials, provider failure, stale/missing calibration, low confidence, malformed/out-of-set choices, missing SDK and open circuit never produce a Jev-caused user-facing 500 or unsupported factual answer.
- A resolved Olympiad can affect eligibility only through deterministic persisted current-year benefit rules; no historical observation or Jev answer grants BVI/100 points/individual-achievement points.
- Shadow mode is shown to call Jev while leaving the user-visible deterministic result unchanged. Operations without a production callsite or calibrated compatible lock remain evaluation-only/deterministic-only.
- If the human-reviewed corpus or live provider credentials are unavailable, report that exact external blocker; do not mark T30 production-ready. Keep the operation disabled and leave any dependent live slice blocked/not-run instead of claiming completion.

### Rollback

Disable the operation-specific feature flag/lock path. Never roll back deterministic facts or remove safety tests.

## Task T32 — Publish detailed acceptance evidence, commit, push and verify hosted CI

### Documentation

Update the existing `docs/operations/jev-stage2-live-acceptance-2026-09-24.md` rather than creating a duplicate report. Preserve the baseline section and v2 pilot numbers; append the T30/T31 closeout with exact new corpus/observation hashes, independent-review status, Jevcal output, latency/token metrics, scenario matrix, fallback results, operation-specific readiness, unsupported/not-run items and reproduction commands. Mark unavailable evidence `BLOCKED_EXTERNAL`/`NOT_RUN`; never substitute mocks. Exclude keys, headers, raw personal text and private provider payloads. Explicitly state that the next-action.v2 production lock was not modified.

### Verification and delivery

1. Run `git diff --check`, focused Jev/admission/analytics/assistant tests, the full backend suite, ruff, mypy, OpenAPI/architecture/docs checks, PostgreSQL integration where available, and CI-equivalent checks locally where practical. Confirm the current next-action production artifact remains byte-identical and valid.
2. Inspect `git diff --cached --name-only` and secret scan before each normal commit. Keep commits reviewable: one after T30 corpus/live-calibration disposition (whether production lock is promoted or explicitly withheld), then one after T31 regression/report completion. Do not rebase, reset or force-push.
3. Push only `feature/jev-ecosystem-stage-2`; verify remote SHA equals local final HEAD and compare that SHA to `main`.
4. Observe the hosted workflow for that exact final SHA to completion. Required green jobs: `backend`, `postgresql-integration`, `fullstack`, `frontend-next`, `packaging`, `dependency-audit`, `documentation`, `telegram-bot`, `proftest-integration`, `jev-ecosystem-offline`. If local `gh` remains unauthorized, use the public Actions run page and verify the SHA plus every job. If a job fails, fix its cause on the same branch, commit/push the new HEAD, then verify that new SHA; never reuse the baseline run as final evidence.

### Acceptance and limitations

- Report contains separate `OFFLINE VERIFIED`, `LIVE VERIFIED`, and `NOT VERIFIED` sections and distinguishes the existing baseline CI run from the post-closeout final-SHA run.
- Each operation verdict matches actual callsite and upstream calibration evidence; unsupported operations are explicitly not production-ready.
- Final handoff includes final SHA, branch URL, report link, CI run URL/job results, tests and any honest external blockers.

### Risks and rollback

No runtime enablement is required to complete the evidence report. If hosted CI is red or unavailable, do not claim completion; retain the pushed checkpoint and report exact blocker. Revert only new operation-specific changes through a normal corrective commit; preserve prior Stage 2 history and the dirty sibling worktree.

## Verification commands

From `backend/`: `uv run --locked --extra evaluation --extra dev pytest tests/infrastructure/test_typesafe_client.py tests/infrastructure/test_jev_adapter.py tests/infrastructure/test_jevcal_cascade.py tests/infrastructure/test_jev_runtime.py tests/evaluation tests/e2e/test_jev_ecosystem_scenarios.py tests/api/test_assistant_query.py`; then the repository's full `uv run --locked --extra dev pytest` and lint/type commands discovered from CI. Hosted CI is the final authority for the pushed SHA.
