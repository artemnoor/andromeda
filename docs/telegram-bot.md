[← Конфигурация](configuration.md) · [Back to README](../README.md) · [PostgreSQL →](postgresql.md)

# Telegram-клиент Andromeda

Telegram-клиент находится в отдельном пакете `telegram-bot/` и является
тонким transport/render-клиентом существующего Andromeda backend. Он не
читает PostgreSQL, не импортирует backend-модули и не содержит второго
recommendation или Admission Fit engine.

## Граница системы

```text
Telegram update
  → aiogram router
  → TelegramFlows
  → BackendHttpClient ── HTTP ──→ FastAPI canonical API
  → RendererClient ── signed HTTP ──→ frontend-next /og/*
  → PNG + inline keyboard
```

`BackendHttpClient` работает только с публичными HTTP-контрактами. Сессия
пользователя передаётся backend в cookie `andromeda_profile_session`; bot
хранит только зашифрованное opaque-значение в своей локальной SQLite-базе.
Canonical IDs, admissions, curricula, discipline area weights, Content Fit,
Admission Fit и provenance остаются owned backend-данными.

## Что бот вызывает

| Сценарий | Backend API | Render route | Результат |
|---|---|---|---|
| Каталог | `GET /programs` | `/og/catalog` | PNG-каталог и кнопки карточек |
| Карточка | `GET /programs/{id}` | `/og/program?ids=...` | PNG-карточка программы |
| Сравнение | `GET /compare/summary?programIds=...` | `/og/compare` | вертикальная матрица 2–3 программ |
| Мой shortlist | `GET /decision/suggestions` | `/og/shortlist` | основные и альтернативные варианты |
| Поступление | `GET /decision/suggestions`, `PUT /decision/constraints` | `/og/chances` | горизонтальные risk/chance bars |
| Профиль различий | `GET /compare/summary` | `/og/radar` | SVG-радар отдельных факторов |
| Учебный план | данные comparison/curriculum | `/og/curriculum` | stacked-бары по семестрам и часам |
| Дайджест | `GET /decision/suggestions` | `/og/digest` | состояние shortlist и source gaps |
| Уточнение | `GET /decision/context`, `POST /decision/refinement/answer` | — | короткий вопрос и подтверждение |

Изменения shortlist выполняются только явными backend-командами с
`expectedRevision`. Бот никогда не удаляет сохранённую программу из-за
пересчёта suggestions.

## Правило вывода

Короткий текст используется для вопросов, подтверждений, ошибок, source gaps
и уведомлений. Всё, где есть матрица, три и более структурных элемента или
числа для сопоставления, отправляется PNG:

- карточка программы: название, вуз, canonical code, risk/chance, budget и
  source-backed gaps;
- сравнение: summary-first вывод, key differences, trade-offs, admission
  context, content differences и ссылка на evidence;
- shortlist/chances/digest: компактные блоки, где категории и числа читаются
  без длинного текстового полотна;
- radar/curriculum: SVG-графика внутри Satori, без canvas.

PNG создаётся существующим Next `ImageResponse`/Satori render layer. Шрифт
`Noto Sans` с кириллицей лежит в `frontend-next/public/fonts/`. Светлая тема
используется по умолчанию; параметр `theme=dark` выбирает тёмную палитру.
Палитра и area colors переиспользуют frontend tokens, а не отдельную копию
дизайн-системы.

## Inline-кнопки и безопасность callback

Кнопки под изображением используют callback-токены вида `cb:<opaque-token>`.
В токен не кладутся program IDs, cookie, баллы и другие данные пользователя.
Payload хранится в памяти процесса, привязан к Telegram owner key и истекает
через ограниченное время. Просроченный или чужой callback отклоняется.

Для render routes бот подписывает `METHOD`, путь, нормализованную query string
и Unix timestamp HMAC-SHA256 заголовками:

```text
X-Andromeda-Render-Timestamp
X-Andromeda-Render-Signature
```

Next проверяет подпись и возраст запроса, затем передаёт cookie backend только
server-to-server. Cookie не попадает в URL, ключи не попадают в PNG и не
выводятся в логах. Кэш renderer изолирует записи по template, параметрам,
session scope и decision revision; устаревший shortlist не переиспользует
персонализированную картинку.

## Команды и естественный ввод

Доступны `/start`, `/catalog`, `/compare`, `/shortlist`, `/admission` и
`/digest`. Фразы `сравни ... и ...` и `сопоставь ...` проходят через live
`GET /programs`; коды и названия не зашиты в бота. Если resolver видит
несколько совпадений, пользователь получает короткий вопрос с кнопками.

`/admission` принимает только bounded формат `предмет=балл`, например
`математика=90, русский=85`. Введённые значения сохраняются как explicit
constraints и затем backend пересчитывает batch Admission Fit. Исторический
проходной балл не показывается как гарантия поступления.

Adaptive refinement остаётся необязательным. Ответ на вопрос изменяет только
derived suggestions/profile refinement; shortlist остаётся прежним.

## Analytics

Backend имеет allow-listed decision analytics с источником `telegram` и
ограниченным payload. В analytics не передаются raw answers, cookies,
admission scores или source bodies. Авторитетные mutation events генерирует
backend после успешной команды; transport-клиент может отправлять только
разрешённые view/interaction checkpoints. Analytics не влияет на ответ,
ranking или shortlist.

## Локальный запуск

```powershell
Copy-Item telegram-bot/.env.example telegram-bot/.env
# заполнить TELEGRAM_BOT_TOKEN и Fernet key
python -m pip install -e "telegram-bot[dev]"
$env:ANDROMEDA_BOT_BACKEND_URL = "http://127.0.0.1:8000"
$env:ANDROMEDA_BOT_RENDERER_URL = "http://127.0.0.1:3000"
python -m andromeda_telegram
```

Для автоматических проверок Telegram token не нужен: используются mocked
aiogram flows, HTTP adapters и fixture demo. PNG smoke проверяет подпись,
`Content-Type: image/png` и PNG magic bytes для всех `/og/*` routes.

## YC deployment

`deploy/yc/compose.yaml` запускает bot как один внутренний long-polling
service. Public port для него не открывается: bot ходит к `backend` и
`frontend` по внутренним именам compose-сети. В production нужно задать
`TELEGRAM_BOT_TOKEN`, `ANDROMEDA_SESSION_ENCRYPTION_KEY` и
`ANDROMEDA_RENDER_HMAC_SECRET` через secret manager/окружение; их нельзя
коммитить в `.env`, compose или CI.

Для экономичного single-instance режима Redis не требуется. При нескольких
bot replicas callback store нужно будет вынести в общий короткоживущий store;
это отдельное инфраструктурное решение и сейчас не добавляется.

## Источники и честные gaps

Бот не создаёт events, deadlines, проходные баллы или учебные планы из
fixtures в production flow. Если canonical backend возвращает `sourceGaps` или
`insufficient_data`, это явно показывается пользователю. Digest является
on-demand снимком текущего выбора; scheduled weekly delivery не включена,
пока нет подтверждённого live source и opt-in пользователя.

## See Also

- [Конфигурация](configuration.md) — environment variables and secrets.
- [API](api.md) — canonical backend endpoints and contracts.
- [PostgreSQL](postgresql.md) — deployment database and migrations.
