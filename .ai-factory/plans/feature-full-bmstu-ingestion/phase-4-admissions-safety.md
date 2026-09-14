# Phase 4: admissions and live-source safety

## Goal

Extract admissions from every official detail payload and keep event/campus fixture behavior isolated from live production truth.

## Files and symbols

- `backend/src/andromeda/ingestion/universities/bmstu/parser/admissions.py`: JSON/HTML detail input and all-profile extraction.
- `backend/src/andromeda/ingestion/universities/bmstu/normalizers/admissions.py`: source-code alias resolution and grouped offerings.
- `backend/src/andromeda/ingestion/universities/bmstu/adapter.py`: per-detail admissions orchestration and live event/campus branch.
- `backend/src/andromeda/ingestion/universities/bmstu/normalizers/events.py`, `normalizers/campus.py`: remove fixed known-code assumptions while retaining fixture validation.

## Ordered edits

1. Accept official API detail JSON as an alternative to `__NEXT_DATA__` HTML and parse all profiles in that detail.
2. Normalize direction-level admissions to all canonical programs under the source direction and program-level rows by raw source identity/name.
3. Keep event/campus fixture snapshots only for fixture mode; live mode returns empty event/campus collections unless a real official live source is explicitly present.
4. Ensure source provenance on each admission points to an actually captured detail snapshot.

## Tests and acceptance

- Existing admissions/events/campus tests remain green; add a full multi-detail admissions test and a live-no-fixture regression.
- Command: `python -m pytest backend/tests/ingestion backend/tests/api/test_admission_fit_api.py backend/tests/integration/test_events_live_projection_safety.py backend/tests/integration/test_campus_live_projection_safety.py -q`.
