[← Архитектура](architecture.md) · [Back to README](../README.md) · [Admissions →](admissions.md)

# API

FastAPI-приложение `andromeda.api.main` публикует OpenAPI на `/openapi.json`. Frontend использует только эти HTTP endpoints; `frontend/src/api/generated.ts` создаётся из спецификации.

## Программы

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/programs` | Список программ для выбора A/B |
| GET | `/programs/{id}` | Карточка программы |
| GET | `/programs/{id}/curriculum` | Позиции учебного плана |
| GET | `/programs/{id}/admissions` | Source-backed данные поступления |

`GET /programs/{id}/admissions` возвращает strict `ProgramAdmissionsResponse`: каноническую программу и offering-записи по годам, форме и типу финансирования. В offering доступны места, ЕГЭ и минимумы, проходные баллы, квоты и стоимость обучения — только если они опубликованы в доступном источнике. Каждая запись и дочерний показатель содержит provenance с URL, временем capture и хэшем источника. Поля без источника остаются пустыми; значения `0` не используются как замена неизвестности.

`DisciplineResponse` сохраняет `name`/`sourceName` и дополнительно отдаёт `areaWeights` — вектор областей с весами — и `primaryArea`. Каталог областей доступен через `GET /discipline-areas`; он содержит 22 стабильных кода, название, описание и позицию для сортировки.

## Сравнение

```text
GET /compare?programIds=program:09.03.01-02,program:09.03.01-12
GET /compare?programIds=program:09.03.01-02,program:09.03.01-12&scope=semester&semester=1
```

`ComparisonResponse` содержит `programA`, `programB`, `scope`, `rows`, `totalsA`, `totalsB`, `blocks` и `areaBreakdownA`/`areaBreakdownB`. Последние показывают агрегированный вектор содержания программы в выбранной области и режиме. Строка хранит `a`, `b`, статус и `hoursDelta`/`creditsDelta`; у дисциплин сохраняются исходные названия, семестры, блоки, формы контроля и area weights.

Доли и веса передаются как decimal-строки (`"0.4589"`), чтобы frontend не терял точность JSON number. Frontend types генерируются из OpenAPI, поэтому изменение этих полей проходит через drift gate.

Статусы:

- `both` — одинаковые дисциплина и workload;
- `different` — дисциплина есть в обеих программах, workload различается;
- `only_a` / `only_b` — позиция есть только с одной стороны.

## Ошибки

Ответ ошибки имеет strict-поля `code`, `message`, `details`. Основные коды: `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `CONTRACT_ERROR`, `SOURCE_CONTRACT_ERROR`, `INTERNAL_ERROR`.

## Профиль содержания

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/proftest/questions` | Versioned bank scenario-based вопросов без внутренних весов |
| POST | `/proftest/preview` | Строит `UserProfile`, первичный ranking и adaptive selection |
| POST | `/proftest/results` | Строит финальный профиль и TOP рекомендаций с fit/anti-fit evidence |
| GET | `/proftest/profile` | Читает current completed profile anonymous session |
| POST | `/proftest/profile` | Создаёт current profile; повторное создание возвращает `409 CONFLICT` |
| PUT | `/proftest/profile` | Обновляет профиль по optimistic `expectedRevision` |

Оба POST endpoint принимают strict `answers` и optional `adaptiveAnswers`. `UserProfile` строится до matching, а response содержит integer `contentFit`, breakdown компонентов, реальные workload/share и исходные названия отличительных дисциплин. В этих Content Fit responses optional metrics (`workloadReadiness`, `careerFit`, `admissionFit`) возвращаются с `status: "not_available"` и не влияют на scoring. Отдельный endpoint Admission Fit описан ниже и также не меняет этот ranking.

После изменения API frontend-контракт регенерируется из OpenAPI:

```powershell
python backend/scripts/export_openapi.py --out frontend/openapi.json
cd frontend
npm run generate-api
npm run check-api-drift
```

## Recommendations

| Метод | Endpoint | Назначение |
|---|---|---|
| POST | `/recommendations` | Ранжирует реальные программы для готового `UserProfile` |
| GET | `/recommendations/current?limit=10` | Ранжирует программы для current persisted profile |

Request содержит `profile` и `limit` (`1..20`). Профиль — тот же strict public contract, который возвращает proftest. Ответ `RecommendationsResponse` содержит профиль и TOP программ с integer `contentFit`, breakdown (`subjectFit`, `activityFit`, `distinctiveFit`, `antiPenalty`), долями областей и блоков, распределением по семестрам, отличительными дисциплинами и evidence-backed `reasons`/`antiFitReasons`.

Пример минимального запроса:

```json
{
  "profile": {
    "version": 1,
    "interests": ["computer_science_data"],
    "activityPreferences": ["software_creation"],
    "antiInterests": [],
    "preferredSubjectWeights": {"computer_science_data": "1"},
    "preferredActivityWeights": {"software_creation": "1"},
    "negativeWeights": {},
    "confidence": {"value": "1", "answeredBase": 6, "answeredAdaptive": 0},
    "adaptiveAnswers": []
  },
  "limit": 10
}
```

`/recommendations` и `/proftest/results` используют один RecommendationService. Он не импортирует ORM или parser, а получает fingerprints через infrastructure adapter, который делегирует существующий `Program/Curriculum/Discipline` catalog path.

## Personal route

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/personal-route?limit=10` | Строит логический персональный план по current profile |

