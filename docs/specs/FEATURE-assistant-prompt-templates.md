# ИИ-помощник: общий + модуль + задание

**Статус:** APPROVED (слои промптов)

## Цель

Владелец/ментор настраивает промпт **в 3 уровнях** — ИИ понимает контекст:

1. **Общий** (вся школа) — тон, правила, базовый контекст  
2. **Модуль** — доп. правила для блока курса  
3. **Задание** — нюансы конкретной задачи  

Непустые уровни **склеиваются** через разделитель `---`.

Студент спрашивает в «Помощь → ИИ».

---

## Как настроить (для людей)

| Уровень | Где |
|--------|-----|
| Общий | Ментор → Редактор контента → «Общий промпт ИИ»; или Django Admin |
| Модуль | Дерево курса → модуль → «Промпт модуля» |
| Задание | Coding-урок → «Промпт ИИ для этого задания» |

Плейсхолдеры:

| | |
|--|--|
| `{{course}}` | курс |
| `{{module}}` | модуль |
| `{{title}}` | задача |
| `{{condition}}` | условие |
| `{{tests}}` | публичные тесты |
| `{{code}}` | код ученика |

---

## Для разработки

### Иерархия

```
base (AssistantSettings) + module.assistant_prompt? + challenge.assistant_prompt?
→ render placeholders
```

### API

- `GET/PATCH /api/mentoring/assistant/settings/` — `{ base_prompt }` (mentor/admin)
- `PATCH /api/mentoring/editor/modules/{id}/` — поле `assistant_prompt`
- coding lesson editor — поле `assistant_prompt` (как раньше)
- `POST /api/mentoring/assistant/chat/` — без изменений; контекст с `module_title`

### DB

- `mentoring.AssistantSettings.base_prompt`
- `content.Module.assistant_prompt`
- `content.CodingChallenge.assistant_prompt`

### Тесты

- `backend/mentoring/tests/test_assistant.py` — base / module / task compose
- editor API — `assistant_prompt` на coding

### Deploy

Обычный CI push → migrate → restart. Секреты LLM уже в `.env` (ProxyAPI).
