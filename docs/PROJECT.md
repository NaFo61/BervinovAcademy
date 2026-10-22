# Bervinov Academy — полное описание проекта

Один справочник по платформе: как устроена, какие внешние сервисы, как работает доска и конспект, схема БД, примеры API.

---

## 1. Что это

Платформа для подготовки к ЕГЭ по информатике:

- курсы → модули → уроки (теория, тесты, код);
- ментор и ученик в чате и в видеозвонке;
- у ученика **одна постоянная доска** (как Miro) — на уроке рисуют на ней;
- кнопка **«Конспект»** делает короткий текст урока из аудио (STT + LLM);
- код ученика проверяется в Docker-песочнице через Kafka.

Прод: `https://academy.bervinov-miron.ru`  
Сервер: `/opt/bervinov-academy` (только образы, без git-сборки на хосте).

---

## 2. Стек

| Слой | Технологии |
|------|------------|
| Backend | Python 3.11, Django 4.2, DRF, Simple JWT, Celery, Channels |
| БД / кэш | PostgreSQL 15, Redis |
| Очереди | Apache Kafka (заявки на проверку кода и результаты) |
| Frontend | React 18 (CDN + Babel), hash-router `#/…`, Tailwind CDN |
| Видео | LiveKit Cloud |
| Доска | tldraw + `services/tldraw-sync` |
| Песочница | `code-check-runner` → Docker-образ `code-check-sandbox` |
| Файлы | локальный `MEDIA` или Selectel S3 |
| Почта | SMTP (Selectel mail) или console |
| LLM / STT | OpenAI-compatible API (часто ProxyAPI) |

Структура репо:

```
backend/          # Django apps
frontend/         # SPA src + whiteboard bundle
services/         # tldraw-sync, code_check_emulator, code_check_sandbox
deploy/           # prod compose, nginx, restart.sh
docs/PROJECT.md   # этот файл
```

---

## 3. Внешние сервисы и токены

Где брать ключи и куда писать в `.env`:

| Сервис | Зачем | Где получить | Переменные |
|--------|--------|--------------|------------|
| **LiveKit Cloud** | Видеозвонки | https://cloud.livekit.io → Project → Settings → Keys | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` |
| **Яндекс OAuth** | Вход через Яндекс | https://oauth.yandex.ru/ | `YANDEX_OAUTH_CLIENT_ID`, `YANDEX_OAUTH_CLIENT_SECRET` |
| **VK OAuth** | Вход через VK | https://id.vk.com / VK app | `VK_OAUTH_CLIENT_ID`, `VK_OAUTH_CLIENT_SECRET` |
| **Telegram Bot** | Бот / webhook | https://t.me/BotFather | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `TELEGRAM_WEBHOOK_SECRET` |
| **OpenAI / ProxyAPI** | ИИ-помощник + Whisper + конспект | https://proxyapi.ru/docs/overview или OpenAI | `ASSISTANT_LLM_ENABLED`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_STT_MODEL` |
| **Selectel S3** | Видео и медиа | Selectel → Object Storage | `USE_S3`, `AWS_*` |
| **Selectel SMTP** | Письма | Selectel mail | `EMAIL_HOST`, `EMAIL_HOST_USER`, … |

OAuth redirect (локально): `http://localhost:3000/auth-callback`  
Telegram webhook: `https://academy.bervinov-miron.ru/api/telegram/webhook/$TELEGRAM_WEBHOOK_SECRET/`

Шаблон всех переменных: [`.env.example`](../.env.example). Секреты в git не коммитить.

Доска (tldraw sync):

- `WHITEBOARD_ENABLED`, `WHITEBOARD_SYNC_SECRET`, `TLDRAW_LICENSE_KEY` (опционально).

JWT:

- короткий access + длинный refresh (`JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`).

---

## 4. Как работает (основные потоки)

### 4.1. Авторизация

1. Email/пароль или OAuth (Яндекс/VK) → JWT access + refresh в `localStorage`.
2. Все `/api/…` с `Authorization: Bearer …`.
3. Публичные id в API — UUID `public_id`, не внутренний PK.

### 4.2. Урок и код

1. Ученик решает coding-задачу → `POST /api/progress/code/`.
2. Django кладёт заявку в Kafka (`code-submissions`).
3. `code-check-runner` поднимает контейнер песочницы (без сети, лимиты CPU/RAM/pids, nofile).
4. Результат в Kafka → consumer обновляет `CodeSubmission`.

