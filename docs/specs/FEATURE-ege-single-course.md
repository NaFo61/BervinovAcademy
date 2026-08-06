# FEATURE: Единый курс «ЕГЭ-информатика» + брендинг платформы

Status: **APPROVED**

## Acceptance criteria

- [x] Активных курсов в API `GET /api/content/courses/` — **ровно 1**, title «ЕГЭ-информатика» (slug `ege-informatika`).
- [x] У курса ровно **4** активных модуля с названиями:
  - `1-й урок ЕГЭ: Графы`
  - `2-й урок ЕГЭ: Кодирование и поиск`
  - `3-й урок ЕГЭ: Электронные таблицы`
  - `Контрольная`
- [x] В каждом из модулей 1–3: ≥1 теория, ≥2 radio, ≥2 checkbox, ≥3 coding, ≥3 short-answer; у теории и у каждого задания заданы video (`video_url` и/или `video_file`) — в seed допустимы **placeholder URL**.
- [x] В модуле «Контрольная»: ≥2 radio, ≥2 checkbox, ≥2 coding, ≥2 short-answer; **без** обязательной новой теории; у каждого задания — video (placeholder OK) + Pro-гейт разбора.
- [x] Видео теории **не** отдаётся free-пользователю (`video_requires_pro` / null payload + флаг).
- [x] Видео разборов radio / checkbox / coding / short-answer — через существующий Pro-гейт `solution_video` (текст эталона по текущим правилам unlock).
- [x] Новый тип «краткий ответ»: create/read в content API + submit в progress API + учёт в прогрессе курса; сравнение с нормализацией **trim + collapse whitespace + case-insensitive**.
- [x] Mentoring **editor UI** для short-answer входит в **ту же** реализацию (тот же PR/scope), что seed и API.
- [x] Seed / data-команда поднимает эту структуру; курс «Python с нуля» и прочие демо-курсы **не** создаются.
- [x] Старые Enrollment на Python / прежний ЕГЭ: **не важны** — простейший путь (orphan / delete / ignore при деактивации старых курсов), без миграции прогресса.
- [x] Frontend: landing / auth tagline / catalog categories / document title отражают ЕГЭ; demo-карточки Python Junior убраны или заменены.
- [x] Pytest: seed-инварианты структуры (4 модуля, counts); Pro-гейт теории; short-answer correct/incorrect + нормализация; radio+checkbox в seed; list courses count=1 после seed.

## Goal / user value

Платформа Bervinov Academy становится **школой подготовки к ЕГЭ по информатике**, а не каталогом нескольких IT-курсов.

1. В каталоге и в БД — **ровно один** активный курс: **«ЕГЭ-информатика»** (не «Python с нуля»).
2. Курс состоит из **четырёх модулей** (`content.Module`): три урока ЕГЭ + одна контрольная.
3. В каждом учебном модуле (1–3) — фиксированный набор материалов: теория + radio + checkbox + задачи + краткий ответ; у теории и у каждого задания — видео.
4. **Все видео** (теория и разборы заданий) доступны только при **Pro** (`solution_video` / активный entitlement Pro).
5. UI/копирайт (landing, auth, каталог, title) ориентированы на ЕГЭ, а не на «Python Junior».

## Как устроено сейчас (as-is)

