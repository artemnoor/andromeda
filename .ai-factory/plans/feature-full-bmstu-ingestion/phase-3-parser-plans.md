# Phase 3: full catalog parser and study plans

## Goal

Parse every discovered profile and every available linked study-plan document once, projecting rows to all profiles that reference that document.

## Files and symbols

- `backend/src/bmstu_parser/tracer/parser.py`: `parse_sources`, `parse_captured`, detail and curriculum parsing.
- `backend/src/bmstu_parser/adapters/bmstu.py`: `_study_plan_records` compatibility and PDF-shape handling.
- `backend/src/andromeda/ingestion/universities/bmstu/adapter.py`: dynamic/full-mode orchestration.
- `backend/src/andromeda/ingestion/universities/bmstu/parser/curriculum.py`: resolver/document parser helpers.

## Ordered edits

1. Make parser discovery the default for live snapshots; explicit code filters remain opt-in for fixture/debug only.
2. Parse multiple detail snapshots, deduplicate profiles by deterministic source identity and resolve each plan URL by exact URL rather than body substring or positional order.
3. Parse each unique PDF once and clone typed curriculum rows to every referencing canonical profile; de-duplicate discipline/semester rows deterministically.
4. Add a source gap when metadata exists but no usable PDF is available; fail closed when a required fixture document is silently missing.
5. Log catalog/detail/profile/plan/document/row counts and parse failures without logging bodies or secrets.

## Tests and acceptance

- Synthetic multi-detail test covers shared plan URLs, multiple PDFs, no-file source gap, malformed PDF and missing fixture document.
- Command: `python -m pytest backend/tests/ingestion backend/tests/contracts -q`.
- Acceptance: current official crawl can produce a raw bundle without `TARGET_PROGRAM_CODES`; all profile records are represented.
