# Andromeda: MVP Production Level evidence ledger

**Decision date:** 2026-09-19
**Repository baseline:** branch `feature/andromeda-mvp-production-level`,
baseline commit `4088116`
**Current release decision:** **NOT READY — Private Alpha transition**

This ledger is a release-evidence document, not a runtime source of truth. It
records what the repository currently proves, what it does not prove, and the
next verification required before the project may claim **MVP Production
Level**. `VERIFIED` means reproducible from repository-controlled fixtures or a
disposable local database; it does not mean that live production operation has
been proven.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `VERIFIED` | The stated behavior has executable, repeatable evidence in the repository or an explicitly named disposable environment. |
| `PARTIALLY VERIFIED` | A real implementation and some evidence exist, but a release-relevant path or state is still missing. |
| `UNVERIFIED` | The repository does not currently contain sufficient executable evidence. It must not be treated as green. |
| `INTENTIONAL` | A deliberate architecture or product-scope decision; it is not a defect to simplify away. |
| `FUTURE RISK` | Not a current MVP blocker, but requires a scale-triggered follow-up. |

## Evidence ledger

| Claim | Current status | Evidence | Missing evidence | Owner / next verification | Release impact |
| --- | --- | --- | --- | --- | --- |
| Five primary user flows have a truthful current-state map | `VERIFIED` | [capability matrix](mvp-capability-matrix.md), [vertical smoke](../backend/tests/vertical/test_mvp_production_flows.py::test_mvp_anonymous_journey_covers_data_gaps_choice_and_ingestion_recovery), [current browser flow](../frontend-next/tests/mvp-production-flow.spec.ts) | Live deployment and wider browser matrix are not release proof | `MVP-093..095`; rerun browser smoke after deployment | Required baseline; not sufficient for promotion alone |
| BMSTU and HSE ingestion is reproducible with stable canonical outcomes | `PARTIALLY VERIFIED` | [baseline manifest](../backend/tests/fixtures/mvp/baseline_manifest.json), [baseline regression](../backend/tests/vertical/test_mvp_baseline_regression.py::test_fixture_source_manifest_is_stable), and 2026-09-19 read-only live probes accepted both adapters as `degraded` (BMSTU 134/134 curriculum+admission programmes; HSE 85/96 curriculum and 49/96 admission programmes) | Release-owner source-health artifact, repeatability record, source-change handling, and third-university onboarding | `MVP-021..024` / `MVP-095`; attach authorized live capture evidence | P0 until live/recovery evidence exists |
| PostgreSQL migration and projection path works on a disposable database | `PARTIALLY VERIFIED` | [PostgreSQL ingestion test](../backend/tests/integration/test_postgresql_ingestion.py::test_postgresql_ingest_is_repeatable_and_updates_projection), [profile persistence test](../backend/tests/integration/test_postgresql_user_profile.py::test_postgresql_persists_user_profile_through_repository_and_api), and a fresh disposable PostgreSQL 16 run passed 5 integration/smoke tests on 2026-09-19 | Clean-checkout bootstrap, supported production PostgreSQL version matrix, rollback and crash recovery | `MVP-040..042`; attach release CI/deployment evidence | P0 |
| Catalog, curriculum, admissions, comparison, and source-backed admission fit return stable business outcomes | `VERIFIED` | [baseline public read assertions](../backend/tests/vertical/test_mvp_baseline_regression.py::test_public_fixture_read_paths_keep_stable_business_outcomes), [production flow test](../backend/tests/vertical/test_mvp_production_flows.py::test_mvp_anonymous_journey_covers_data_gaps_choice_and_ingestion_recovery) | Partial/failed UI states and live source freshness | `MVP-051`, `MVP-071`; verify browser and source-health scenarios | P0 product trust |
| Recommendation ranking is deterministic and explainable for Content Fit | `VERIFIED` | [recommendation tests](../backend/tests/modules/recommendations), [versioned regression corpus](../backend/tests/fixtures/recommendations/regression-v1.json), [vertical smoke](../backend/tests/vertical/test_mvp_production_flows.py::test_mvp_anonymous_journey_covers_data_gaps_choice_and_ingestion_recovery) | This is verified for the bounded MVP policy: the corpus proves deterministic ordering, anti-interest behavior, tie-breaks, source-backed reasons, explicit unknowns, and evidence degradation; it is not predictive-accuracy validation | `MVP-060..063`; connect the evaluated profile/session path and review new source snapshots before changing weights | P0 |
| Admission Fit is an evidence-backed readiness assessment, not a probability claim | `PARTIALLY VERIFIED` | [partial-data assertion](../backend/tests/vertical/test_mvp_production_flows.py::test_mvp_anonymous_journey_covers_data_gaps_choice_and_ingestion_recovery), [Admission Fit docs](admission-fit.md), [browser validation](../frontend-next/tests/admission-fit.spec.ts) | Complete/partial submission browser matrix and explicit constraint semantics | `MVP-052`; extend browser and API evidence for constraint outcomes | P0 |
| Career Fit and validated Workload Readiness are public MVP capabilities | `INTENTIONAL` — out of scope | [product principles](product-principles.md), [capability matrix](mvp-capability-matrix.md) | No implementation is promised in the MVP claim | Product decision; do not promote without a new scoped plan | Must remain excluded from MVP claims |
| Adaptive proftest session path is compact, resumable, revision-bound, and persisted | `PARTIALLY VERIFIED` | [production flow](../backend/tests/vertical/test_mvp_production_flows.py::test_mvp_anonymous_journey_covers_data_gaps_choice_and_ingestion_recovery), [session API tests](../backend/tests/api/test_proftest_sessions_api.py), [expiry repository test](../backend/tests/infrastructure/test_proftest_sessions_repository.py::test_expired_draft_is_not_resumed_and_next_start_creates_a_new_session), [signal corpus](../backend/tests/fixtures/proftest/signal-corpus-v3.json), [handoff projection tests](../backend/tests/modules/proftest/test_proftest_projection.py), [browser regression](../frontend-next/tests/proftest.spec.ts) | Core session/recovery and handoff are covered; a broader two-context and mobile/accessibility matrix remains useful evidence, but is not a missing runtime contract | `MVP-095`; run the canonical browser suite in the production-like deployment | P0 for first recommendation experience |
| DecisionContext owns shortlist/final choice, optimistic revision, and explicit constraint outcomes | `VERIFIED` | [decision regression](../backend/tests/vertical/test_mvp_baseline_regression.py::test_decision_baseline_is_deterministic_and_revision_bound), [constraint API test](../backend/tests/api/test_decision_routes.py::test_decision_suggestions_report_source_backed_constraint_outcomes), [browser constraint smoke](../frontend-next/tests/admission-fit.spec.ts) | Concurrency and durable analytics behavior under deployment load | `MVP-041`; add concurrent mutation evidence | P0 if choice can be lost |
| Anonymous profile/auth isolation and guest-to-account transfer are implemented | `PARTIALLY VERIFIED` | [vertical auth flow](../backend/tests/vertical/test_mvp_production_flows.py::test_mvp_anonymous_journey_covers_data_gaps_choice_and_ingestion_recovery), [auth API tests](../backend/tests/api/test_auth_api.py), [request-control tests](../backend/tests/api/test_request_controls.py) | Production cookie/origin matrix and deployment evidence remain | `MVP-095`; run security/browser checks with production-like origins | P0 |
| Admin/Ops ingestion run lifecycle is diagnosable and retryable | `PARTIALLY VERIFIED` | [vertical failed→completed retry](../backend/tests/vertical/test_mvp_production_flows.py::test_mvp_anonymous_journey_covers_data_gaps_choice_and_ingestion_recovery), [admin API tests](../backend/tests/api/test_admin_ops_api.py) | Locking, durable source health/alerts, HSE parity, and operator UI confirmation/error states | `MVP-023`, `MVP-082`; execute failed-run/recovery drill | P0 |
| Structured request/run observability is sufficient for MVP operation | `PARTIALLY VERIFIED` | [health/runtime route](../backend/src/andromeda/api/routes/health.py), [API tests](../backend/tests/api/test_andromeda_api.py), [request-control tests](../backend/tests/api/test_request_controls.py) | External source alerting/retention policy and production deployment log evidence | `MVP-095`; verify logs and health in deployment smoke | P0 |
| Taxonomy coverage and unknown classification are auditable | `PARTIALLY VERIFIED` | [taxonomy classifier tests](../backend/tests/modules/test_discipline_classifier.py), [taxonomy metric tests](../backend/tests/ingestion/test_taxonomy_metrics.py), [regression corpus](../backend/tests/fixtures/taxonomy/discipline_classification.json) | Run metadata contains versioned coverage, unknown/fallback counts, area usage, source hashes and affected programs; reviewed overrides and grouped unknown queue are deterministic; external operator review remains | `MVP-095`; attach a current ingestion quality artifact | P0 for recommendation trust |
| CI proves clean-checkout backend/frontend/integration/browser quality | `PARTIALLY VERIFIED` | [testing guide](testing.md), [test matrix](test-matrix.md), [CI workflow](../.github/workflows/andromeda-ci.yml), canonical scripts under `../scripts/`, a local `core.autocrlf=false` clean-checkout simulation with `npm ci` where `python scripts/andromeda.py full` passed, and a fresh current-worktree full run (backend 535 passed/8 skipped, frontend 19 passed, Telegram 14 passed, migrations 22 passed, coverage 87%, fixture/production smoke) | Local evidence is not an owner-attached GitHub Actions run; CI must execute the same packaging/dependency/coverage gates and retain artifacts | `MVP-095`; run the workflow from the release commit | P0 |
| Production-like deployment can be installed, migrated, smoked, rolled back, and restored | `PARTIALLY VERIFIED` | [deployment documentation](deployment.md), [YC compose](../deploy/yc/compose.yaml), [deployment contract gate](../scripts/check_deployment_artifacts.py), disposable compose PostgreSQL/Caddy smoke, backup/restore and failed-image rollback evidence | Clean release checkout, owner-attached image/backup artifacts, and authorized live deployment evidence | `MVP-095`; attach the release run record | P0 |
| Documentation and AI workflow describe the current repository truth | `PARTIALLY VERIFIED` | [README](../README.md), [architecture](architecture.md), [test matrix](test-matrix.md), [AGENTS.md](../AGENTS.md), [repository rules](../.ai-factory/RULES.md), and `scripts/check_docs.py` | Remote clean-checkout command snippets and final migration/deployment evidence still need a release run | `MVP-095`; run documentation and deployment gates | P1 until final release gate |
| Current performance is adequate without premature optimization | `FUTURE RISK` | [baseline regression](../backend/tests/vertical/test_mvp_baseline_regression.py), [query/repository tests](../backend/tests/infrastructure) | Production-like timings, query plans, N+1 and memory evidence | `MVP-043`; measure before optimizing | Not a blocker without evidence |

