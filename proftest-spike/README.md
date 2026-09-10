# Andromeda Proftest Spike

Отдельное приложение для проверки гипотезы: интересы и предпочтения пользователя
сопоставляются не с абстрактной профессией, а с содержанием реальных учебных
планов. Spike не импортируется основным Andromeda backend и не обращается к его
БД, ORM, parser output или файлам.

## Архитектура

```text
Andromeda API (HTTP)
        ↓
backend/api_client        strict read DTOs
        ↓
catalog                    загрузка и TTL-кэш в памяти
        ↓
program_fingerprints       workload → areas → activities → evidence
        ↓
questions → profiling      answers → UserProfile
        ↓
adaptive → matching        candidate spread → deterministic score
        ↓
explanations → API         evidence-backed recommendations
        ↓
frontend                   только Spike API / OpenAPI types
```

Внутри backend крупные блоки разделены на `api_client`, `catalog`,
`program_fingerprints`, `questions`, `profiling`, `adaptive`, `matching` и
`explanations`. Публичные границы проходят через Pydantic DTOs; ORM-моделей в
Spike нет.

## Данные

В production path Spike вызывает только:

- `GET /programs`;
- `GET /programs/{id}/curriculum`;
- `GET /discipline-areas` — опциональный справочник.

Из curriculum используются программа, исходное название дисциплины, семестр,
часы, ЗЕТ, форма контроля, группа, позиция и weighted `areaWeights`. В текущем
Andromeda API area vector приходит с ключом `code`; Spike принимает его на
границе как canonical `area`, сохраняя остальные строгие поля DTO.

## Как считается результат

`ProgramFingerprint` строится автоматически из учебного плана:

- часы — основная база нагрузки, ЗЕТ — fallback при нулевых часах;
- weighted area vector раскладывает каждую дисциплину по 22 областям;
- из областей вычисляются subject shares, activity signals, группы и семестры;
- исходные названия сохраняются в evidence;
- distinctive disciplines считаются по межпрограммной редкости нормализованного
  названия и не объединяют неоднозначные совпадения.

`UserProfile` строится после ответов и содержит отдельные positive subject
weights, activity weights, anti-interest negative weights, confidence и
adaptive answers. Основной Content Fit:

```text
0.55 × subject_fit
+ 0.25 × activity_fit
+ 0.20 × distinctive_fit
- 0.60 × anti_penalty
```

Результат округляется до целого и ограничивается диапазоном `0..100`.
Workload readiness, Career Fit и Admission Fit присутствуют в контракте как
`not_available` и не влияют на Content Fit.

Адаптивный вопрос выбирается только после предварительного ranking: берутся
значимые области/активности с максимальным разбросом среди кандидатов. Если
текущий каталог недостаточно различается, API возвращает `status=skipped` и
объясняет причину.

## Запуск

Сначала подними существующий Andromeda API. Например, fixture-данные можно
подготовить так:

```powershell
python backend/scripts/run_tracer_bullet.py --mode fixture `
  --database-url sqlite:///./backend/data/proftest-spike-demo.db
$env:BMSTU_DATABASE_URL = "sqlite:///./backend/data/proftest-spike-demo.db"
$env:PYTHONPATH = "$PWD/backend/src"
python -m uvicorn andromeda.api.main:app --host 127.0.0.1 --port 8000
```

Затем из корня репозитория запусти Spike runner:

```powershell
python proftest-spike/scripts/run_spike_demo.py `
  --andromeda-base-url http://127.0.0.1:8000
```

Runner проверяет upstream по `/openapi.json`, запускает Spike backend и Vite,
загружает каталог по HTTP, прогоняет пять personas и после проверки безопасно
останавливает дочерние процессы. Для ручного браузерного просмотра используй
`--keep-alive`; по умолчанию runner завершается после проверки.

Ручной frontend:

```powershell
cd proftest-spike/frontend
npm ci
$env:VITE_API_BASE_URL = "http://127.0.0.1:8100"
.\node_modules\.bin\vite.cmd --host 127.0.0.1 --port 5174
```

## Проверки

Из корня репозитория:

```powershell
python -m pytest proftest-spike/tests -q
python -m mypy --strict proftest-spike/backend/src/proftest_spike
python -m mypy --strict proftest-spike/scripts/run_spike_demo.py
```

Из `proftest-spike/frontend` при запущенном Spike API:

```powershell
npm ci
npm run generate-api
npm run check-api-drift
npm run test:unit
npm run build
npm run test:e2e
```

Playwright E2E покрывает базовый проход, adaptive skipped/ready состояние,
anti-interest с интенсивностью, detail screen, reload/restore и desktop/mobile
проекты. Скриншоты visual QA сохраняются в `proftest-spike/output/playwright/`.

## Ограничение текущего Spike

Fixture-каталог, доступный через текущий API, содержит две реальные программы и
212 curriculum positions. Поэтому на этой выборке адаптивный вопрос честно
пропускается: разброс между кандидатами недостаточен. Unit-тесты adaptive
selector отдельно проверяют выдачу вопроса на различающемся каталоге. Перед
интеграцией нужен versioned bulk read-contract для fingerprints; детали — в
[`docs/andromeda-api-gaps.md`](docs/andromeda-api-gaps.md).

Итог визуальной и функциональной проверки записан в
[`docs/spike-report.md`](docs/spike-report.md). После этого Spike scope
завершён; интеграция профтеста в основной Andromeda в этот scope не входит.
