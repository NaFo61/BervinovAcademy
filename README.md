# Bervinov Academy

Образовательная платформа: курсы ЕГЭ, автопроверка Python, созвоны с ментором, общая доска ученика, AI-конспект урока.

**Прод:** https://academy.bervinov-miron.ru

## Стек (коротко)

Django + DRF + JWT · React SPA · PostgreSQL · Redis · Celery · Kafka · LiveKit · tldraw · Docker

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d --build
# сайт: http://localhost
# API:  http://localhost/api/
```

Тесты:

```bash
pytest backend -v --reuse-db
```

## Документация

Всё подробное — в одном файле: **[docs/PROJECT.md](docs/PROJECT.md)**  
(стек, токены/OAuth, доска, конспект, БД, деплой, примеры API).

Для Cursor-агентов: [AGENTS.md](AGENTS.md).
