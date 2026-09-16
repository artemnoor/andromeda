# Phase 8: verification, commit and CI

## Goal

Run the requested gates, fix only blocking findings, and hand off a clean feature branch without merge.

## Commands

1. From `backend`, run the CI backend gates: `python -m pytest -q` and `python -m mypy`; the mypy file scope is owned by `backend/pyproject.toml`.
2. From the repository root, run the CI SQLite fixture smoke: `python backend/scripts/run_tracer_bullet.py --mode fixture --campus-fixture-dir backend/tests/fixtures/campus/raw --database-url sqlite:///backend/data/ci.db --log-level ERROR`.
3. From `backend`, run `python -m alembic upgrade head` against fresh SQLite and configured PostgreSQL, then run repeat-ingestion and invariant checks. If no local PostgreSQL DSN is configured, record the local skip; the CI PostgreSQL job remains required.
4. Run the contract/frontend CI gates: export OpenAPI with `python backend/scripts/export_openapi.py --out frontend/openapi.ci.json`, then from `frontend` run `npm run check-api-drift` with `OPENAPI_FILE=openapi.ci.json`, `npm run test:unit` and `npm run build`; from `frontend-next` run `npm run lint` and `npm run build`.
5. Run `git diff --check` and `git status --short` with explicit review of pre-existing dirty paths. Run strict architecture/rules verification and code review of only the BMSTU/full-ingestion diff.
6. If a blocking test/review finding occurs, apply a narrow fix, rerun strict verification/review and repeat until green or a genuine external blocker remains.
7. Stage only changed BMSTU/contract/repository/migration/test/doc/plan/research paths, verify `git diff --cached --name-only`, commit on `feature/full-bmstu-ingestion`, push, then inspect GitHub Actions status if remote/credentials permit. Do not claim the combined branch is merge-ready while later uncommitted paths remain outside the verified commit.

## Acceptance

Final handoff lists counts from the actual full ingestion run, source gaps, taxonomy coverage, removed tracer hardcodes, exact test/CI results and merge readiness. No merge is performed.

## Local verification evidence

- [x] Current backend verification: `340 passed, 6 skipped, 3 warnings`; `python -m mypy`: no issues in 320 source files; `python -m compileall -q src scripts`: passed. These are the exact backend command families used by CI (`python -m pytest -q` and `python -m mypy` from `backend`).
- [x] Full BMSTU live-ingestion baseline `ingest:78c2b34552824712af75ba8198b9bea7`: 54 directions, 152 programs, 134 study plans, 14,910 curriculum items, 1,492 admissions, 18 source gaps, 319 captured snapshots, 0 events and 0 campus points.
- [x] Current fixture repeat/idempotence and DB invariants: canonical IDs unique, valid discipline weights, no orphan curriculum rows, repeat ingestion produces no duplicate canonical rows; fixture smoke reports 212 curriculum items, 2 study plans, 0 source gaps and 101 unique disciplines. Alembic head is `0012_neutral_curriculum_items`.
- [x] PostgreSQL integration tests: `4 skipped` because no local DSN is configured; the CI workflow provisions PostgreSQL.
- [x] Staged review: `git diff --cached --check` passed, staged paths are limited to the BMSTU ingestion/contracts/repository/tests/docs/AIF scope, and live target hardcode scan is clean. The requested `aif-*` executables are unavailable in this environment; their rules/verify/review gates were run manually and documented.
- [x] Push and GitHub Actions status check for the full-ingestion commit `b68bacb`: run `34872246737` is green for all jobs; no merge was performed. The current working tree contains later uncommitted changes, so that CI result does not certify the combined uncommitted state.
