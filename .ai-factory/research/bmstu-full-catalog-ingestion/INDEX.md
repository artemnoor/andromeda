<!-- aif:research-mode:ultra -->

Topic: Полный каталог BMSTU ingestion
Slug: bmstu-full-catalog-ingestion
Updated: 2026-09-14
Status: active

# Исследование: полный каталог BMSTU ingestion

## Artifact Index

| Артефакт | Назначение |
| --- | --- |
| [RESEARCH.md](RESEARCH.md) | Факты, evidence, ограничения источников и критерии успеха |
| [C4-CONTEXT.md](C4-CONTEXT.md) | Граница внешних официальных источников и Andromeda |
| [C4-CONTAINER.md](C4-CONTAINER.md) | Поток catalog/detail/document/DB внутри ingestion |
| [C4-COMPONENT.md](C4-COMPONENT.md) | Владельцы динамического обхода и canonical projection |
| [ADR-0001.md](ADR-0001.md) | Решение по multi-direction и source-gap identity |

## Active Summary (input for /aif-plan)

<!-- aif:active-summary:start -->

- Цель: заменить tracer-путь, ограниченный двумя профилями `09.03.01-*`, на автоматический обход официального BMSTU catalog API, всех detail payloads и связанных study-plan документов с атомарной загрузкой canonical snapshot.
- На 2026-09-14 официальный API вернул 53 карточки направлений и 152 profile entries; все 152 профиля содержали `plan`, было 133 уникальные plan-ссылки.
- API пагинируется через `limit`/`offset`; реализация должна продолжать обход до `meta.count`, а не принимать `limit=100` за полный контракт.
- Детали доступны как `https://api.www.bmstu.ru/majors/{slug}` и содержат `additional`, `chairs.items[].educationalProgram.items[]`, включая admissions-поля.
- В profile-кодах есть повторяющиеся direction-level значения (`12.03.04`) и source-формы с `/`, Unicode dash и скобками; canonical identity нельзя строить только из необработанного `code`.
- Study plans требуют resolver: официальный BMSTU detail ссылается на Yandex public resource напрямую или через `clck`; для `type=file` download URL находится в `file`, для `type=dir` — в `_embedded.items[].file`.
- Доступность study plans является частичной: директории без файлов и placeholder `Заглушка.docx` должны попасть в явные source gaps; программа и admissions при этом не должны исчезать из snapshot.
- Текущие `TARGET_DIRECTION_CODE`, `TARGET_PROGRAM_CODES`, `S06_DETAIL_URL`, positional fallback документов и фиксированный compare URL — tracer-specific ограничения. Они допустимы только для legacy fixture/demo compatibility, не для live discovery.
- Существующие public contracts и modular boundaries сохраняются: additive `directions`/`source_gaps` допускает старый singular alias, а program IDs остаются стабильными для уже валидных numeric profile codes. Невалидные/неуникальные source-коды получают deterministic internal suffix с сохранением исходного source code и имени в raw provenance.
- Taxonomy остаётся существующей 22-area taxonomy; классификация — deterministic exact mappings + ordered rules, с проверкой положительных весов и суммы `1.0000`. Runtime LLM запрещён.

<!-- aif:active-summary:end -->

## Sessions

<!-- aif:sessions:start -->

- 2026-09-14: local context/rules/architecture/test audit; current branch `feature/full-bmstu-ingestion`.
- 2026-09-14: official BMSTU API/catalog read-only crawl and linked Yandex metadata audit.

<!-- aif:sessions:end -->
