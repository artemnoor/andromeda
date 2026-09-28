# Phase 3: DATA-API 1.0 and official validator

Plan: [index.md](index.md)
Tasks: 4
Depends on: Phase 2 / Tasks 2-3

## Objective

Add a root `DATA-API.yaml` that follows the organizers' exact DATA-API 1.0 schema, references the canonical Public API v1 OpenAPI, exercises deterministic existing operations with extracted values, and is checked using the official validator in local workflow and CI.

## Current-Code Evidence

| Path | Symbols / evidence | Why it matters |
|------|-------------------|----------------|
| Organizer repo `https://gitverse.ru/stasnorman/example-data-api` | master SHA `8504a6d9b39e6f652bce689d96e88538d7541c6b`; `Example/DATA-API.schema.json`, `Example/DATA-API.template.yaml`, `validate_data_api.py`, `requirements.txt`, `licence.md` | Pin the exact official schema/validator revision; schema is Draft 2020-12 and validator also checks variable order, duplicate IDs, path params and OpenAPI operations. |
| `backend/tests/api/test_assistant_query.py` | deterministic metric comparison case | Exact Russian assistant query returns a complete metric-comparison envelope without live Jev or LLM. |
| `backend/tests/api/test_andromeda_api.py` | source fixture includes `program:bmstu:09.03.01-02` and `...-12`, curriculum and admission facts | Establishes real representative fixture data for detail, curriculum, admissions and comparison checks. |
| Root `openapi.json` | generated Public API v1 | DATA-API's `api.openapi` must be cross-checked against this exact public contract. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| `scripts/data_api/validate_data_api.py` | create | Exact upstream validator script from pinned GitVerse commit; preserve upstream copyright/author text. |
| `scripts/data_api/DATA-API.schema.json` | create | Exact official DATA-API 1.0 JSON Schema from the same commit. |
| `scripts/data_api/UPSTREAM.md` | create | Repository URL, commit SHA and copied-file SHA-256 hashes. |
| `scripts/data_api/UPSTREAM-LICENSE.md` | create | Preserve upstream use/attribution terms verbatim. |
| `scripts/data_api/upstream-requirements.txt` | create | Preserve upstream validator dependency declaration as provenance; execute in the existing locked backend dev environment instead of adding runtime dependencies. |
| `DATA-API.yaml` | create | Root organizer contract with public base URL placeholder, relative `openapi.json`, public-only role and deterministic checks. |
| `.github/workflows/andromeda-ci.yml` | modify | Run the exact official validator/schema after Public OpenAPI export and snapshot drift checks using the locked backend dev environment. |
| `scripts/andromeda.py` | modify | Add a `data-api` command and call it from the `fast` gate, which is part of full verification, with explicit schema and OpenAPI paths. |
| `scripts/check_docs.py` or `docs/api.md` | modify | Document validator command and link the DATA-API/OpenAPI files. |

## Task 4: Add and validate deterministic DATA-API checks

### Intent

Give the organizers a reproducible contract-level smoke scenario that proves Andromeda exposes representative Public API v1 behavior. The official validator's PASS is the acceptance; YAML syntax alone is insufficient.

### Implementation Steps