| Сущность | Модель / место | Замечание |
|----------|----------------|-----------|
| Курс | `content.Course` | В seed сейчас **два** курса: `ЕГЭ по информатике` + `Python с нуля` (`fixture/course_fixtures.py` → `COURSE_FIXTURES`) |
| Блок | `content.Module` | Порядок `order_index` внутри курса |
| Теория | `LessonTheory` | Поля `video_url` / `video_file`; в API отдаётся как `video` **без Pro-гейта** |
| Вопрос (1 ответ) | `LessonRadioQuestion` | Видео разбора → `reference_solution` + Pro |
| Вопрос (несколько) | `LessonCheckBoxQuestion` | То же |
| Задача (код) | `CodingChallenge` + `TestCase` | То же |
| Краткий ответ | **нет модели** | Нужен новый тип урока |
| Запись на курс | `education.Enrollment` | FK на `Course`; при смене курсов старые записи не важны |
| Pro-видео | `subscriptions` + `content.solution_access.build_reference_solution` | Фича `solution_video`: текст эталона — всем (после unlock), видео — только Pro |
| Seed | `manage.py seed_data` | Создаёт оба курса; `--clear` чистит контент |
| Frontend-демо | `shared.jsx` `DEMO_COURSES` / `CATEGORIES`, `landing.jsx`, `auth.jsx` | Остаётся брендинг «Python / кодить» |

## Target structure (to-be)

### Курс

- **Title:** `ЕГЭ-информатика`
- **Slug:** `ege-informatika` (стабильный)
- **Technologies:** `ЕГЭ`, `Информатика` (без акцента на «Python Junior» в каталоге; Python как инструмент экзамена допустим в описании)
- **is_active:** `true`
- Другие курсы: **неактивны** или удалены простейшим способом (см. Decisions)

### Четыре модуля (= `Module`)

Терминология: это **уроки / модули курса**, **не** школьные классы (5–11).

Названия привязаны к типовой нумерации заданий ЕГЭ по информатике (кодинг/ФИПИ-ориентированные формулировки с Решу ЕГЭ / типовых разборов 2024–2026):

| # | Название модуля (seed / UI) | Тема (intent) | Соответствие типовым номерам ЕГЭ |
|---|-----------------------------|---------------|----------------------------------|
| 1 | **1-й урок ЕГЭ: Графы** | графы | **№1** — анализ информационных моделей, соотнесение таблицы и графа |
| 2 | **2-й урок ЕГЭ: Кодирование и поиск** | код / поиск | **№4** — кодирование и декодирование информации (условие Фано); **№10** — поиск в текстовом редакторе |
| 3 | **3-й урок ЕГЭ: Электронные таблицы** | таблицы / Excel | **№9** — работа с электронными таблицами (Excel); смежно **№3** — поиск в связанных таблицах/БД (в теории модуля можно кратко упомянуть) |
| 4 | **Контрольная** | КР после уроков 1–3 | Смешанная проверка тем модулей 1–3 (не новый «номер ЕГЭ») |

Краткое обоснование названий (research):

- №1 стабильно про граф ↔ таблица дорог / матрица смежности.
- «Код» в ЕГЭ-сленге учеников = **кодирование** (№4), не «написать программу»; «поиск» = **поиск в тексте** (№10). Вместе — один учебный модуль.
- «Таблицы / Excel» = **электронные таблицы** (№9); это основной якорь названия модуля 3.

### Инвентарь модулей 1–3 (учебные уроки)

Порядок в модуле (рекомендуемый `order_index`):

1. **1× теория** (`LessonTheory`) — текст + видео (Pro)
2. **≥2× radio** (`LessonRadioQuestion`) — один правильный вариант + видео-разбор (Pro)
3. **≥2× checkbox** (`LessonCheckBoxQuestion`) — несколько правильных + видео-разбор (Pro)
4. **≥3× задачи** (`CodingChallenge`) — код + тесты + видео-разбор (Pro)
5. **≥3× с кратким ответом** (`LessonShortAnswer` — **новый тип**) — ввод строки/числа + эталон + видео-разбор (Pro)

Рекомендуемые counts в seed (на каждый из модулей 1–3): **1 theory + 2 radio + 2 checkbox + 3 coding + 3 short-answer = 11** уроков.

**Оба** типа вопросов обязательны: radio **и** checkbox используются в seed и в UI (не «выбрать один»).

Маппинг терминов:

| Пользователь | Тип в системе |
|--------------|---------------|
| теория | `LessonTheory` |
| вопросы (один верный) | `LessonRadioQuestion` |
| вопросы (несколько верных) | `LessonCheckBoxQuestion` |
| задачи | `CodingChallenge` |
| с кратким ответом | **новый** `LessonShortAnswer` |

### Инвентарь модуля 4 — Контрольная

Модуль идёт **после** уроков 1–3. Цель — проверка усвоения, без нового большого теоретического блока.

Рекомендуемый состав seed (итого **8** уроков):

| # | Тип | Кол-во | Содержание (заглушки) |
|---|-----|--------|------------------------|
| — | теория | **0** | Новой теории нет (КР = практика) |
| 1–2 | radio | 2 | По 1 вопросу на темы модулей 1 и 2 (графы; кодирование/поиск) |
| 3–4 | checkbox | 2 | Смешанно: графы/кодирование и таблицы |
| 5–6 | coding | 2 | Простые задачи на темы модулей 1–3 |
| 7–8 | short-answer | 2 | Числовой/строковый ответ в стиле ЕГЭ (№1/№4/№9) |

У **каждого** задания КР — placeholder `video_url` разбора + Pro-гейт, как в модулях 1–3.

Итого на курс: **3×11 + 8 = 41** урок (seed-ориентир; acceptance — через минимумы ниже).

Тексты уроков в seed — учебные заглушки по темам модуля; **не** полный банк ФИПИ.

## User stories

1. Как ученик, в каталоге я вижу **только** курс «ЕГЭ-информатика» и понимаю, что платформа про ЕГЭ.
2. Как ученик, открыв курс, вижу **четыре модуля**: 1–3 урок ЕГЭ (графы / кодирование и поиск / электронные таблицы) и **Контрольную**.
3. Как ученик без Pro, я читаю теорию и решаю задания, но **не смотрю видео** — вижу CTA «доступно в Pro».
4. Как ученик с Pro, я смотрю видео теории и видео-разборы всех заданий (включая КР).
5. Как ученик, я сдаю radio, checkbox, coding и краткий ответ; для краткого ответа сравнение **без учёта регистра и лишних пробелов**.
6. Как ментор/админ, я могу править short-answer в editor API / UI в той же итерации, что и seed.

## API contract

### Без ломающих изменений (reuse)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/content/courses/` | После изменений — 1 курс |
| GET | `/api/content/courses/{public_id}/` | Модули + уроки (расширить short-answer; checkbox уже есть) |
| GET | `/api/content/...` detail theory/radio/checkbox/coding | Как сейчас + Pro на theory video |
| POST | `/api/progress/radio/` | без изменений |
| POST | `/api/progress/checkbox/` | без изменений (убедиться, что используется) |
| POST | `/api/progress/code/` | без изменений |
| GET | `/api/subscriptions/me/` | `features` включает `solution_video` |
| POST | `/api/education/enrollments/` | `{ "course": "<uuid>" }` — тот же единственный курс |

### Новое / изменение

#### Theory video Pro-гейт

Сейчас `LessonTheorySerializer.video` отдаёт полный payload всем.

**To-be** (зеркало `reference_solution`):

```json
{
  "video": null,
  "has_video": true,
  "video_requires_pro": true
}
```

или при доступе:

```json
{
  "video": { "url": "...", "embed_url": "..." },
  "has_video": true,
  "video_requires_pro": false
}
```

- Free / anon: `video=null`, `has_video=true`, `video_requires_pro=true` если файл/URL есть.
- Pro / mentor / admin: полный `video`, `video_requires_pro=false`.
- Текстовый `content` теории остаётся доступен без Pro.

#### Short answer — content

| Method | Path | Auth | Body / response |
|--------|------|------|-----------------|
| (через course/module detail) | в списке уроков модуля | JWT / как сейчас | `kind: "short_answer"`, `public_id`, `title`, `order_index` |
| GET | `/api/content/short-answers/{public_id}/` | как у radio | поля ниже; **не** отдавать `correct_answer` ученику |

Поля модели:

| Field | Type | Notes |
|-------|------|-------|
| `title` | str | |
| `question_text` | text | условие |
| `correct_answer` | str | эталон (сервер only) |
| `answer_normalize` | choice | по умолчанию `strip_casefold` (см. ниже); опционально `exact` / `numeric` для будущего |
| `comment`, `explanation`, `solution_text` | text | как у radio |
| `video_url`, `video_file` | url/file | разбор |
| `points`, `order_index`, `is_active` | | |
| parent | module **или** exam **или** course | как у других уроков |

**Нормализация (обязательная для seed и default):**

- применить к эталону и к ответу пользователя одинаково:
  - `strip()` по краям;
  - схлопнуть внутренние пробелы (`\s+` → один пробел);
  - сравнение **case-insensitive** (`casefold()`).
- Отдельная числовая нормализация (`01` == `1`) **не обязательна** в этой итерации (режим `numeric` можно заложить в enum, но default — `strip_casefold`).

`reference_solution` — тот же билдер, что у radio/coding/checkbox (текст + Pro-видео после unlock).

#### Short answer — progress

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/api/progress/short-answer/` | `{ "question": "<uuid>", "answer": "42" }` | `{ "is_correct", "public_id", ... }` |
| GET | `/api/progress/short-answer/` | list своих попыток/последних | |

Ошибки: 400 валидация; 401 без JWT; 404 чужой/неактивный вопрос.

Unlock эталона: как radio — после верного ответа или ≥3 неверных (`SOLUTION_FAIL_THRESHOLD`).

#### Mentoring editor (**в scope этой итерации**)

- CRUD short-answer в существующем content-editor API **и** форма в `content-editor.jsx` (поля: title, question_text, correct_answer, normalize, solution/video) — **обязательно в том же PR**, что backend seed/API.
- Radio и checkbox в editor уже есть — убедиться, что seed и learn UI оба типа показывают.

## DB / migrations

1. **Новая модель** `LessonShortAnswer` (+ `answer_normalize`) в `content`.
2. **Новая модель** `UserAnswerShort` (или аналог) в `progress`: user, question FK, answer text, is_correct, timestamps / failed_attempts.
3. Индексы / `order_index` / parent validation — через существующий `content.lesson_parent` (расширить).
4. **Данные:**
   - Обновить `backend/fixture/course_fixtures.py`: один курс, **4** модуля, инвентарь выше, placeholder `video_url` (любой стабильный dummy YouTube/Rutube — достаточно одного на все).
   - Убрать `PYTHON_FROM_ZERO` из `COURSE_FIXTURES`.
   - Management: `seed_data` создаёт только ЕГЭ-курс; опционально `ensure_ege_course` для prod без `--clear`.
5. **Prod / существующие записи:**
   - Деактивировать (`is_active=False`) все курсы кроме целевого **или** удалить демо-курсы — на усмотрение реализации, простейший путь.
   - Enrollment / прогресс на старый Python: **игнорировать** (не мигрировать, не auto-enroll). Допустимо orphan при деактивации или удаление записей enrollment на неактивные курсы — без сохранения истории.
   - Не запускать `full-restart.sh` без явного OK владельца.

Миграции схемы обязательны; data-migration минимальна (деактивация старых курсов / upsert ЕГЭ).

## UI

| Экран | Изменение |
|-------|-----------|
| `index.html` title | ЕГЭ / Академия (например «Bervinov Academy · ЕГЭ-информатика») |
| `landing.jsx` | Hero/подзаголовок про подготовку к ЕГЭ по информатике; «топ курсов» → один курс или блок «Начать подготовку» |
| `auth.jsx` | Tagline вместо «Python с нуля до Junior» |
| `catalog.jsx` + `shared.jsx` | Категории под ЕГЭ; убрать DEMO Python Junior |
| `course.jsx` / `learn.jsx` | 4 модуля; short-answer UI; radio **и** checkbox; Pro-lock на video теории |
| `content-editor.jsx` | Форма short-answer + video_url (**в scope**) |
| Nav / profile | Единый копирайт ЕГЭ |

Состояния видео:

- нет видео → блок скрыт;
- есть, нет Pro → заглушка + ссылка на `#/pro`;
- Pro → `VideoExplanation`.