## Release decision

The repository remains **Private Alpha transition**. The green fixture and
local PostgreSQL evidence proves a runnable vertical slice, not a production
claim. The status may change only after the P0 rows are verified and
`MVP-095` closes the complete exit checklist. An unknown row is never treated
as passed by assumption.

The release metadata command also records whether its `HEAD` is backed by a
clean worktree. `--require-clean` is the preflight for a release checkpoint;
it fails closed and does not promote the product by itself.

The complete tracer namespace disposition is recorded in the [MVP-012
migration checkpoint](archive/tracer-migration.md); it distinguishes retained
raw contracts/fixtures from executable compatibility wrappers and untracked
local artifacts.

## Decisions protected from scope drift

These are intentional and must survive all implementation phases:

- Keep the modular monolith, bounded contexts, domain/contracts/services/
  repository layering, typed Protocol ports, and architecture tests.
- Keep contract-first public APIs and generated frontend types.
- Keep Content Fit, Admission Fit, Career Fit, and Workload Readiness as
  distinct semantics; only the latter two remain explicitly out of MVP scope
  until separately implemented and validated.
- Keep `DecisionContext` as the owner of explicit shortlist/final choice;
  recommendations are derived suggestions and never silently prune choice.
- Keep anonymous opaque HttpOnly sessions, account precedence, and explicit
  guest-to-account transfer.
- Keep fail-closed behavior for blocking missing data, while exposing
  degradable and informational gaps where a safe result remains possible.
- Keep university-specific parsing and mapping inside ingestion adapters; do
  not leak source assumptions into university-independent domain core.
- Keep map-agnostic events/campus boundaries and the documented single-replica
  Telegram callback limitation until scale requirements justify shared state.

## Verification protocol

For every later phase, update the current ledger row only after the named
command/test has run against the current code. Historical baseline artifacts
under `backend/tests/fixtures/mvp/` are immutable evidence; intentional
behavior changes require a new migration note and updated assertions rather
than rewriting the baseline silently.
