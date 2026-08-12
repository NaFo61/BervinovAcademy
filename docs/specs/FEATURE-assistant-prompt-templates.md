# ИИ-помощник: общий → курс → модуль → урок

**Статус:** APPROVED (4 слоя)

## Цель

Промпт настраивается в 4 уровнях. Непустые слои **склеиваются**.

1. **Общий** — вся школа  
2. **Курс** — все уроки курса  
3. **Модуль** — уроки модуля  
4. **Урок** — любой тип: теория, radio, checkbox, краткий ответ, код  

В любом слое можно вставить `{{condition}}` / `{{instructions}}`, чтобы модель видела текст задания и могла его выполнять.

---

## Плейсхолдеры

| | |
|--|--|
| `{{condition}}` | условие / текст урока (теория, вопрос, описание+инструкции кода) |
| `{{instructions}}` | инструкции coding-задачи (иначе пусто) |
| `{{tests}}` | публичные тесты |
| `{{title}}` | название урока |
| `{{course}}` | курс |
| `{{module}}` | модуль |
| `{{kind}}` | theory / radio / checkbox / short_answer / coding |
| `{{code}}` | код ученика |

Пример в промпте модуля:

```text
Условие текущего задания:
{{condition}}

Инструкции:
{{instructions}}

Выполни задание сам и кратко объясни решение ученику.
```

---

## Где править в UI

- Общий — блок «Общий промпт ИИ»
- Курс — блок «Промпт ИИ курса»
- Модуль — кнопка у модуля в дереве
- Урок — поле в карточке любого урока

---

## API / DB

- `GET/PATCH /api/mentoring/assistant/settings/`
- `PATCH /api/mentoring/editor/courses/{id}/` → `assistant_prompt`
- `PATCH /api/mentoring/editor/modules/{id}/` → `assistant_prompt`
- lesson editor serializers — `assistant_prompt` на всех kinds

Поля: `AssistantSettings.base_prompt`, `Course.assistant_prompt`, `Module.assistant_prompt`, `*.assistant_prompt` на всех lesson-моделях.
