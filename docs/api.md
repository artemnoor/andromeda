[← Архитектура](architecture.md) · [Back to README](../README.md) · [Конфигурация →](configuration.md)

# API

FastAPI-приложение `andromeda.api.main` публикует OpenAPI на `/openapi.json`. Frontend использует только эти HTTP endpoints; `frontend/src/api/generated.ts` создаётся из спецификации.

## Программы

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/programs` | Список программ для выбора A/B |
| GET | `/programs/{id}` | Карточка программы |
| GET | `/programs/{id}/curriculum` | Позиции учебного плана |

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

## See Also

- [Архитектура](architecture.md) — почему API не импортирует ORM.
- [Конфигурация](configuration.md) — адреса и переменные окружения.
- [Тестирование](testing.md) — OpenAPI drift и API integration.
