# Andromeda BMSTU parser

Конфигурационно управляемый парсер для Excel-карты источников МГТУ им. Н.Э. Баумана. Он не переносит 177 полей в код вручную: схема, URL, резервные источники, приоритеты и ограничения читаются из листов `Источники`, `Карта данных`, `Пайплайн` и `Пробелы и риски`.

## Что сохраняется

- `snapshots.jsonl` — HTTP/browser-статус, финальный URL, время, content hash и путь к сырому снимку;
- `records.jsonl` — нормализованные записи университета, структуры, программ, документов, стоимости, приёма и рейтингов;
- `tables.jsonl` — все найденные HTML-таблицы без потери исходных строк;
- `network.jsonl` — JSON-ответы, перехваченные в Playwright-режиме для JS-источников;
- `raw/` — локальные снимки HTML/JSON/PDF с хэшем в имени файла;
- `followup_count`/`followup_pdf_count` в `run.json` — сколько найденных документов было дополнительно скачано и разобрано;
- `facts.jsonl` — одно состояние для каждого поля из карты данных, включая `not_found`, `source_unavailable`, `reserve` и `conflict`;
- `conflicts.jsonl` — расхождения между основным и резервным источником;
- `source_map.json`, `extractions.jsonl`, `run.json` — схема и технический журнал запуска;

Парсер не объявляет источник пустым только потому, что обычный HTTP-клиент получил 403 или SPA вернул HTML без данных. В режиме `auto` он попробует Playwright, если он установлен; иначе сохранит техническое ограничение в `run.json` и `facts.jsonl`.

## Запуск

```powershell
cd backend
python -m pip install -e ".[dev]"

# Только проверка схемы
python -m bmstu_parser inspect-map --map "C:\path\1-Andromeda_BMSTU_source_map_2026.xlsx"

# Быстрый запуск по доступной странице стоимости
python -m bmstu_parser run `
  --map "C:\path\1-Andromeda_BMSTU_source_map_2026.xlsx" `
  --out "..\output\bmstu-run-s10" `
  --source S10 `
  --browser never
```

Для JS/403-источников:

```powershell
python -m pip install -e ".[browser]"
playwright install chromium
python -m bmstu_parser run `
  --map "C:\path\1-Andromeda_BMSTU_source_map_2026.xlsx" `
  --out "..\output\bmstu-run-core" `
  --source S01 --source S02 --source S03 --source S05 --source S07 --source S08 `
  --browser auto `
  --download-documents --max-followups 50 --followup-depth 2
```

Если источники собирались несколькими короткими запусками, их можно свести в одну выгрузку:

```powershell
python -m bmstu_parser merge `
  --run "..\output\bmstu-run-batch-01-2026-09-07" `
  --run "..\output\bmstu-run-batch-02-2026-09-07" `
  --run "..\output\bmstu-run-batch-03-2026-09-07" `
  --run "..\output\bmstu-run-batch-04-2026-09-07" `
  --run "..\output\bmstu-run-s07-final-2026-09-07" `
  --run "..\output\bmstu-run-s08-final-2026-09-07" `
  --out "..\output\bmstu-final-2026-09-07"
```

По умолчанию без `--source` запускаются все 19 источников. Для регулярного запуска лучше указывать отдельную директорию на каждый снимок, чтобы не перезаписывать историю.

## Andromeda: сравнение образовательных программ

Текущий vertical slice использует modular monolith: `andromeda/ingestion` принимает BMSTU sources, предметные модули публикуют typed contracts, `infrastructure` содержит SQLAlchemy/Alembic, а `andromeda/api` отдаёт FastAPI/OpenAPI. Сравнение поддерживает весь учебный план и выбранный семестр, блоки, часы, ЗЕТ, контроль и статусы `both`/`different`/`only_a`/`only_b`.

Полный live-crawl BMSTU классифицирует 2 582 уникальные дисциплины по существующей 22-area taxonomy: 21 область реально встречается в каталоге, а сельское хозяйство отсутствует в опубликованном наборе. Классификация многомерная: у предмета хранится детерминированный вектор весов, исходное имя не заменяется и неоднозначные предметы не объединяются. BMSTU-specific векторы находятся в `andromeda/ingestion/universities/bmstu/mappings/discipline_areas.py`; агрегированный профиль программы считается по учебной нагрузке и доступен в `areaBreakdownA`/`areaBreakdownB`.

