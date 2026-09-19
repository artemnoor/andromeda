# Phase 3: BMSTU/HSE ingestion production readiness

Plan: [index.md](index.md)

Tasks: MVP-020, MVP-021, MVP-022, MVP-023, MVP-024

Depends on: MVP-001, MVP-002, MVP-003, MVP-010

Priority: P0 for safe publication; P1 for adapter hardening

## Objective

Make BMSTU and HSE ingestion repeatable, diagnosable, safe to publish, and
retriable without weakening university-specific adapters or moving their
assumptions into university-independent core code.

The required flow remains:

discovery → fetch/download → HTML/PDF parsing → typed raw data →
normalization/canonicalization → validation → provenance → atomic projection →
diagnostic ingest run.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| Adapter registry and separation | CONFIRMED | backend/src/andromeda/ingestion/registry.py has BMSTU/HSE UniversityAdapterSpec; university-specific code lives under ingestion/universities |
| Fixture vertical paths | PARTIALLY CONFIRMED | backend/tests/ingestion and backend/tests/integration/test_hse_full_ingestion.py/test_bmstu_full_ingestion.py cover fixtures; no full live repeatability evidence was executed |
| Atomic canonical projection | CONFIRMED but incomplete operationally | infrastructure/repositories/ingestion.py uses a projection transaction; audit lifecycle calls are separate |
| Retry robustness | CONFIRMED GAP | BMSTU fetch retries network exceptions but not all 429/5xx cases; HSE Fetcher defaults retries=0 |
| Optional source failures | CONFIRMED GAP | hse/capture.py::_optional_snapshot and bmstu/capture.py optional document paths log gaps without always creating RawSourceGap records |
| Fixture integrity | CONFIRMED GAP | HSE fixture loader computes content hash but does not verify manifest content_sha256 against body |
| SSRF/source allowlist | CONFIRMED GAP | ingestion/contracts/constraints.py validates HttpUrl shape; adapters validate selected official hosts but final redirects/private IPs are not uniformly enforced |
| PDF resource safety | FUTURE RISK | BMSTU PDF parsing uses fitz/pypdf/pdfplumber fallbacks with broad exception handling; pdfplumber caps pages but all parsers need explicit size/page/time policy |
| Mutating source health | CONFIRMED | backend/scripts/source_health.py runs live ingestion; .github/workflows/source-health.yml schedules it without a read-only probe/alert artifact |

## Files to Change

