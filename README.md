# Andromeda BMSTU

> Andromeda — data-driven система поддержки выбора образовательной программы.

Andromeda объединяет source-backed данные МГТУ им. Н.Э. Баумана о поступлении и содержании учебных планов и помогает превратить набор вариантов в небольшой объяснимый shortlist. Пользователь может начать с каталога, сравнения, проверки поступления, профиля предпочтений или уже сохранённого выбора — профтест и линейный маршрут не обязательны.

Система разделяет факты и решения: `DecisionContext` хранит только явно подтверждённые пользователем ограничения и shortlist, а предложения, Admission Fit, Content Fit, trade-offs и source gaps остаются derived evidence. Andromeda никогда не удаляет сохранённую программу автоматически; последнее решение принимает пользователь. Гостевая anonymous HttpOnly-сессия работает сразу, аккаунт нужен только для переноса выбора между устройствами.

## Быстрый старт

```powershell
python -m pip install -e "backend[dev]"
python backend/scripts/run_tracer_demo.py --mode fixture --check
```

После запуска API доступен на `http://127.0.0.1:8000/docs`, UI — на `http://127.0.0.1:3000/`. Для ручной работы уберите `--check`.

Для обычной dev-работы используйте PostgreSQL: инструкции находятся в [руководстве PostgreSQL](docs/postgresql.md). SQLite остаётся быстрым test fallback.

## Что уже работает

- BMSTU fixture/live ingestion с provenance и fail-closed source selection.
- Изолированные модули universities, programs, curricula, disciplines, decision, comparison, proftest, recommendations, admissions и admission_fit.
- SQLAlchemy/Alembic с FK, unique/check constraints и Decimal без float-конверсии.
- FastAPI/OpenAPI и сгенерированные TypeScript-типы.
- Persistent shortlist с ролями «основная/альтернатива», явными add/remove/restore и optimistic revision; raw A/B comparison и summary-first сравнение 2–3 программ.
- Профиль содержания: короткое ядро из пяти вопросов, preliminary topic chips, bounded adaptive refinement и TOP реальных программ с объяснениями по учебному плану. Новая session-сессия использует `proftest-v3`; старые pinned `proftest-v2` продолжают читаться.
- Persistence профиля: completed `UserProfile` хранится по anonymous HttpOnly session cookie и восстанавливается после перезагрузки UI.
- Recommendation vertical slice: готовый `UserProfile` → детерминированный Content Fit → reasons/anti-reasons по реальному fingerprint.
- Admissions vertical slice: реальные BMSTU данные поступления по canonical `program_id` — места, ЕГЭ и минимумы, квоты, проходные баллы, стоимость и форма обучения.

### Подбор и профиль содержания

Профиль предпочтений — один из способов уточнить `DecisionContext`, а не обязательный первый этап. В UI выберите «Подобрать». Compact adaptive v3 получает вопросы и результаты только через API: `GET /proftest/questions`, `POST /proftest/preview` и `POST /proftest/results`; session-вариант сохраняется через `/proftest/sessions/*`. Финальный результат сохраняется в Andromeda по anonymous HttpOnly cookie; после reload UI использует `GET /proftest/profile` и `GET /recommendations/current`. Профиль обновляет предложения, но не меняет shortlist без явного действия пользователя. После изменения API обновите frontend-контракт:

```powershell
python backend/scripts/export_openapi.py --out frontend-next/openapi.json
cd frontend-next
npm run generate-api
npm run check-api-drift
```

`Content Fit` рассчитывается детерминированно по реальным часам/ЗЕТ и долям предметных областей. В recommendation response `Workload readiness` и `Career Fit` пока имеют статус `not_available`; отдельный `Admission Fit` показывает риск по source-backed admissions facts и не влияет на Content Fit или ranking рекомендаций.

### Данные поступления

В UI выберите «Поступление» или откройте карточку программы. `DecisionContext` может сохранить явно введённые баллы и ограничения, после чего Decision Service оценивает batch кандидатов как realistic/borderline/unlikely/insufficient-data. Исторический проходной балл не является гарантией. Данные проходят тот же BMSTU parser → canonical contracts → PostgreSQL/SQLite repository → FastAPI flow; отсутствующие официальные значения не заменяются нулями.

### Мой выбор

`Мой выбор` — основной пользовательский экран. Он показывает основные варианты, альтернативы, ранее сохранённые варианты, известные ограничения и missing data. Система может предложить до трёх основных кандидатов и двух альтернатив с причинами, рисками, content differences и source gaps, но добавление, удаление, восстановление, исключение и смена роли выполняются отдельными командами пользователя. Все изменения защищены `expectedRevision`; устаревшая запись получает `409 CONFLICT`.

Сравнение сначала показывает краткий вывод и trade-offs, затем Admission/Content Fit и только потом дисциплины, часы, ЗЕТ и другие raw evidence. События, campus и `personal-route` оставлены как необязательная поддержка выбора; они не образуют следующий обязательный шаг.

## Пример

```text
GET /compare?programIds=<program-id-a>,<program-id-b>&scope=semester&semester=1
```

Ответ содержит rows со статусами `both`, `different`, `only_a`, `only_b`, а также totals и blocks.

## Документация

| Гид | Содержание |
|---|---|
| [Быстрый старт](docs/getting-started.md) | Установка и первый запуск |
| [Архитектура](docs/architecture.md) | Модули и поток данных |
| [API](docs/api.md) | OpenAPI endpoints и контракты |
| [Admissions](docs/admissions.md) | Данные поступления и source gaps |
| [Admission Fit](docs/admission-fit.md) | Отдельная оценка реалистичности поступления |
| [Принципы продукта](docs/product-principles.md) | Правила Decision Support и пользовательского выбора |
| [Конфигурация](docs/configuration.md) | Переменные окружения |
| [PostgreSQL](docs/postgresql.md) | Dev/staging, migrations и ingestion |
| [Тестирование](docs/testing.md) | Локальные и CI-проверки |

## Лицензия

Лицензия проекта не задана в текущем репозитории.
