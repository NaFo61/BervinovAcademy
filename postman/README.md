# Postman / Newman — проверки API

Зачем: руками и в CI ловить поломки **безопасности и контракта API** (JWT, 401/403, webhooks, health).

## В Postman

1. Import:
   - `BervinovAcademy.postman_collection.json`
   - `local.postman_environment.json` (или `prod`)
2. В environment укажи `login` / `password` тестового пользователя.
3. Collection Runner → Run (порядок папок важен: Auth → … → Logout).

## Newman (CLI)

```bash
# установка один раз
npm i -g newman

# local (нужен поднятый docker compose)
newman run postman/BervinovAcademy.postman_collection.json \
  -e postman/local.postman_environment.json \
  --delay-request 100
```

Prod — только со **своим** тестовым аккаунтом (пароль не коммить):

```bash
newman run postman/BervinovAcademy.postman_collection.json \
  -e postman/prod.postman_environment.json \
  --env-var "login=YOUR_TEST_USER" \
  --env-var "password=YOUR_TEST_PASSWORD"
```

## Что покрыто

| Папка | Проверки |
|-------|----------|
| Health | публичный `{"status":"ok"}`, без утечек |
| Auth | anti-enumeration, JWT `public_id`, me 401, reset generic |
| Content | нет доступа по integer PK |
| Notify | vapid 401 / no private key, VK/LiveKit webhook reject |
| Subscriptions | me требует JWT |
| Logout | refresh после logout → 401 |

Автотесты Django (pytest) — основной щит; Postman — живой smoke по HTTP.
