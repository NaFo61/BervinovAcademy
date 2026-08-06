# FEATURE: VK chat bridge + OAuth (без Telegram)

Status: **IMPLEMENTED** (2026-08-06)

## Goal

Убрать Telegram. Авторизация: email+пароль, телефон+пароль, Яндекс OAuth, VK OAuth.
VK-сообщество: двусторонний мост менторского чата + уведомления (звонки, учёба, подписка).

## User stories

1. Как ученик, я вхожу через Яндекс или VK без пароля и получаю JWT.
2. Как ученик, я регистрируюсь/вхожу по email или телефону + пароль.
3. Как ученик с привязанным VK и разрешёнными сообщениями, я вижу сообщения ментора в VK и отвечаю там — ответ появляется на сайте.
4. Как ментор на сайте, я вижу ответы ученика из VK в том же треде.
5. Как пользователь, я не вижу Telegram/GitHub на странице входа.

## Acceptance criteria

- [x] Нет кода/env/UI Telegram; Web Push сохранён
- [x] OAuth Яндекс/VK: start → callback → JWT; link/unlink в профиле
- [x] Merge: social id → email → create student; конфликт id → 409
- [x] VK Callback: confirmation, message_new, message_allow/deny
- [x] Outbound chat/notify в VK при `vk_id` + `vk_messages_allowed`
- [x] Inbound текст (+ одно фото) → активный DirectThread
- [x] Антилуп: сообщения из VK не эхоим обратно в VK
- [x] Auth UI: Яндекс/VK; регистрация email или телефон; без GitHub/TG

## API

### OAuth

| Method | Path | Auth | Body / notes |
|--------|------|------|--------------|
| GET | `/api/auth/oauth/{provider}/start/` | AllowAny | `provider=yandex\|vk` → `{ authorize_url, state }` |
| POST | `/api/auth/oauth/{provider}/` | AllowAny | `{ code, redirect_uri, state }` → JWT pair |
| POST | `/api/auth/oauth/{provider}/link/` | JWT | `{ code, redirect_uri, state }` → привязка |
| POST | `/api/auth/oauth/{provider}/unlink/` | JWT | отвязка если остаётся другой способ входа |

### VK bot

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/vk/status/` | JWT → linked, messages_allowed, bot_configured, group_id |
| POST | `/api/vk/webhook/<secret>/` | path secret + body secret |

Existing: `/api/auth/register|login|…`, chat REST/WS без изменений контракта.

## DB

**User:** drop `telegram_*`; add `yandex_id`, `vk_id`, `vk_messages_allowed`.

**notify:** drop `TelegramLinkToken`; optional `VkOutboundDedup` не требуется — антилуп через `source=vk` на сообщении или флаг в create_message.

**ChatMessage:** поле `source` (`site`\|`vk`, default `site`) для антилупа.

## UI

- `#/auth` — кнопки Яндекс/VK; register login = email или телефон
- `#/auth/callback` — обмен code
- Профиль — панель VK (messages allowed, vk.me/club…) + привязки OAuth

## Test plan

- OAuth merge/link/unlink (моки HTTP)
- VK webhook confirmation/secret
- inbound → ChatMessage; outbound mock; no echo loop
- register phone; auth page без TG/GitHub

## Deploy

Env: `YANDEX_OAUTH_*`, `VK_OAUTH_*`, `VK_GROUP_TOKEN`, `VK_GROUP_ID`, `VK_CALLBACK_CONFIRMATION`, `VK_CALLBACK_SECRET`.
После деплоя: migrate + `restart.sh`. Настроить Callback API URL на `/api/vk/webhook/<secret>/`.

## Out of scope

SMS/OTP, полные медиа через VK, GitHub/Google OAuth, отдельный чат «со школой».