1. Copy `validate_data_api.py`, `Example/DATA-API.schema.json`, and `licence.md` from GitVerse `stasnorman/example-data-api` commit `8504a6d9b39e6f652bce689d96e88538d7541c6b` without semantic edits. Preserve upstream attribution and record SHA-256 hashes in `UPSTREAM.md`.
2. Pin validator-only `PyYAML` and `jsonschema` dependencies in `requirements.lock`; do not add either solely for DATA-API to Andromeda runtime dependencies.
3. Create `DATA-API.yaml` from the official template. Set `schemaVersion: "1.0"`, solution name `Andromeda`, omit unknown team IDs, use an HTTPS `.example` base URL with a clear comment that the organizer deployment URL must replace it, and set `api.openapi: ./openapi.json`.
4. Define public role checks for `/api/v1/health/live`, university/program lists, two fixture-backed BMSTU program details, curriculum, admissions, comparison, and a deterministic policy assistant query about the fourth EGE rumor.
5. Use DATA-API `extract` and `${variable}` substitution to pass exact IDs from detail responses into curriculum, admissions and comparison. Declare dependencies explicitly and assert stable response fields/body fragments from actual OpenAPI DTOs.
6. Mark GET checks repeatable and the assistant query non-repeatable because it creates an owner-bound, TTL-limited QuerySession. Do not add `DecisionContext` to the recurring smoke flow because its first read creates a stored context. Do not claim the validator executes HTTP requests; it validates the DATA-API document, its semantics and OpenAPI mappings.
7. Add `scripts/andromeda.py data-api` and call it from `fast` (and transitively `full`). In CI, run the official validator after confirming canonical `openapi.json` matches a fresh backend export.
8. Run the official script directly and through the repository wrapper; require exit code 0 with no warnings. Fix actual contract errors or variable/path ordering rather than weakening the validator.

### Required Interfaces and Contracts

- `DATA-API.yaml` must validate against the official schema at the pinned upstream revision.
- OpenAPI source: repository root `openapi.json`, OpenAPI 3.1.0, Public API v1 only.
- Role: `public` for all listed checks; no test credentials, cookies, bearer tokens or API keys in the YAML.
- The required scenario uses deterministic public operations and fixture-backed BMSTU canonical programs; its assistant query is recognized as a policy question and uses the deterministic fail-closed path, without live Jev, LLM, external parsing, live university websites, admin APIs or canonical data mutation. It creates one bounded assistant QuerySession.
- API base URL remains a placeholder until an organizer-accessible HTTPS deployment URL is provided; local validator PASS is independent of network execution.

### Error Handling and Logging

- Validator exit code 1 means DATA-API/schema/OpenAPI mismatch and fails local/CI gate; exit code 2 means validator setup or file-read failure and also fails.
- No user session or application secret is added to DATA-API, CI variables or logs.
- Keep assistant check repeatability explicitly `false`; do not suppress or hide session creation.

### Tests

- Run official upstream validator with explicit schema and OpenAPI.
- Run repository wrapper `python scripts/andromeda.py data-api`.
- Add unit/contract test for the repository wrapper's selected pinned paths/arguments if the wrapper has branching logic.
- CI job must fail for stale Public OpenAPI, wrong path/method, unknown extracted variable, malformed schema version or leaked secret header.

### Acceptance Criteria

- Official validator prints its success confirmation and exits 0 locally.
- The identical pinned validator/schema check runs in CI.
- All DATA-API paths and methods exist in canonical Public API v1 OpenAPI.
- The scenario transfers extracted identifiers between checks, remains deterministic, and contains no real URL credentials.

### Verification

- `python scripts/data_api/validate_data_api.py DATA-API.yaml --schema scripts/data_api/DATA-API.schema.json --openapi openapi.json`
- `python scripts/andromeda.py data-api`
- Expected result: official DATA-API 1.0 success message, exit code 0, no warnings.

## Phase Risks and Mitigations

- Risk: organizer schema changes upstream. Mitigation: pin commit and hashes; update only through an explicit reviewed vendor refresh.
- Risk: `.example` base URL cannot run a hosted HTTP scenario. Mitigation: state the required replacement in docs; do not invent a deployment hostname.
- Risk: referenced BMSTU fixture programs change. Mitigation: use stable canonical IDs already present in the fixture regression corpus and test the detail → curriculum/admissions → comparison path against the fixture DB.
- Risk: assistant check leaves test rows. Mitigation: run it once per DATA-API scenario, declare non-repeatable, and rely on the existing TTL; omit context mutations.

## Phase Completion Checklist

- Task 4 satisfies all acceptance criteria.
- The actual upstream validator exits 0.
- `index.md` Task 4 checkbox is updated immediately after verification.