## Test plan

1. **Fixture/structure:** 1 course, 4 modules, counts для модулей 1–3 и КР.
2. **Theory Pro video:** free → `video` null + `video_requires_pro`; после `grant_pro` → video payload.
3. **Short answer API:** correct / incorrect; нормализация `Ab C` == `ab  c`; эталон не в GET detail; unlock после 3 fail.
4. **Checkbox + radio:** оба присутствуют в seed; submit работает.
5. **Progress stats / enrollment sync:** short-answer учитывается в «пройдено».
6. **Catalog:** list length 1; title/slug.
7. **Editor:** create/update short-answer через editor API (и smoke UI при наличии e2e).
8. **Regression:** radio/coding/checkbox Pro video как в `test_entitlements.py`.
9. Ручной smoke: `#/catalog` → курс → модуль 1 → теория (lock) → radio → checkbox → задача → краткий ответ → модуль 4 КР.

## Deploy impact

- Миграции `content`, `progress`.
- Пересборка backend image (CI) + `restart.sh` (не `full-restart`).
- Наполнение контента: `seed_data` только на чистых стендах; на prod — data-команда / editor.
- Env: **none** новых секретов.
- Видео: **placeholder URL** в seed; реальные URL — контент-операция позже.

## Out of scope

- Полная перепись всех 27 номеров ЕГЭ и авторский контент «как в ФИПИ».
- Жёсткий запрет создавать второй курс в admin/editor (публичный каталог фильтрует `is_active`).
- Новые тарифы / изменение цены Pro.
- Удаление Python playground / Monaco — только убрать позиционирование «курс Python Junior».
- VK/OAuth, whiteboard, conference — без изменений.
- Числовая нормализация short-answer (`01` == `1`) — опциональный режим, не обязателен в acceptance.
- Миграция/сохранение старых Enrollment и прогресса Python-курса.

## Decisions (закрыто владельцем)

1. **Не «класс»** — модули называются **уроками ЕГЭ** (1-й / 2-й / 3-й урок), не школьные классы.
2. **Видео** — placeholder URL в seed достаточны.
3. **Названия модулей** — финальные (см. таблицу выше): Графы; Кодирование и поиск; Электронные таблицы; Контрольная.
4. **Старые Python enrollments** — ignore / delete / orphan, простейший путь.
5. **Вопросы** — в seed и продукте используются **и radio, и checkbox**.
6. **КР** — **да**, 4-й модуль «Контрольная» после трёх уроков; состав — см. инвентарь модуля 4.
7. **Нормализация short-answer** — trim + collapse spaces + case-insensitive.
8. **Editor short-answer** — **да**, в той же реализации / PR.
9. «Блок» / «урок» = `content.Module`; курс slug `ege-informatika`.
10. Все видео (теория + разборы) → Pro feature `solution_video`.
11. Старый Python-курс: не создавать в seed; на prod — `is_active=False` или удаление демо — на выбор реализации.

## Open questions (остаток)

1. Сила ребрендинга в `<title>` / хедере: оставить **«Bervinov Academy»** + подзаголовок ЕГЭ (рекомендуемый default) или сильнее переименовать продукт?  
   → Если нет ответа до `APPROVED`, реализация берёт default: `Bervinov Academy · ЕГЭ-информатика`.

Остальные прежние open questions **закрыты** решениями выше.

---

**Следующий шаг:** пользователь при необходимости правит ТЗ и пишет в чат:

`APPROVED: docs/specs/FEATURE-ege-single-course.md`

После этого — Phase 2 (backend-agent) → frontend → docs → deploy по необходимости.
