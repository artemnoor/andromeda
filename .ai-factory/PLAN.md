# Implementation Plan: Tracer Bullet Closeout

Branch: `codex/contract-first-tracer-bullet`
Created: 2026-09-10

## Original Request

Что делать сейчас:

1. Починить CI до полного green.
2. Убедиться, что одной командой реально поднимается fixture → DB → API → frontend.
3. Проверить один live-run на реальных данных МГТУ.
4. И всё — прекратить улучшать Tracer Bullet.

## Settings

- Testing: yes
- Logging: standard
- Docs: yes — only the command, prerequisites, and stop condition required for this closeout

## Current Evidence

- GitHub Actions run `34478269032` is red at `python -m pytest -q`; the failure is `Curriculum document ... produced no rows`.
- The failed runner installed current `pypdf`, `PyMuPDF`, and `pdfplumber`, but did not install Poppler. The study-plan parser uses `pdftotext -layout` in `backend/src/bmstu_parser/adapters/bmstu.py:_pdf_layout_text`; without that executable it returns an empty string.
- The same test suite passes locally (`29 passed`) because Poppler is available on the development machine.
- `backend/scripts/run_tracer_bullet.py` currently applies migrations and ingests the fixture, but does not start FastAPI or Vite. The documented flow still requires separate `uvicorn` and `npm run dev` commands.
- Live source selection is already implemented in `backend/src/bmstu_parser/tracer/source.py:TracerSource._capture_live` for the official BMSTU S01/S06 pages and the two linked study-plan documents.

## Tasks

### Phase 1: Green CI on a fresh runner

- [x] **Task 1: Make the existing contract suite green in the actual GitHub runner environment** (depends on none)

  **Deliverable:** Update `.github/workflows/ci.yml` so every job that parses the study-plan fixture installs and verifies the declared system prerequisite `poppler-utils`/`pdftotext` before Python tests or the demo smoke. Keep the existing strict pytest, migration, mypy, OpenAPI drift, and frontend build gates; do not skip fixture tests or weaken the source contract. Add a silent layout-extraction preflight against `backend/tests/fixtures/tracer/raw/curriculum.pdf` that checks for the expected plan marker without printing the document body. Update `backend/README.md` only with the prerequisite and the reason it is required. Do not change parser semantics or broaden the domain.

  **Files:** `.github/workflows/ci.yml`, `backend/README.md`.

  **Verification:** Re-run the exact GitHub workflow on this branch. The backend job must reach the runner script and mypy; the frontend job must reach drift check and build; all jobs must conclude `success`. The local reproduction must run `python -m pytest -q` from `backend` in an environment where the same Poppler preflight is visible.

  **Logging requirements:** CI logs only the dependency version, stage name, schema/migration revision, and test/build result at `INFO`; log missing executables and failed preflight as `ERROR`. Never print PDF bodies, API payloads, signed URLs, or credentials. Honor `LOG_LEVEL` in application commands.

### Phase 2: One-command fixture demonstration

- [x] **Task 2: Add one cross-platform command that starts and checks fixture → DB → API → frontend** (depends on Task 1)

  **Deliverable:** Add `backend/scripts/run_tracer_demo.py` as the single demo entry point. It must reuse the existing fixture capture, contract validation, Alembic migration, and `TracerIngestService` path rather than implementing a second ingest. After ingesting the two configured programs into the selected SQLite database, start FastAPI with `sys.executable -m uvicorn` and Vite with the platform-appropriate npm executable, wait for `GET /openapi.json` and `GET /` readiness, call `GET /compare?programIds=program:09.03.01-02,program:09.03.01-12`, and manage child-process shutdown on normal exit, Ctrl-C, or child failure. Provide a bounded `--check` mode that performs the same startup and checks, then exits non-zero on any failure; the default mode keeps both services alive for the user. Use the existing `run_tracer_bullet.py` logic through a callable helper or a small shared runner refactor. Update `backend/README.md`, `frontend/README.md`, and `.github/workflows/ci.yml` with the one command and its setup prerequisites. The documented command from repository root is `python backend/scripts/run_tracer_demo.py --mode fixture`.

  **Files:** `backend/scripts/run_tracer_demo.py`, `backend/scripts/run_tracer_bullet.py`, `backend/README.md`, `frontend/README.md`, `.github/workflows/ci.yml`.

  **Verification:** Add an integration/black-box test under `backend/tests/integration/` for the `--check` lifecycle or its extracted orchestration seams. In CI, install Python, Node, npm dependencies, and Poppler in one smoke job and run the exact `python backend/scripts/run_tracer_demo.py --mode fixture --check` command. Assert the same run id reaches the database, `/openapi.json` is served, compare returns both real programs and non-empty rows, and the frontend dev server returns successfully before the command exits 0. `npm run check-api-drift` and `npm run build` remain separate explicit gates.

  **Logging requirements:** Emit `INFO` stage events for ingest start/commit, API start/ready, frontend start/ready, verification success, and child shutdown; emit `ERROR` with exit code and sanitized endpoint on timeout or child failure. Do not log response bodies or source bytes. Make verbosity controllable by `--log-level`/`LOG_LEVEL`.

### Phase 3: One real live-run and stop

- [x] **Task 3: Execute one live BMSTU smoke and close the Tracer Bullet scope** (depends on Task 2)

  **Deliverable:** Run the same demo entry point once in live mode against the official URLs already defined by `TracerSource`, using a disposable ignored database, for example `python backend/scripts/run_tracer_demo.py --mode live --database-url sqlite:///./data/tracer-live-2026-09-10.db --check --log-level INFO`. Do not fall back to the fixture if live capture fails. Confirm that the live source chain selects S01/S06, resolves both official study-plan documents, validates raw → normalized → domain data, commits both programs and non-empty curricula, serves the API, and renders the frontend-compatible comparison path. Keep the live database and any temporary raw output local and ignored; do not commit source bodies or signed download URLs.

  **Files:** `backend/src/bmstu_parser/tracer/source.py` only if a failure is required to make the already-declared live path work; `backend/scripts/run_tracer_demo.py`, `backend/README.md`, and `.gitignore` only if the closeout command or disposable output needs correction. No new domain entities, endpoints, parser generalization, UI features, or performance work is in scope.

  **Verification:** The one live command exits 0 and reports a run id, exactly the two target program ids, non-zero curriculum item count, source count, and content hashes. During that same run, `/compare` returns HTTP 200 with both program names and rows, and the frontend readiness check succeeds. If the official source contract has drifted, the run must exit non-zero with a structured source error; that is a blocker to closeout, not a reason to silently use fixture data.

  **Logging requirements:** Use `INFO` for source kind, public host/path, HTTP status, byte count, hash, run id, counts, and readiness checkpoints; use `WARN`/`ERROR` for contract rejection, timeout, rollback, or source drift. Redact query secrets, signed URLs, raw documents, and response payloads. Preserve the live-run command and its exit status in the implementation handoff, without adding a general monitoring system.

## Definition of Done

The plan is complete only when the GitHub workflow is fully green, the fixture command starts and verifies the complete local vertical slice, and one live command succeeds on real BMSTU data with the expected provenance and non-empty comparison.

## Stop Rule

After Task 3 passes, mark this plan complete and stop improving the Tracer Bullet. Future entities, new endpoints, parser generalization, UI polish, performance work, deployment, and broader Andromeda coverage are explicitly deferred. Only fixes strictly required to make the three acceptance gates above pass are allowed.
