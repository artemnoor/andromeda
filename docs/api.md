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

Ответ ошибки имеет strict-поля `code`, `message`, `details`. Основные коды: `VALIDATION_ERROR`, `NOT_FOUND`, `CONTRACT_ERROR`, `SOURCE_CONTRACT_ERROR`, `INTERNAL_ERROR`.

## Профиль содержания

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/proftest/questions` | Versioned bank scenario-based вопросов без внутренних весов |
| POST | `/proftest/preview` | Строит `UserProfile`, первичный ranking и adaptive selection |
| POST | `/proftest/results` | Строит финальный профиль и TOP рекомендаций с fit/anti-fit evidence |

Оба POST endpoint принимают strict `answers` и optional `adaptiveAnswers`. `UserProfile` строится до matching, а response содержит integer `contentFit`, breakdown компонентов, реальные workload/share и исходные названия отличительных дисциплин. Optional metrics (`workloadReadiness`, `careerFit`, `admissionFit`) сейчас возвращаются с `status: "not_available"` и не влияют на scoring.

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

## Admissions

Admission API — read-only application path. Route вызывает `AdmissionService`, service читает `ProgramReader` и `AdmissionReader`, а SQLAlchemy projection остаётся внутри infrastructure. BMSTU adapter преобразует detail-page `__NEXT_DATA__` в raw/canonical contracts и связывает записи с canonical `program_id`; HTTP schema не экспортирует ORM-модели.

## See Also

- [Архитектура](architecture.md) — почему API не импортирует ORM.
- [Конфигурация](configuration.md) — адреса и переменные окружения.
- [Тестирование](testing.md) — OpenAPI drift и API integration.