`GET /personal-route` — read-only orchestration поверх существующих `CurrentRecommendationService`, `EventService` и `CampusService`. Он не создаёт новую сущность профиля, программы, события или точки и не хранит отдельный route snapshot. `limit` ограничен диапазоном `1..20`.

Ответ `PersonalRouteResponse` содержит `status`, `summary`, те же source-backed `recommendations` и последовательность typed `steps`. Шаги имеют только логические типы `explore_program`, `compare_programs` и `attend_event`; позиция означает порядок действия, а не перемещение между местами. Шаг программы ссылается на canonical `programId`, шаг события — на существующий `eventId`, `venueId` и, если точка известна, полную `CampusPointDetailResponse` с карточкой, coordinate/address и university/department/program links. Для онлайн-события `venueId` и `point` остаются `null`.

Без current profile endpoint возвращает стандартный `404 NOT_FOUND`; пустая рекомендационная выдача получает `status: "no_recommendations"`, а отсутствие будущих подходящих событий — `status: "no_events"` при сохранённых шагах программ. События отфильтрованы по рекомендованным canonical program IDs, текущему времени и deterministic UTC ordering. Endpoint не возвращает geometry, directions, расстояния, карту или route optimizer.

Минимальный пример ответа:

```json
{
  "status": "ready",
  "summary": "План по рекомендациям профиля",
  "recommendations": [],
  "steps": [
    {
      "position": 1,
      "kind": "explore_program",
      "reason": "Начните с программы с самым высоким Content Fit",
      "programIds": ["program:09.03.01-02"]
    },
    {
      "position": 3,
      "kind": "attend_event",
      "reason": "Событие связано с рекомендованной программой",
      "programIds": ["program:09.03.01-02"],
      "eventId": "event:bmstu:dod-2026",
      "venueId": "venue:bmstu:main-campus",
      "startsAt": "2026-10-17T08:00:00Z"
    }
  ]
}
```

Frontend client генерирует `PersonalRouteResponse` из `/openapi.json`; для UI используется только логический план, без маршрутизации по карте.

`POST /proftest/results` сохраняет только финальный `UserProfile` (без `AnswerSet` и cookie token). `GET /proftest/profile` и `GET /recommendations/current` используют anonymous HttpOnly session cookie. Если профиля нет или его TTL истёк, API возвращает `NOT_FOUND`; устаревший `expectedRevision` и duplicate create возвращают `CONFLICT`. Session key в БД представлен только SHA-256 hash.

## Admission Fit

| Метод | Endpoint | Назначение |
|---|---|---|
| POST | `/programs/{id}/admission-fit` | Считает отдельную оценку реалистичности поступления для выбранного offering |

Endpoint принимает баллы абитуриента и явный `offeringId` из `GET /programs/{id}/admissions`. Это не подбор программы и не прогноз зачисления: сервер сравнивает введённые значения только с source-backed минимумами и проходным баллом выбранного набора.

Минимальный strict-запрос:

```json
{
  "version": 1,
  "offeringId": "admission-offering:program:09.03.01-02:2026:unknown:budget:direction",
  "applicant": {
    "version": 1,
    "scores": [
      {"subject": "Математика", "score": 90},
      {"subject": "Русский язык", "score": 88},
      {"subject": "Информатика", "score": 92}
    ]
  }
}
```

Поле `offeringId` нужно брать из фактического ответа admissions: год, форма, финансирование и scope могут отличаться между программами и источниками. `score` каждого предмета находится в диапазоне `0..100`; неизвестное поле или дублирующийся после нормализации предмет возвращают `VALIDATION_ERROR`.

Ответ содержит `status`, целочисленный `score` `0..100`, `dataQuality`, три независимые метрики `breakdown`, а также `reasons`, `antiReasons` и `dataGaps`. Decimal-значения баллов и метрик сериализуются строками. У reason сохраняются предмет, введённый факт, reference score и provenance, когда они есть.

Статусы:

- `realistic` — обязательные предметы сопоставлены, известные минимумы не нарушены, а введённая сумма не ниже выбранного проходного ориентира; итоговый score не ниже 80;
- `borderline` — данные полные, но сумма ниже опубликованного проходного ориентира либо итоговый score находится в диапазоне 55–79;
- `unlikely` — нарушен известный минимум, сумма ниже 85% проходного ориентира или итоговый score ниже 55;
- `insufficient_data` — отсутствует обязательный балл или невозможно посчитать доступную метрику.

Ошибки `NOT_FOUND` означают неизвестную программу или offering. Отсутствие admission facts не маскируется нулевыми значениями: API возвращает успешный результат с `dataQuality`/`dataGaps`, а UI показывает, каких фактов не хватает.

## Admissions

Admission API — read-only application path. Route вызывает `AdmissionService`, service читает `ProgramReader` и `AdmissionReader`, а SQLAlchemy projection остаётся внутри infrastructure. BMSTU adapter преобразует detail-page `__NEXT_DATA__` в raw/canonical contracts и связывает записи с canonical `program_id`; HTTP schema не экспортирует ORM-модели.

## See Also

- [Архитектура](architecture.md) — почему API не импортирует ORM.
- [Конфигурация](configuration.md) — адреса и переменные окружения.
- [Тестирование](testing.md) — OpenAPI drift и API integration.