Повторяемый fixture-запуск из корня репозитория:

```powershell
python backend/scripts/run_tracer_demo.py --mode fixture --check
```

Для разработки API запускается из нового delivery layer:

```powershell
cd backend
python scripts/run_tracer_bullet.py --mode fixture --database-url sqlite:///./data/tracer.db
python -m uvicorn andromeda.api.main:app --reload --port 8000
```

Межмодульные зависимости проходят через `andromeda.modules.*.contracts.public` и Protocol-порты. ORM-модели не выходят из `andromeda.infrastructure`.

The demonstrable vertical slice uses official BMSTU S01/S06 pages and the linked study-plan documents. The live tracer discovers catalog API pages, every returned detail payload, every linked public study-plan resource and detail-page admissions without a manual program list. It keeps raw bytes and source gaps, validates typed raw DTOs, normalizes domain entities, writes SQLite constraints, and serves the database through FastAPI/OpenAPI.

Study-plan PDFs use the fixed-width text layout produced by Poppler. Install `pdftotext` before running the tracer bullet: on Ubuntu/Debian use `sudo apt-get install poppler-utils`; on Windows install a Poppler distribution and put its `bin` directory on `PATH`. The CI workflow installs and verifies this prerequisite explicitly.

From the repository root, one command runs the complete fixture tracer bullet, starts FastAPI and Vite, waits for both servers, and verifies the compare response:

```powershell
python backend/scripts/run_tracer_demo.py --mode fixture --check
```

Use the same command without `--check` to keep the API and frontend running for a manual demo. The command prints the run id, both program ids, curriculum item count, and source hashes. `--mode live` uses the official BMSTU source and fails closed on source or contract errors.

For a backend-only fixture run:

```powershell
cd backend
python -m pip install -e ".[dev]"
python scripts/run_tracer_bullet.py --mode fixture --database-url sqlite:///./data/tracer.db
python -m uvicorn andromeda.api.main:app --reload --port 8000
```

For the complete official BMSTU catalog, omit `--program-code`/`--program-id`; the runner discovers all catalog directions and profiles automatically. An optional code is an explicit bounded selection for diagnostics only:

```powershell
cd backend
python scripts/run_tracer_bullet.py --mode live --database-url sqlite:///./data/tracer.db --log-level INFO
```

The live run currently discovers 53 official catalog cards, expands them to 54 canonical directions and 152 profiles, projects 134 curricula with 14,910 canonical items, 1,492 admission offerings and 18 explicit study-plan source gaps. A missing or placeholder public document is retained as a provenance-backed gap; it is never replaced by fixture data. Live events and campus points remain empty because no complete official live source is currently in this ingestion scope.

The runner applies `alembic upgrade head` before ingest; it can also be run manually with `python -m alembic -c alembic.ini upgrade head`.

Open `http://localhost:8000/docs` for Swagger UI and `http://localhost:5173/` for the frontend. To refresh the captured official source, install the browser extra and run `python scripts/capture_tracer_fixture.py`; live mode fails closed when the source shape no longer satisfies its contract.

## Важное ограничение

Адаптеры сохраняют сырые таблицы и provenance даже для источников, DOM которых изменился. Для admission SPA сетевые JSON-ответы сохраняются только в browser-режиме. Скачивание связанных документов включается флагом `--download-documents` и ограничивается `--max-followups`; конкурсные/зачислительные PDF разбираются в строки, остальные документы сохраняются как артефакты. Новый PDF-шаблон, который не распознался, не считается подтверждённым фактом.

## Приоритетный PDF плана приёма

Для официального PDF с распределением мест используйте `--priority-pdf`. Его строки имеют приоритет над данными сайта для мест и квот:

```powershell
python -m bmstu_parser run `
  --map "C:\path\1-Andromeda_BMSTU_source_map_2026.xlsx" `
  --out "..\output\bmstu-priority" `
  --priority-pdf "C:\path\БС.pdf"
```

При объединении уже собранных запусков параметр работает так же. Профильные дисциплины из карточек программ намеренно не сохраняются; дисциплины учебных планов остаются.
