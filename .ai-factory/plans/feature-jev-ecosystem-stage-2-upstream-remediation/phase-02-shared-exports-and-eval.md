# Phase 02: Shared exports and evaluation corpus

Plan: [index.md](index.md)
Tasks: 4–5
Depends on: Phase 01 / Tasks 2–3

## Objective

Produce native upstream inputs and real typed evaluation observations while keeping fixture evidence separate from production calibration evidence. This phase does not enable production Jev and does not alter user-facing decisions.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|---|---|---|
| `backend/scripts/jevcal_export.py` | export main/helpers | Current output is custom `jevcal-export.v1`, uses `expected`, and never calls upstream loaders/commands. |
| `backend/evals/jev/fixtures/` | current JSONL corpus | Five definitions have three rows each; one heldout row is not production calibration. |
| `backend/evals/jev/system_one_evaluator.py` | `OfficialSystemOneQuestionFactory`, evaluator | Existing eval boundary is reusable but currently targets stale SDK/API and a generic Noul-only shape. |
| `backend/src/andromeda/infrastructure/jev/question_registry.py` | registry loader | Task 3 supplies the shared definition projection. |

## Files to Change

| Path | Action | Required change |
|---|---|---|
| `backend/scripts/jevcal_export.py` | replace implementation | Export the actual jevcal dataset/question contract and call upstream validation. |
| `backend/evals/jev/fixtures/` | reorganize/add metadata | Mark as fixture-only and preserve current small corpus for wiring tests. |
| `backend/evals/jev/production/` | create ignored/runtime-configured path | Define a production corpus contract; do not commit private/raw production rows. |
| `backend/evals/jev/system_one_evaluator.py` | modify | Use real System One Adapter v0.2.0 and official typed question primitives/usage. |
| `backend/evals/jev/exporters.py` | create or use Task 3 exporter | Centralize native serializers without moving registry ownership. |
| `backend/tests/evals/` | create/modify | Test native schemas, corpus separation, redaction and evaluation protocol. |

## Task 4: Export the registry/corpus into the exact upstream jevcal input format

### Intent

Export `QuestionRegistry` and Andromeda evaluation corpus data into the exact input format expected by upstream jevcal. The exporter remains Andromeda-owned and may perform serialization, normalization, validation and provenance emission; it must not reimplement calibration logic.

### Implementation Steps

1. Replace the custom row builder in `backend/scripts/jevcal_export.py` with an Andromeda-owned command that loads `QuestionRegistryExport` and emits the exact upstream jevcal question/dataset format expected by the pinned source. Use the actual `labels`/target field names and preserve stable example IDs, definition IDs, definition versions and split labels in sidecar metadata.
2. Call the pinned upstream jevcal loader/linter (`jevcal lint` or its public module equivalent) immediately after writing a temporary export. The exporter must fail if native parsing rejects the file.
3. Keep `backend/evals/jev/fixtures/` as a committed, synthetic, minimal corpus for schema/wiring. Add a separate production corpus input contract that is supplied by configuration and is never committed with private user text.
4. Produce a manifest containing `registry_hash`, dataset SHA-256, source kind (`fixture` or `production`), number of rows per definition, definition versions, and whether labels are human/fixture. Do not produce accuracy, ECE or threshold values in this task.
5. Enforce that fixture data cannot be passed to a production calibration command unless an explicit `--fixture`/offline flag is used; production mode must reject a fixture source. Do not move threshold selection, confidence measures, ECE, holdout scoring or lock compilation into this exporter; those remain upstream jevcal responsibilities in Task 7.

### Required Interfaces and Contracts

- Input: registry export, JSONL/CSV/Parquet rows with stable ID, native target/label, definition ID/version, and sanitized state/input.
- Output: native jevcal questions/dataset files plus `export-manifest.json`.
- A dataset row with no label, unknown definition, mismatched version, duplicate ID or private-field marker is rejected.
- The exporter is Andromeda-owned data transformation/provenance code; it never selects thresholds or computes calibration metrics.

### Error Handling and Logging

- Log `INFO` with source kind, rows by definition, registry hash and dataset hash.
- Log `ERROR` for upstream lint failure, missing labels, duplicate IDs, schema mismatch or production/fixture misuse.
- Never log raw state, free-form question text, expected private answers, or complete rows.

### Tests