| Future change | Path |
| --- | --- |
| Generic ingestion orchestration | backend/scripts/run_andromeda_ingestion.py, backend/src/andromeda/ingestion |
| BMSTU adapter | backend/src/andromeda/ingestion/universities/bmstu/{capture.py,fetch.py,adapter.py,pdf.py} |
| HSE adapter | backend/src/andromeda/ingestion/universities/hse/{capture.py,fetch.py,adapter.py,parser/*.py} |
| Raw contracts and provenance | backend/src/andromeda/ingestion/contracts/{raw.py,source.py,validation.py} |
| Ingestion repository/run state | backend/src/andromeda/infrastructure/repositories/ingestion.py and modules/admin_ops |
| Ingestion fixture tests | backend/tests/ingestion/, backend/tests/integration/, backend/tests/fixtures/{tracer,hse} |
| Source health workflow | backend/scripts/source_health.py and .github/workflows/source-health.yml |

## Task MVP-020: Define safe fetch, redirect, retry, and resource policy

### Intent

Prevent a university source outage, redirect, oversized document, or hostile
URL from producing a misleading successful run or an unsafe network/file
operation.

### Implementation Steps

1. Define per-adapter allowlists for official source hosts and accepted final
   redirect hosts. Keep public-link exceptions explicit and adapter-owned.
2. Resolve DNS/IP before requests where practical and reject loopback,
   private, link-local, metadata, and reserved targets. Re-check redirect
   destinations instead of trusting only the original URL.
3. Define retry classes: connection reset, timeout, 429, selected 5xx, and
   non-retryable 4xx. Use bounded exponential backoff with jitter and a
   Retry-After ceiling.
4. Give BMSTU and HSE explicit timeout, total request budget, response-size,
   page-count, decompression, and parser-time limits.
5. Mark truncated bodies as errors/source gaps; never parse partial content as
   a complete official document.
6. Preserve browser fallback only where the adapter has evidence of anti-bot
   or JavaScript requirements. Keep browser dependencies optional and fail
   with a named source gap when unavailable.
7. Make all fetch policy values typed and configurable only within safe
   upper/lower bounds. Do not permit an arbitrary user-provided URL in ops
   retry.

### Required Interfaces and Contracts

- SourceAdapter.capture receives a bounded, validated adapter request.
- Raw snapshots include original URL, final URL, content hash, capture time,
  response class, and safe source metadata.
- RawSourceGap distinguishes blocked, unavailable, malformed, truncated,
  optional-missing, and unsupported content.
- Generic core never knows BMSTU/HSE host exceptions.

### Error Handling and Logging

- Log university, source kind, sanitized host, attempt, retry class,
  duration, response status, final safe URL, and run ID.
- Do not log query tokens, cookies, Authorization headers, full body, or
  credentials embedded in URLs.
- A rejected redirect or private IP must have a stable security error code.
- A retry-exhausted source must remain diagnosable in the run record.

### Tests

- Add/update:
  backend/tests/ingestion/test_fetch_security.py,
  backend/tests/ingestion/test_retry_policy.py,
  backend/tests/ingestion/test_source_allowlists.py.
- Cover 429/500/timeout/retry-after, redirect to a disallowed host,
  localhost/private IP, oversized body, truncated body, PDF page limit,
  browser fallback unavailable, and final URL provenance.
- Keep existing
  backend/tests/ingestion/test_bmstu_source_capture.py and
  backend/tests/ingestion/test_hse_parser.py green.

### Acceptance Criteria

- No accepted ingestion URL can resolve to a private/reserved target.
- Retry behavior is deterministic under a fake clock and bounded by a total
  budget.
- Partial/truncated bytes cannot become a completed canonical snapshot.
- Every fetch failure is represented by a stable source-gap/error record.

### Verification

- Run offline mock-server tests with no external network.
- Execute a staging allowlist check against known official sources only when
  explicitly scheduled as operational evidence.
- Review logs for secret and raw-body leakage.

## Task MVP-021: Make BMSTU and HSE parser contracts explicit

### Intent

Prove that university-specific assumptions remain in adapters and that both
adapters produce the same typed canonical contract without pretending their
source structures are identical.

### Implementation Steps

1. For BMSTU, document catalog discovery, detail pages, public study-plan
   links, admissions/orders, events, and campus assumptions in the adapter
   contract.
2. For HSE, document catalog/detail/plan/admission/enrollment traversal,
   program matching rules, address fallback, and optional source behavior.
3. Replace silent parser fallback with a typed parser result containing
   parsed records, warnings, gaps, and confidence/ambiguity reason where
   needed.
4. Remove use of datetime.now().year as an unrecorded source fact; derive
   academic year from source metadata or mark it unknown with a gap.
5. Preserve HSE curriculum semester absence as an explicit unknown; never
   infer semester from row order.
6. Make ambiguous name/code matching produce a source gap and diagnostic
   candidates rather than choosing arbitrarily.
7. Verify admissions/tuition heuristics against source fixtures and record
   route/form/funding identity in canonical records.

### Required Interfaces and Contracts

- Adapter-specific raw DTOs may differ; normalized canonical DTOs remain
  university-independent.
- Canonical program identity must be university-scoped and stable.
- Optional data must be represented as absent-with-reason, not zero or a
  fabricated default.
- Parser warnings do not automatically block non-dependent data; blocking
  gaps do.

### Error Handling and Logging

- Log parser stage, source record key, ambiguity count, and gap code.
- Keep raw source references/hashes, not raw HTML/PDF, in ordinary logs.
- Aggregate repeated row-level warnings to avoid log floods while preserving
  counts in run metadata.

### Tests

- backend/tests/ingestion/test_bmstu_adapter.py
- backend/tests/ingestion/test_hse_parser.py
- backend/tests/ingestion/test_bmstu_admissions_parser.py
- backend/tests/ingestion/test_bmstu_admissions_normalizer.py
- backend/tests/ingestion/test_raw_canonical_contract.py
- backend/tests/integration/test_bmstu_full_ingestion.py
- backend/tests/integration/test_hse_full_ingestion.py
- Add golden parser fixtures for ambiguous match, missing semester, missing
  passing score, optional plan, and changed source markup.

### Acceptance Criteria

- BMSTU and HSE fixture runs produce valid canonical IDs, source hashes,
  provenance, and explicit gaps.
- No generic domain service imports university-specific parser logic.
- HSE and BMSTU parser failures are distinguishable from empty valid sources.
- No current-year or address fallback is silently presented as source fact.

### Verification

- Run both adapter suites and the all-university fixture runner.
- Compare canonical counts and identities with MVP-003 baseline.
- Use a third synthetic adapter fixture to prove generic core does not require
  a BMSTU/HSE branch.

## Task MVP-022: Add pre-publication quality gates and safe projection

### Intent

Ensure a successful process does not publish a sparse or semantically invalid
catalog. Current _check_live_drift only compares coarse counts and the
projection transaction does not quarantine a suspicious capture.

### Implementation Steps

1. Define source completeness expectations per university and source profile:
   required catalog identity, program metadata, curriculum, admission facts,
   and optional events/campus.
2. Replace one coarse minimum-ratio check with typed quality metrics:
   count delta, identity continuity, curriculum coverage, admission coverage,
   parser gap severity, taxonomy unknown rate, and source hash freshness.
3. Add a fail-closed gate for blocking regressions and a degradable path for
   optional data; record both decisions.
4. Stage capture/parse/validate results in an ingestion run before replacing
   current canonical rows. If the gate fails, keep the last known-good
   projection and expose the failed run.
5. Make empty-source behavior explicit: an intentionally empty supported
   source is different from a fetch/parser failure.
6. Keep raw snapshots immutable and link all projected rows to the run/source
   evidence.
7. Add a safe operator override only if it is audited, scoped to a run, and
   cannot be triggered by an arbitrary external URL.

### Required Interfaces and Contracts

- IngestionRun state must include capture, parse, validate, quality-gate,
  projection, and terminal outcome.
- Quality outcome must carry blocking/degradable/informational gaps.
- Canonical readers must see either previous good projection or new complete
  projection, never a half-updated mixture.

### Error Handling and Logging

- Emit structured stage events with run ID, university, source profile,
  counts, gap severity, and quality decision.
- On rejection, retain the reason and previous successful run reference.
- Do not expose raw parser exceptions to public users; expose safe source-gap
  codes and operator detail through admin API.

### Tests

- backend/tests/infrastructure/test_atomic_ingest.py
- backend/tests/integration/test_postgresql_ingestion.py
- backend/tests/integration/test_hse_full_ingestion.py
- Add backend/tests/ingestion/test_quality_gate.py and
  backend/tests/integration/test_failed_projection_preserves_last_good.py.
- Test sparse live-like capture, zero capture, optional source loss,
  invalid taxonomy, duplicate identity, and projection rollback.

### Acceptance Criteria

- A failed or low-quality BMSTU/HSE run cannot replace the last known-good
  canonical projection.
- Every terminal run is diagnosable without reading raw source bodies.
- Quality criteria are measured and versioned per adapter.
- The API can show source gaps without claiming a complete catalog.

### Verification

- Run repeated fixture ingestion and compare identity/count/hash evidence.
- Simulate parser and database failure at each stage.
- Run PostgreSQL transaction tests with a disposable database.

## Task MVP-023: Make retries, recovery, and source health operational

### Intent

Turn admin_ops and source-health from a partially useful control surface into
an operator-safe workflow for both BMSTU and HSE.

### Implementation Steps

1. Extend the allowlisted retry profile contract to identify university,
   fixture/live mode, source revision, and safe configuration version.
2. Add a retry/backoff policy at orchestration level, while preserving
   adapter fetch policies.
3. Add stale-running detection and recovery with an explicit timeout and
   operator-visible state.
4. Separate read-only source availability/contract probe from mutating
   canonical ingestion. The scheduled source-health workflow must not change
   user-visible canonical data by default.
5. Persist source-health result artifacts and alertable status, including
   run ID, source hashes, gap summary, and previous-good comparison.
6. Make HSE retry support symmetrical with BMSTU where the source profile is
   safe and configured.
7. Require explicit idempotency key or run profile identity for operator
   retries.

### Required Interfaces and Contracts

- Admin API remains disabled without configured key and keeps safe 404
  behavior for unauthorized access.
- Retry request is allowlisted and cannot carry URL, shell command, raw
  payload, program IDs, or database target.
- Health probe is read-only; ingestion run is mutating and has separate
  permissions/audit.

### Error Handling and Logging

- Log operator action type, authenticated operator identity class (not key),
  source profile, prior run, new run, and outcome.
- Treat a retry conflict as a safe 409 with a run ID.
- Alert on stale running, repeated source failure, projection rejection,
  and failed recovery without exposing source contents.

### Tests

- backend/tests/api/test_admin_ops_api.py
- backend/tests/integration/test_admin_ops_vertical_slice.py
- backend/tests/infrastructure/test_atomic_ingest.py
- Add HSE retry, stale-run recovery, source-health read-only, and idempotency
  tests.
- Add a scheduled workflow test or script-level contract test that verifies
  source-health does not call mutating projection.

### Acceptance Criteria

- BMSTU and HSE supported retry profiles are explicit and safe.
- A crashed worker cannot leave an unbounded invisible running run.
- Scheduled source health cannot overwrite canonical data unless a separate
  explicitly authorized ingestion step is invoked.
- Every retry is traceable to a prior run and has deterministic terminal
  state.

### Verification

- Run two concurrent retries and a crash simulation against PostgreSQL.
- Inspect admin detail responses for safe, useful diagnostics.
- Verify source-health workflow artifacts and alert conditions in a staging
  dry run.

## Task MVP-024: Verify parser dependencies and clean deployment inputs

### Intent

Make PyMuPDF, pdfplumber, pypdf, BeautifulSoup, Poppler, and browser fallback
requirements explicit and reproducible without removing a dependency merely
because it is heavyweight.

### Implementation Steps

1. Map each parser dependency to concrete module/symbol and source type.
2. Decide which are mandatory for fixture/live profiles and which are
   optional fallbacks.
3. Add startup/preflight diagnostics that state missing system dependency and
   affected source capability.
4. Pin compatible versions or introduce a reproducible dependency lock
   strategy for backend and Telegram packages.
5. Add PDF limits and malformed/encrypted/embedded-resource policy.
6. Ensure Docker images include exactly the needed runtime packages and do
   not copy untracked database artifacts.

### Required Interfaces and Contracts

- Dependency absence yields a typed capability/source gap, not an empty
  successful parse.
- Parser interfaces remain adapter-specific; core sees normalized records.
- Deployment image build must be reproducible from tracked files only.

### Error Handling and Logging

- Startup logs list dependency name/version and safe capability status.
- Parser exceptions are categorized and counted; raw document content is not
  logged.

### Tests

- backend/tests/ingestion/test_bmstu_pdf.py
- backend/tests/ingestion/test_hse_pdf.py
- backend/tests/ingestion/test_source_capture.py
- Docker build and startup smoke from clean checkout.
- Dependency audit job added in MVP-092.

### Acceptance Criteria

- A clean checkout can build and run the supported fixture profile.
- Missing Poppler/browser/PDF dependency produces a useful fail-fast or
  explicitly degraded result.
- No source profile succeeds with silently empty parser output.

### Verification

- Build backend and frontend images from tracked files.
- Run parser fixture suite with each documented optional dependency matrix.
- Record dependency versions in release evidence.

## Phase Risks and Mitigations

- **Risk:** stricter quality gates reject legitimate source changes.
  **Mitigation:** version metrics per adapter, retain last-known-good projection,
  and provide audited operator override only for reviewed runs.
- **Risk:** network hardening breaks public Yandex document links.
  **Mitigation:** model the documented public-host exception and validate
  final redirect host/IP explicitly.
- **Risk:** separating source health delays freshness. **Mitigation:** keep
  health frequent and ingestion scheduled/triggered independently with clear
  freshness metadata.

## Phase Completion Checklist

1. BMSTU and HSE fixture/live-like paths have typed parser, retry, gap, and
   provenance outcomes.
2. Quality gate prevents sparse projection publication.
3. Ingestion runs are retryable, recoverable, and operator-diagnosable.
4. Source health is read-only unless explicit ingestion is authorized.
5. Parser/system dependencies and clean image inputs are reproducible.
