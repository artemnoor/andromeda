# Phase 5: taxonomy coverage

## Goal

Give every discipline emitted by the full dataset a deterministic valid 22-area vector without runtime LLM classification.

## Files and symbols

- `backend/src/andromeda/ingestion/universities/bmstu/mappings/discipline_areas.py`: exact source vocabulary overrides.
- `backend/src/andromeda/modules/disciplines/services/classifier.py`: ordered BMSTU-relevant rules only when an exact mapping is not available.
- `backend/tests/ingestion/test_bmstu_taxonomy.py` (new): coverage and vector invariants.

## Ordered edits

1. Run the full live/PDF vocabulary audit after parser changes and store the observed names in test fixtures or deterministic mapping data where appropriate.
2. Add explicit mappings for stable BMSTU names and narrow rules for families; use multiple areas for genuinely interdisciplinary subjects.
3. Reject malformed/zero/negative vectors and assert Decimal sum `1.0000` for every emitted discipline.
4. Report exact, rule and unresolved counts; do not hide unresolved names by changing the classifier to universal wholesale. If a name is inherently generic, map it explicitly to universal with a documented rationale.

## Tests and acceptance

- Every unique discipline from the full ingestion result is classified by an exact override or an intentional rule; fallback names are zero or explicitly reviewed.
- Command: `python -m pytest backend/tests/ingestion/test_bmstu_taxonomy.py backend/tests/ingestion/test_bmstu_adapter.py -q`.
