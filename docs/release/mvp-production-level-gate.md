# MVP Production Level release gate

**Current decision:** `NOT READY — Private Alpha transition`

This is the current release gate, not a product claim. The repository may use
the `MVP Production Level` label only after every item below has a passing,
reviewable artifact. `UNKNOWN` is never treated as pass.

## Evidence required

| # | Exit criterion | Current status | Required evidence / command |
|---:|---|---|---|
| 1 | Five primary user flows work end-to-end | `PARTIAL` | `python scripts/andromeda.py production-smoke` plus browser suite |
| 2 | No implemented capability is represented by a placeholder | `PASS` | current capability matrix, UI wording tests, explicit out-of-scope claims |
| 3 | BMSTU/HSE ingestion is reproducible | `PARTIAL` | Fixture gate plus the official `source_health.py --mode live --university all` probe on 2026-09-19 accepted BMSTU/HSE as `degraded` (BMSTU 134/134 curriculum+admission programmes; HSE 85/96 curriculum and 49/96 admission programmes); release-owner artifact and repeatability record are still required |
| 4 | Failure, retry, recovery, and last-good state are diagnosable | `PASS` | ingestion recovery/admin-ops tests and run-ID diagnostics |
| 5 | PostgreSQL schema, migrations, and readiness are stable | `PARTIAL` | `python scripts/andromeda.py migrations` passed; disposable PostgreSQL 16 target passed 5 integration/smoke tests on 2026-09-19; clean release/CI and deployment evidence remain required |
| 6 | Critical rules have meaningful tests | `PASS` | [critical test matrix](../test-matrix.md), backend/frontend/Telegram suites |
| 7 | Full CI passes from clean checkout | `PARTIAL` | A `core.autocrlf=false` clean-checkout simulation with documented `npm ci` passed canonical `python scripts/andromeda.py full`; the current worktree also reran it successfully (backend 535 passed/8 skipped, frontend unit 19 passed, Telegram 14 passed, migrations 22 passed, coverage 87%, fixture/production smoke). GitHub Actions has a success for baseline `main` commit `4088116`, but no run exists for this uncommitted implementation snapshot, so an owner-attached run for the release commit is still required |
| 8 | Production-like deployment is runnable | `PARTIAL` | Docker images, compose PostgreSQL/backend/frontend, Caddy TLS gateway, readiness, fixture ingestion, full browser flow, and VM/systemd packaging contract were exercised locally; a clean release checkout/target still needs owner-attached evidence |
| 9 | Frontend loading/error/empty/stale/partial states are honest | `PASS` | `frontend-next/tests/mvp-production-flow.spec.ts`, state and responsive suites |
| 10 | Recommendation explains evidence, uncertainty, and provenance | `PASS` | recommendation evidence/explanation tests and browser rendering |
| 11 | Missing data is typed and actionable | `PASS` | source-gap/provenance contracts and partial-data browser assertions |
| 12 | Security baseline passes | `PARTIAL` | security/request-control/auth tests plus dependency audit in CI |
| 13 | Documentation matches code and operations | `PASS` | `python scripts/check_docs.py`, current docs and deployment contract gate |
| 14 | Critical paths have no unowned tracer shortcut | `PASS` | architecture/dead-surface checks and tracer migration disposition |
| 15 | Production smoke passes after clean deploy and restore | `PARTIAL` | disposable compose backup/restore reached Alembic head `0022_ingestion_concurrency`; failed-image rollback restored readiness and TLS browser smoke passed; clean release artifact and authorized deployment evidence remain |
| 16 | New university onboarding remains adapter/data scoped | `PASS` | adapter contracts, generic-core architecture tests, BMSTU/HSE coexistence |

## Latest local live-source evidence

The repository-controlled live probe was run against a disposable, migrated
SQLite database and wrote the secret-free artifact
`artifacts/release/source-health-20260919.json`. It completed with exit code 0
and explicitly reported `mutatesCanonicalProjection: false`:

| University | Source snapshots | Canonical programmes | Curriculum coverage | Admission coverage | Taxonomy coverage | Source gaps | Blocking gaps | Quality decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| BMSTU | 344 | 134 | 100% | 100% | 100% | 2,817 | 0 | `degraded` |
| HSE | 1,493 | 96 | 85/96 | 49/96 | 84.59% | 122 | 0 | `degraded` |

This is stronger than a fixture-only check, but it is still local evidence from
a dirty worktree. It does not replace an owner-attached clean-checkout CI run,
release repeatability record, or authorized deployment/source-health artifact.

## Reproducible metadata

Generate a secret-free JSON metadata artifact for a candidate release:

```powershell
python scripts/release_evidence.py
```

The output is written under `artifacts/release/` and is intentionally not a
promotion switch. It records the commit, lockfile hashes, regression corpus
hashes, an explicit secret-free worktree state, and the 16 checklist items.
For a candidate release checkpoint, require a clean checkout:

```powershell
python scripts/release_evidence.py --require-clean
```

CI/deployment owners attach their run IDs,
image digests, migration head, backup/restore result, and safe logs to the
corresponding rows.

## Rollback references

Keep all of the following with the release record:

- previous backend/frontend/Telegram image tags or digests;
- previous extracted VM release and the exact standalone `server.js` path;
- applied Alembic revision and compatibility boundary;
- encrypted PostgreSQL backup and isolated restore result;
- fixture/source manifest hashes and current taxonomy/policy versions.

Until rows 7, 8, and 15 are `PASS` with attached release artifacts, the public
status remains Private Alpha transition even if local fixture tests are green.
