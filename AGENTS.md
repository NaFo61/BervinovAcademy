# Agents — Bervinov Academy

Краткий роутер для Cursor. Детали — в `.cursor/rules/` и `.cursor/skills/`.

## Специалисты

| Команда / запрос | Skill | Делает |
|------------------|-------|--------|
| backend, API, Django, pytest | `backend-agent` | `backend/`, code-check services |
| frontend, UI, React, страница | `frontend-agent` | `frontend/` |
| deploy, Docker, CI, nginx | `deploy-agent` | `deploy/`, compose, workflows |
| фича целиком, ТЗ → код | `feature-pipeline` | ТЗ → APPROVED → backend → frontend → docs → deploy |

## Как вызывать

В Agent chat:

```
Используй backend-agent: добавь endpoint ...
```

```
Используй feature-pipeline: ...
```

Или просто опиши задачу — core rule направит к нужному skill.

## Порядок для новой фичи

1. `feature-pipeline` → ТЗ в `docs/specs/`
2. Ты правишь и пишешь `APPROVED`
3. Backend → frontend → (deploy если нужно)

Не запускай `deploy/full-restart.sh` без явного подтверждения.
