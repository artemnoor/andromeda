[← API](api.md) · [Back to README](../README.md) · [Конфигурация →](configuration.md)

# Admissions

Admissions — read-only vertical slice с source-backed условиями поступления по canonical `program_id`. Он не вычисляет `Admission Fit`, вероятность поступления или рейтинг программ.

## Data flow

```text
BMSTU detail/API source
  → raw admission DTO
  → BMSTU normalization + canonical program identity
  → admission_offerings + typed child tables
  → AdmissionReader → AdmissionService
  → GET /programs/{id}/admissions → program UI
```

`admissions` не импортирует ORM, SQLAlchemy или parser internals. Service получает программу через публичный `ProgramReader`, а данные поступления — через `AdmissionReader`. У каждой offering и каждого дочернего показателя хранится provenance: source kind, URL, capture timestamp, content hash и locator.

## Source inventory and gaps

| Поле | Доступный источник в текущем fixture | Поведение |
|---|---|---|
| год набора | BMSTU detail `additional`/current payload | сохраняется как offering year |
| форма обучения | BMSTU detail `price` | нормализуется в `StudyForm` |
| бюджет/платное | BMSTU detail `places` и `price` | отдельные offerings |
| бюджетные и платные места | BMSTU detail `places` | `places` nullable, без догадок |
| ЕГЭ и минимумы | BMSTU detail `points` | отдельные typed exam requirements |
| стоимость | BMSTU detail `price` | отдельные regular/discounted tuition rows |
| исторические проходные | BMSTU detail `additional.oldPoints` | отдельные historical offerings |
| квоты | текущий fixture detail не публикует квоты | пустая коллекция; `0` не подставляется |
| официальный PDF плана приёма | не включён в текущий captured fixture | optional future source gap, не fabricated |

Если новый source добавляет квоты или уточняет размерность конкурса, это должно пройти через новый raw parser/normalizer и тот же canonical contract. Неподтверждённая или неоднозначная identity не записывается как связанная программа.

## API contract

```text
GET /programs/program:09.03.01-02/admissions
```

Ответ содержит:

- `program` и `programId`;
- `offerings[]` по году, `scope`, форме и типу финансирования;
- `places`, `exams`, `quotas`, `passingScores`, `tuition`;
- `provenance` с официальным source URL.

Для программы без admission-источника API возвращает `200` с `offerings: []`. Для неизвестного canonical ID возвращается strict `404 NOT_FOUND`. Decimal-поля приходят строками OpenAPI-контракта, например `"529000.00"` и `"46.00"`.

## Migration and ingestion

Fixture SQLite smoke:

```powershell
python backend/scripts/run_tracer_demo.py --mode fixture --check
```

Development PostgreSQL:

```powershell
$env:ANDROMEDA_ENV = "development"
$env:BMSTU_DATABASE_URL = "postgresql+psycopg://andromeda:change-me@127.0.0.1:5432/andromeda_dev"
python -m alembic upgrade head
python backend/scripts/run_tracer_bullet.py --mode live --database-url $env:BMSTU_DATABASE_URL
```

Runner applies Alembic before ingestion and synchronizes admissions atomically with programs and curricula. A repeated source snapshot is idempotent; stale rows for the affected program are reconciled inside the same transaction. PostgreSQL и SQLite используют один repository port и одинаковые public contracts.

## Manual browser check

1. Запустите `python backend/scripts/run_tracer_demo.py --mode fixture`.
2. Откройте `http://127.0.0.1:5173/` и выберите «Программа».
3. Проверьте карточки 2026 budget/paid, `318`/`230` мест, ЕГЭ minimum `46`, стоимость `529000 ₽` и исторические проходные баллы.
4. Переключите вторую программу в select и убедитесь, что hash, карточка и данные обновились.
5. Уменьшите viewport до ~390 px: select, карточки, ссылки источников и текст не должны выходить за экран или накладываться.

## See Also

- [API](api.md) — strict HTTP schemas и endpoints.
- [Архитектура](architecture.md) — границы modular monolith.
- [PostgreSQL](postgresql.md) — dev/staging migration flow.
