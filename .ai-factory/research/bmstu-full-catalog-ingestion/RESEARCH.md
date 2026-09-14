# Исследование полного BMSTU ingestion

Topic: Полный каталог BMSTU ingestion
Slug: bmstu-full-catalog-ingestion
Updated: 2026-09-14
Status: active

## Research question

Как пройти официальный публичный BMSTU catalog без ручного списка программ, сохранить raw provenance, построить валидный multi-direction canonical graph и не потерять программы, для которых учебный план недоступен?

## Evidence

### Official catalog and details

1. `GET https://api.www.bmstu.ru/majors/baccalaureate-and-specialty?limit=20&offset=0` returned a JSON object with `data` and `meta`; `meta.count` was 53. Offsets 0, 20 and 40 returned successive pages. The observed full crawl therefore found 53 catalog cards.
2. The catalog cards expose `slug`, `code` and `name`. The corresponding official detail endpoint is `https://api.www.bmstu.ru/majors/{slug}`; all 53 observed detail requests returned successfully.
3. Detail data contains `additional.code`, `additional.name`, `description`, admissions fields and nested `chairs.items[].educationalProgram.items[]`. The observed crawl found 152 profile entries, 141 distinct raw profile-code strings and 133 distinct `plan` URLs.
4. One detail has the combined direction label `40.05.03 / 40.05.01`. Profile codes also include direction-level codes, slash forms and codes with Unicode dash/parenthetical suffixes. These values do not satisfy the current canonical `DirectionCode`/`ProgramCode` shapes without deterministic normalization.

Official sources: [BMSTU catalog](https://bmstu.ru/bachelor/majors), [BMSTU catalog API](https://api.www.bmstu.ru/majors/baccalaureate-and-specialty?limit=100&offset=0), [BMSTU detail API example](https://api.www.bmstu.ru/majors/informatika-i-vycislitelnaa-tehnika-090301), [BMSTU common information](https://bmstu.ru/sveden/common/).

### Study-plan resolver

1. The API `plan` fields use both `disk.yandex.ru` public URLs and official short links on `clck.ru`/`clck.su`.
2. A Yandex public-resource metadata response for a single file has `type=file` and a top-level `file` URL. A directory has `type=dir` and exposes children through `_embedded.items`.
3. The observed plan audit found 133 unique plan links. Most resolved to downloadable files; several links resolved to empty public directories, and one resolved to the Yandex `Заглушка.docx` placeholder. These are source availability gaps, not permission to fabricate curriculum rows.

The linked documents are treated as source material only because their URLs are published by the official BMSTU catalog/detail API. The BMSTU requested URL remains the program's stable source URL; Yandex metadata/download URLs are captured with hashes for provenance.

### Current implementation constraints

The current tracer source contains `TARGET_PROGRAM_CODES`, `TARGET_DIRECTION_CODE`, a single `S06_DETAIL_URL`, exact two-plan validation, and positional document selection. The modern BMSTU adapter passes the same two-code tuple into the legacy parser and attaches fixture event/campus sources without a live-source branch. The runner also defaults to the two codes and emits a fixed compare example. The repository currently writes one direction and reconciles curricula/items atomically, so multi-direction support belongs in ingestion contracts and the repository boundary, not in API/recommendation logic.

The existing 22-area taxonomy and BMSTU mapping are deterministic and source-owned. The first live study-plan pass produced a much larger vocabulary than the 101-discipline fixture; the final implementation must run a complete vocabulary audit and extend explicit mapping/rules for any unmatched names before declaring coverage.

## Active Summary (input for /aif-plan)

<!-- aif:active-summary:start -->

- Official baseline: 53 catalog cards, 53 detail payloads, 152 profiles and 133 unique plan URLs.
- Pagination is controlled by `meta.count`; live capture must not depend on the two-program tracer constants.
- Plan links require direct-file and directory-item handling plus `clck` resolution. Missing resources become explicit source gaps.
- The repository needs all directions, stable deterministic program IDs and atomic/repeatable projection; events/campus remain fixture-only in live mode.
- All discipline vectors must remain deterministic and sum to `1.0000` over the existing 22-area taxonomy.

<!-- aif:active-summary:end -->

## Data-flow decision

`catalog pages/API → paginated catalog items → detail API payloads → profile records → plan resolver (shortlink → Yandex metadata → file) → PDF rows or source gap → raw bundle → deterministic canonical normalization → existing repository transaction`.

The live path captures no events/campus fixture data. The fixture path keeps the existing two-program demo fixtures so existing API/recommendation/comparison tests continue to exercise their contracts.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| New profile-code shape or duplicate | Keep raw source code; derive deterministic canonical code only when needed; validate uniqueness before projection. |
| Combined direction code | Split valid direction codes for the canonical direction set; attach programs to the first source direction when the source profile cannot disambiguate, and record the source fact/gap. |
| Missing Yandex file | Capture metadata snapshot and `source_gap`; omit only curriculum rows, never the program/detail/admission record. |
| Duplicate plan used by profiles | Fetch/parse each resolved document once, then project rows to every profile whose source plan points to it. |
| Catalog changes between runs | Hash every response, keep source snapshots immutable, and let the repository reconcile only the current canonical graph in one transaction. |
| Generic taxonomy fallback | Report exact/rule/unmatched counts and add checked-in mappings/rules before full-ingestion acceptance. |

## Open questions resolved by implementation defaults

- No manual program list is required. Explicit program selectors remain an opt-in debugging/fixture feature.
- Existing singular `direction`/legacy aggregate fields remain compatibility aliases for the first canonical direction; new full snapshots carry all directions.
- A source gap is a first-class raw/canonical quality record and is persisted through the existing raw source-record audit path.

## Success signals

- Live catalog count, detail count, profile count and plan-link count are emitted in structured logs and the runner payload.
- Every discovered profile has one canonical program ID; every program has either a curriculum with at least one item or an explicit source gap.
- All canonical IDs are unique; all curriculum discipline IDs resolve; every area vector has positive weights summing to `1.0000`.
- Re-running the same snapshot produces no duplicate domain rows and keeps the API/recommendations/comparison contracts green.

## Sessions

<!-- aif:sessions:start -->

- 2026-09-14: local context, rules, architecture and tests read.
- 2026-09-14: official catalog/detail and linked plan metadata audit.

<!-- aif:sessions:end -->
