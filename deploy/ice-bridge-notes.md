# ICE bridge — что сделать на сервере

Общая касса: сайт академии читает/пишет Postgres **pivovarov-ice**.

## 1. Сеть Docker

Имя `postgres` занято у академии. Подключаем контейнер ICE с алиасом:

```bash
docker network connect --alias ice-postgres bervinov-academy_internal pivovarov-ice-postgres-1
```

Проверка из backend:

```bash
cd /opt/bervinov-academy
docker compose exec backend python -c "import socket; print(socket.gethostbyname('ice-postgres'))"
```

## 2. Env академии

В `/opt/bervinov-academy/.env` (пароль взять из ICE, не коммитить):

```
ICE_DATABASE_URL=postgresql://pivovarov:PASSWORD@ice-postgres:5432/pivovarov_ice
ICE_BOT_USERNAME=pivovarovicebot
```

Потом `./restart.sh` (без wipe) или recreate backend.

## 3. Инвайт Мирона

В ICE уже есть tutor id=3 «Мирон Бервинов» (status=invited). Старый инвайт мог протухнуть.

Перевыпуск (из контейнера ICE, под суперадмином Кирилла) — через API superadmin  
`POST /api/superadmin/tutors/3/invite`  
или скрипт в приложении ICE.

Мирон открывает ссылку вида `https://t.me/pivovarovicebot?start=inv_…` своим Telegram → кабинет становится active.

## 4. На сайте

1. Войти как `kuslytuna@yandex.ru`
2. Привязать тот же Telegram в профиле
3. Занятия → «Привязать кабинет» (или авто по tg_id)
4. Статистика: Неделя / Месяц / Год — цифры из ICE

Ученики Кирилла (tutor_id=1) не попадают в кабинет Мирона.
