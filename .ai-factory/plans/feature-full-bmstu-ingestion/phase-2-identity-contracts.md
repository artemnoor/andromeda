# Phase 2: identity and raw/canonical aggregates

## Goal

Represent all directions/profiles without invalid foreign keys or collisions while preserving old fixture IDs and raw source values.

## Files and symbols

- `backend/src/andromeda/ingestion/contracts/raw.py`, `backend/src/bmstu_parser/contracts/raw.py`: `RawDirectionRecord`, `RawProgramRecord`, `RawAdmissionRecord`, `RawCurriculumRow`, `RawTracerBundle`.
- `backend/src/andromeda/ingestion/contracts/normalized.py`, `backend/src/bmstu_parser/contracts/domain.py`: `CanonicalSnapshot`, `NormalizedTracerSnapshot`.
- `backend/src/bmstu_parser/tracer/normalizer.py`: `normalize_bundle`, program identity derivation and direction split.
- `backend/src/andromeda/ingestion/universities/bmstu/identity.py`: deterministic source-to-canonical identity resolver.
- `backend/src/andromeda/modules/programs/domain/entities.py`, curricula domain contracts and `shared/contracts/ids.py`: only additive/compatibility validation changes required by the chosen identity policy.

## Ordered edits

1. Add plural `directions` and `source_gaps` while retaining singular first-direction aliases for existing consumers.
2. Preserve raw profile code/name and compute canonical code from valid numeric source code or stable hash suffix with collision probing; validate `direction_id` membership.
3. Normalize combined direction labels into valid codes and attach ambiguous profiles deterministically to the first source direction, recording the ambiguity as a gap/quality fact.
4. Permit curricula to be absent only when a program-level source gap exists; keep every present curriculum non-empty.
5. Map raw admission/curriculum source codes to canonical program codes before normalization without discarding raw values.

## Tests and acceptance

- Unit-test stable identity across input order, duplicate source codes, slash/Unicode/parenthetical codes and combined directions.
- Validate old fixture IDs are unchanged and full synthetic snapshot has unique programs, directions, curricula/items and gap keys.
- Command: `python -m pytest backend/tests/contracts backend/tests/ingestion -q`.