- Test current fixture export against pinned jevcal lint and native loader.
- Test production mode rejection of fixture source and fixture mode rejection of unlabeled rows.
- Test stable dataset hash, duplicate IDs, version mismatch, unsupported target and PII redaction.
- Commands: `uv run --extra evaluation python backend/scripts/jevcal_export.py --source fixture --check`; focused pytest for exporters.

### Acceptance Criteria

- The produced artifact is accepted by the real pinned jevcal parser/linter.
- The exporter contains no local threshold-selection, ECE, confidence-measure or calibration algorithm.
- Fixture and production paths are visibly distinct and production enablement cannot consume the committed tiny fixture accidentally.

### Verification

- `uv run --extra evaluation python backend/scripts/jevcal_export.py --source fixture --check` — expected pass with native schema validation.
- Inspect the manifest — expected no threshold/accuracy claims and explicit `fixture` source kind.
- `rg "_select_threshold|_ece|accuracy|threshold" backend/scripts/jevcal_export.py` — expected no local calibration implementation.

## Task 5: Make System One Adapter evaluation use the real v0.2.0 API and shared registry

### Intent

Keep System One Adapter as a benchmark/evaluation path while replacing stale/local calling assumptions with the upstream `system_one_adapter` API. This supplies comparable raw observations to jevcal; it is not a production provider.

### Implementation Steps

1. Update `backend/evals/jev/system_one_evaluator.py` to import the pinned public `SystemOneAdapterClient`/async equivalent, `Noul`, `Choice`, `Score`, `SystemOneResponse`, and `Usage` from the real v0.2.0 package where required.
2. Replace the generic local protocol/factory assumptions with an explicit adapter contract that receives `QuestionRegistryExport`, builds the correct operation-specific native question, and records definition/version alongside the answer. Preserve a fake model/test transport for offline tests.
3. Capture raw probabilities/confidence only in sanitized evaluation artifacts. Record model, provider, attempts/retries, latency, usage totals, malformed-output retries and schema failures from the upstream response/debug fields. Do not map these values to production acceptance here.
4. Ensure evaluation comparisons run the same corpus and registry version for deterministic policy, official TypeSafe client and System One Adapter. Record a comparable result schema without exposing secrets or raw private text.
5. Keep the module importable only through the evaluation extra and prevent composition root/runtime code from importing it.

### Required Interfaces and Contracts

- `SystemOneEvaluationObservation` includes `definition_id`, `definition_version`, `case_id`, sanitized answer/probabilities, model/provider, usage, retries, latency, schema status and corpus hash.
- The evaluator may use upstream `SystemOneAdapterClient`; it must not call the future production `DecisionModelPort` as a side effect.
- An unavailable API, malformed output after retry budget or missing usage produces an explicit failed observation, not an invented confidence.

### Error Handling and Logging

- Log `INFO` per batch with definition IDs, model, number of cases and aggregate latency; log per-case only at `DEBUG` with case ID hash.
- Log `WARNING` for retry exhaustion, provider unavailable or malformed response, including safe failure code.
- Never log prompts, API keys, raw model response, state or private profile fields.

### Tests

- Use the upstream package’s fake model/transport fixtures or an equivalent local fake to test Noul/Choice/Score, retries and usage aggregation.
- Test evaluator output against a sanitized golden schema and verify System One package is not imported by production composition.
- Commands: `uv run --extra evaluation pytest backend/tests/evals -q`; run a no-network fixture evaluation in CI.

### Acceptance Criteria

- The evaluator invokes actual System One Adapter v0.2.0 code and emits typed usage/answer observations.
- It consumes Question Registry exports and cannot silently use a different instruction/version.
- It remains eval-only; no runtime decision path depends on it.

### Verification

- `uv run --extra evaluation python -m andromeda.evals.jev.system_one_evaluator --fixture` — expected offline report with provider calls replaced by the declared fake.
- `rg "system_one_adapter|SystemOneAdapterClient" backend/src/andromeda` — expected no production import.

## Phase Risks and Mitigations

- Risk: upstream native dataset schema changes. Mitigation: pin revision and run upstream parser/lint in the exporter test.
- Risk: evaluation rows leak private text. Mitigation: sanitizer rejects or hashes disallowed fields and tests inspect serialized output.
- Risk: small fixture is mistaken for calibration. Mitigation: source-kind manifest and production-mode rejection.

## Phase Completion Checklist

- Tasks 4–5 satisfy acceptance criteria.
- The real upstream packages parse fixture artifacts, but no production trust flag has changed.
- Evaluation output is sanitized, versioned and reproducible.
