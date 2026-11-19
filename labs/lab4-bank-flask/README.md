# Лабораторная №4 — Flask + SQLite

Каталог банковских продуктов (вариант 2) на Python и Flask вместо PHP/MySQL.

## Запуск

```bash
cd labs/lab4-bank-flask
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Открыть: http://127.0.0.1:5000/products

База `bank_catalog.db` создаётся сама из `schema.sql` при первом запуске.

## Проверка фильтров

| Запрос | Ожидание |
|--------|----------|
| `/products` | 6 продуктов |
| `?audience_id=4` | «Карта для бизнеса», 590 ₽ |
| `?name=карт&audience_id=1&description=кэшбэк&tariff_cost=0` | только «Альфа-Карта» |
| `?name=неттакого` | пустой список |
| `?clearFilter=1` | снова все 6 |

## Почему SQLite

Для учебной работы с одной машиной SQLite проще MySQL: один файл, без XAMPP/службы, те же JOIN и параметры `?`. MySQL имеет смысл, если нужен общий сервер для нескольких пользователей.
