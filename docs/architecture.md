[← Быстрый старт](getting-started.md) · [Back to README](../README.md) · [API →](api.md)

# Архитектура

Проект остаётся modular monolith: один backend, одна инфраструктура и явные границы предметных модулей. Микросервисы, Kafka, CQRS и отдельный deployment-модуль в текущий scope не входят.

## Поток данных

```text
BMSTU source
  → ingestion/universities/bmstu
  → raw DTO → normalization → canonical contracts
  → universities / programs / curricula / disciplines
  → infrastructure repositories → SQLite
  → FastAPI/OpenAPI → TypeScript frontend

Для профиля содержания application flow продолжается так:

```text
programs / curricula / disciplines public readers
  → proftest catalog adapter
  → ProgramFingerprint → UserProfile → deterministic matching
  → /proftest/preview|results → generated frontend types
```
```

## Границы

```text
backend/src/andromeda/
├── modules/{universities,programs,curricula,disciplines,comparison}/
├── modules/proftest/{domain,contracts,services,repository}/
├── ingestion/universities/bmstu/
├── infrastructure/{database,repositories,config,logging}/
├── api/{routes,schemas,dependencies}/
└── composition/
```

Предметные модули публикуют `contracts.public` и Protocol-порты. `comparison` получает программы, curricula и disciplines через reader-контракты. SQLAlchemy-модели и `Session` остаются внутри infrastructure.

`proftest` использует те же публичные reader-контракты через собственный typed catalog port; его domain/services не знают об ORM, HTTP schemas или BMSTU parser. `ProgramFingerprint` и `UserProfile` остаются application contracts, а API routes только связывают их с HTTP.

BMSTU URL, selectors, PDF parser, mappings и browser fallback находятся в BMSTU adapter. Добавление нового вуза должно создавать новый adapter без зависимости comparison от структуры сайта.

## Identity дисциплин

Исходное `source_name` сохраняется на каждой позиции. Canonical normalization ограничивается Unicode, casefold и пробелами. Fuzzy-сопоставление и автоматическое объединение неоднозначных названий не используются.

## Таксономия дисциплин Andromeda

Каждая дисциплина получает не единственный ярлык, а нормализованный вектор `area_weights`: веса по 22 верхнеуровневым областям Andromeda. Веса строго положительны, не дублируют область и в сумме дают `1.0000`. Поэтому междисциплинарные предметы не теряют вторичную область: например, машинное обучение хранится как компьютерные науки + математика.

Для BMSTU явные сопоставления находятся в `ingestion/universities/bmstu/mappings/discipline_areas.py`. Это часть university-specific ingestion adapter, а не core comparison. На входе сохраняется исходное название, затем adapter применяет точное сопоставление по нормализованному имени; прозрачные keyword rules и универсальная область являются только fallback для новых или неизвестных предметов.

Распределение содержания программы считается в `comparison` по часам позиций учебного плана (при отсутствии часов используется ЗЕТ). Вектор предмета умножается на долю его нагрузки, после чего веса агрегируются по программе и выбранному семестру. Один предмет может влиять на несколько профилей, но исходная дисциплина и её workload остаются отдельной строкой сравнения.

## See Also

- [API](api.md) — HTTP-контракты для frontend.
- [Конфигурация](configuration.md) — database и logging settings.
- [Тестирование](testing.md) — архитектурные и интеграционные gates.
