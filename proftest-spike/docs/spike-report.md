# Proftest Spike — итог проверки

Дата проверки: 10 сентября 2026 года.

## Что реализовано

Сделан отдельный Spike под `proftest-spike/`. Он получает программы и
учебные планы через HTTP, строит `ProgramFingerprint`, превращает ответы в
`UserProfile`, выбирает adaptive-вопрос по разбросу кандидатов, считает
объяснимый Content Fit и отдаёт frontend shortlist реальных программ с
evidence-backed reasons.

Основной Andromeda backend не переписывался и не импортирует Spike.

## Архитектура

Backend разделён на typed-модули:

```text
api_client → catalog → program_fingerprints
questions → profiling → adaptive → matching → explanations → api
```

`AndromedaApiClient` — единственная production-точка доступа к Andromeda.
ORM, DB, parser output и файлы в Spike не используются. Frontend — отдельный
Vite TypeScript app, который вызывает только Spike API; aliases в
`src/api/generated.ts` ссылаются на `generated.openapi.ts`, созданный из
OpenAPI.

## Использованные данные

Проверка прошла на fixture API с 2 реальными BMSTU-программами и 212 позициями
учебного плана (89 + 123). Использовались исходные названия дисциплин, часы,
ЗЕТ, семестры, формы контроля, subject groups и weighted area vectors.

## Fingerprint и профиль

Fingerprint выбирает hours как basis, credits использует при нулевых часах,
раскладывает workload по 22 областям, считает доли областей, группы,
семестры и activity signals. `sourceName` сохраняется; distinctive subjects
определяются по редкости нормализованного имени между загруженными программами
без автоматического объединения неоднозначных совпадений.

`UserProfile` содержит отдельные positive subject weights, activity weights,
anti-interest negative weights, confidence и adaptive answers. Неприязнь к
области — отдельный отрицательный вес, а не нулевой интерес.

## Scoring

```text
Content Fit = clamp(round(
    0.55 × subject_fit
  + 0.25 × activity_fit
  + 0.20 × distinctive_fit
  - 0.60 × anti_penalty
), 0, 100)
```

Результат целочисленный и детерминированный. Workload readiness, Career Fit и
Admission Fit присутствуют как typed `not_available` и в формулу не входят.
Причины показывают область/деятельность, реальную долю или workload и названия
дисциплин из curriculum evidence.

## Adaptive block

После предварительного ranking selector анализирует spread областей и activity
signals среди TOP-кандидатов и может выдать pairwise question. Для текущей
fixture-выборки из двух близких программ API и браузер честно показали
`adaptive.status=skipped` с причиной недостаточного различия. Отдельные unit
тесты проверяют ready path на различающемся synthetic catalog.

## Synthetic personas

Runner прогнал пять профилей через живую цепочку Spike API:

| Persona | Наблюдение |
| --- | --- |
| IT / Software | обе программы получили 23/100 на ограниченном каталоге |
| Engineering | диапазон 6–8/100 |
| Economics / Business | диапазон 3–3/100 |
| Data / Analytics | диапазон 11–12/100 |
| IT + strong physics anti-interest | диапазон 19–21/100; anti-interest уменьшил fit |

Для каждого профиля повторный одинаковый запрос дал ту же сигнатуру ranking.
Anti-interest property прошла: для программы с заметной долей physics score не
увеличился, high-area проверка нашла 1 такую программу. Reasons содержали
названия реальных дисциплин из curriculum evidence.

Числа показывают ограничение двухпрограммного fixture-каталога, а не готовую
рекомендационную калибровку для полного МГТУ.

## Browser и visual QA

Playwright прошёл 4 сценария: два пользовательских сценария на desktop и
mobile. Проверены intro, базовые вопросы, progress, selectable cards,
anti-interest intensity, adaptive skipped state, results, detail и reload/
restore.

В ходе просмотра были исправлены:

- Decimal-поля API корректно преобразуются в числа перед процентами и
  сортировкой в UI;
- редкие области получили labels из полного словаря 22 блоков и больше не
  отображаются как «Семестр …»;
- добавлена favicon, чтобы чисто проходить загрузку страницы без 404;
- Playwright-конфигурация принимает `PLAYWRIGHT_BASE_URL`, поэтому runner и
  ручной порт используют один и тот же E2E suite.

Проверены desktop/mobile screenshots:
`desktop-results.png`, `desktop-result-detail.png`, `desktop-adaptive.png`,
`mobile-results.png`, `mobile-result-detail.png`, `mobile-adaptive.png`.

## Проверки

- backend: 49 passed;
- frontend unit/state: 2 passed;
- Playwright: 4 passed (desktop/mobile × 2);
- `mypy --strict`: backend и demo runner без ошибок;
- TypeScript strict build: passed;
- OpenAPI drift check: passed;
- standalone runner: passed, дочерние процессы остановлены безопасно.

## Перед интеграцией в Andromeda

Следующим отдельным решением нужно согласовать versioned bulk read-contract
`GET /program-fingerprints?programIds=...` (и item endpoint при необходимости)
с `sourceCoverage` и `calculatedAt`, добавить pagination/filtering и загрузить
полный каталог программ. Только после этого стоит калибровать веса на большем
наборе и решать, какие части fingerprint перенести в основной modular monolith.

Профтест не интегрирован в основной backend; следующий scope здесь не начат.