Лимиты песочницы (жёсткие потолки): time ≤ 10 с, memory ≤ 512 МБ, stdout+stderr ≤ 256 КБ, ≤ 32 файла в `/work`, файл ≤ 1 МБ.

### 4.3. Созвон + доска ученика

1. Ментор создаёт `Conference` (guest = ученик).
2. Join → LiveKit token; **камера при входе выключена**, микрофон включается.
3. Доска: `POST …/whiteboard/token/` → `room_id = u-{guest.public_id}` — одна комната навсегда.
4. PNG-снимок: `POST …/whiteboard/export/` («Снимок доски»).
5. Крупные файлы: `POST /api/communication/board-assets/` → URL на доску; sync принимает только image ≤ 2 МБ.

### 4.4. AI-конспект урока

1. Браузер ментора пишет смешанное аудио (MediaRecorder).
2. `POST …/lesson-summary/` (multipart `audio`) → статус `pending`.
3. Celery: Whisper (`/audio/transcriptions`) → LLM chat → `summary_md`, статус `ready`.
4. `GET …/lesson-summary/` — текст для UI / чата.

Нужны `ASSISTANT_LLM_ENABLED=true` и рабочий `OPENAI_API_KEY`, плюс Celery worker.

---

## 5. Пример схемы БД (важное)

```
User (public_id, email, phone, role, yandex_id, vk_id, …)
  ├─ Student / Mentor профили
  └─ Enrollment → Course

Course → Module → LessonTheory | Radio | Checkbox | ShortAnswer | CodingChallenge
CodingChallenge → TestCase
               → CodeSubmission (progress)

Conference (mentor, guest, room_name, status, …)
  ├─ ConferenceWhiteboard (image PNG, snapshot_json)   # снимок
  └─ ConferenceLessonSummary (audio, transcript, summary_md, status)

BoardAsset (uploaded_by, file, original_name, size)    # файлы для доски

DirectThread (mentor ↔ student) → ChatMessage → attachments
```

Статусы конференции: `waiting` → `active` → `completed` | `declined` | `cancelled` | `expired`.  
Статусы конспекта: `pending` | `ready` | `failed`.

---

## 6. Примеры API

```http
POST /api/communication/conferences/
Authorization: Bearer <jwt>
{"guest": "<student-public-id>"}

POST /api/communication/conferences/<id>/join/

POST /api/communication/conferences/<id>/whiteboard/token/
→ {"token":"…","room_id":"u-<guest-uuid>","expires_in":3600}

POST /api/communication/conferences/<id>/lesson-summary/
Content-Type: multipart/form-data
audio: <blob>
→ 202 {"status":"pending",…}

GET /api/communication/conferences/<id>/lesson-summary/
→ {"status":"ready","summary_md":"- …",…}

POST /api/communication/board-assets/
file: <pdf|png|…>
→ {"url":"https://…","original_name":"…","size":1234}

POST /api/progress/code/
{"challenge":"<uuid>","code":"print(1)"}
```

Health: `GET /health/` → `{"status":"ok"}`.

---

## 7. Деплой

- CI (`.github/workflows/ci-cd.yml`): lint → pytest → build/push образов Docker Hub → SSH deploy.
- На сервере: `deploy/docker-compose.yml` + `.env` + `./restart.sh` (без wipe БД).
- `full-restart.sh` — только по явному ОК (трёт volumes).
- Host nginx → `127.0.0.1:18080`.

Локально: корневой `docker compose up -d --build`.

---

## 8. Тесты

```bash
# из корня репо
pytest backend -v --reuse-db

# песочница (без Django)
cd services/code_check_emulator && PYTHONPATH=. pytest tests/ -v
cd services/code_check_sandbox && pytest test_judge_limits.py -v
```

Ключевые наборы: `backend/communication/tests/` (звонки, доска, конспект, чат), `backend/progress/tests/`, `backend/content/tests/`, `backend/users/tests/`.

---

## 9. Полезные команды

```bash
docker compose ps
docker compose logs -f backend celery
python backend/manage.py migrate
python backend/manage.py seed_data   # если есть fixture
curl -sS https://academy.bervinov-miron.ru/health/
```
