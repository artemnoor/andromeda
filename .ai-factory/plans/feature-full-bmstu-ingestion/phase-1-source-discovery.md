# Phase 1: source discovery and contracts

## Goal

Make live BMSTU capture discover catalog pages/details/plans from official source responses and preserve every response as a hash-addressed snapshot.

## Files and symbols

- `backend/src/bmstu_parser/tracer/source.py`: `TracerSource._capture_live`, plan resolver helpers, catalog pagination helpers.
- `backend/src/andromeda/shared/contracts/enums.py`: `SourceKind` metadata kind.
- `backend/src/andromeda/ingestion/contracts/raw.py` and `backend/src/bmstu_parser/contracts/raw.py`: additive source-gap and raw source identity fields.
- `backend/src/andromeda/ingestion/universities/bmstu/parser/catalog.py`: source-shape helpers for list/detail profile discovery.

## Ordered edits

1. Replace the single fixed detail fetch with a `limit`/`offset` loop controlled by `meta.count`; reject malformed page progress and duplicate catalog slugs.
2. Fetch each official API detail by discovered `slug`; parse nested profile rows and keep the detail source URL on each raw record.
3. Resolve each unique plan URL through redirects/HTML short-link targets and Yandex metadata; read top-level `file` for a file and `_embedded.items[].file` for a directory.
4. Capture metadata and PDF bodies as `RawSourceSnapshot` objects with requested URL, final URL and SHA-256. Capture no fixture event/campus snapshots in live mode.
5. Emit a typed source gap for a published plan with no downloadable document, while retaining the program record.

## Data flow and error handling

Only official `bmstu.ru`, `api.www.bmstu.ru` and BMSTU-published plan links are accepted. Fetch failures for catalog/detail remain fail-closed; individual plan availability failures become source gaps with source URL and reason. Resolver decisions and counts use structured logs.

## Tests and acceptance

- Add parser/source tests for pagination, duplicate slugs, direct Yandex files, directory child files, `clck` resolution and no-file gap.
- Command: `python -m pytest backend/tests/ingestion -q`.
- Acceptance: a captured synthetic multi-page catalog has all discovered detail URLs and distinct snapshot hashes; no target-code constant is consulted by live capture.
