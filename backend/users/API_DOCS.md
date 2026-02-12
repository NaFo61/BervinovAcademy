# API Аутентификации

## Обзор

Система аутентификации использует JWT токены для обеспечения безопасного доступа к API. Все эндпоинты поддерживают throttling для защиты от брут-форс атак.

## Базовый URL

```
/api/auth/
```

## Эндпоинты

### 1. Регистрация пользователя

**POST** `/api/auth/register/`

Регистрирует нового пользователя с ролью "student" и возвращает JWT токены.

#### Тело запроса:

```json
{
    "email": "user@example.com",  // опционально, если указан phone
    "phone": "+79991234567",     // опционально, если указан email
    "first_name": "Иван",
    "last_name": "Иванов",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
}
```

**Правила валидации:**
- Обязательно указать email ИЛИ phone
- first_name и last_name обязательны
- Пароль должен содержать минимум 8 символов, включая заглавные/строчные буквы, цифры и специальные символы
- password_confirm должен совпадать с password

#### Успешный ответ (201):

```json
{
    "message": "Пользователь успешно зарегистрирован",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "phone": "+79991234567",
        "first_name": "Иван",
        "last_name": "Иванов",
        "full_name": "Иван Иванов",
        "role": "student",
        "avatar": null,
        "bio": "",
        "date_joined": "2024-01-01T12:00:00Z",
        "last_login": null
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

#### Ошибки (400):

```json
{
    "email": ["Пользователь с таким email уже существует."],
    "password": ["Пароль должен содержать минимум 8 символов."]
}
```

### 2. Вход в систему

**POST** `/api/auth/login/`

Аутентифицирует пользователя по email или телефону и возвращает JWT токены.

#### Тело запроса:

```json
{
    "login": "user@example.com",  // email или телефон
    "password": "SecurePass123!"
}
```

#### Успешный ответ (200):

```json
{
    "message": "Вход выполнен успешно",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "phone": "+79991234567",
        "role": "student",
        "first_name": "Иван",
        "last_name": "Иванов"
    }
}
```

#### Ошибки (400/401):

```json
{
    "non_field_errors": ["Неверные учетные данные."]
}
```

```json
{
    "non_field_errors": ["Учетная запись неактивна."]
}
```

### 3. Обновление токена

**POST** `/api/auth/refresh/`

Обновляет access токен с использованием refresh токена.

#### Тело запроса:

```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Успешный ответ (200):

```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 4. Выход из системы

**POST** `/api/auth/logout/`

Инвалидирует refresh токен (добавляет в черный список).

#### Заголовки:
```
Authorization: Bearer <access_token>
```

#### Тело запроса:

```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Успешный ответ (200):

```json
{
    "message": "Выход выполнен успешно"
}
```

### 5. Получение профиля

**GET** `/api/auth/profile/`

Возвращает данные текущего авторизованного пользователя.

#### Заголовки:
```
Authorization: Bearer <access_token>
```

#### Успешный ответ (200):

```json
{
    "id": 1,
    "email": "user@example.com",
    "phone": "+79991234567",
    "first_name": "Иван",
    "last_name": "Иванов",
    "full_name": "Иван Иванов",
    "role": "student",
    "avatar": null,
    "bio": "",
    "date_joined": "2024-01-01T12:00:00Z",
    "last_login": "2024-01-01T13:00:00Z"
}
```

### 6. Обновление профиля

**PATCH** `/api/auth/profile/`

Обновляет данные текущего авторизованного пользователя.

#### Заголовки:
```
Authorization: Bearer <access_token>
```

#### Тело запроса:

```json
{
    "first_name": "Петр",
    "bio": "Новый био текст"
}
```

#### Успешный ответ (200):

```json
{
    "message": "Профиль успешно обновлен",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "phone": "+79991234567",
        "first_name": "Петр",
        "last_name": "Иванов",
        "full_name": "Петр Иванов",
        "role": "student",
        "avatar": null,
        "bio": "Новый био текст",
        "date_joined": "2024-01-01T12:00:00Z",
        "last_login": "2024-01-01T13:00:00Z"
    }
}
```

## Использование токенов

### Access токен

Используется для аутентификации запросов к защищенным эндпоинтам.

```
Authorization: Bearer <access_token>
```

Время жизни: 15 минут

### Refresh токен

Используется для получения нового access токена.

Время жизни: 7 дней

## Ограничения (Throttling)

- **Регистрация**: 5 запросов в минуту
- **Вход**: 5 запросов в минуту
- **Обновление токена**: 20 запросов в минуту

## Коды ошибок

- **200**: Успешно
- **201**: Создано (регистрация)
- **400**: Ошибка валидации
- **401**: Не авторизован
- **403**: Доступ запрещен
- **429**: Слишком много запросов (throttling)

## Пример использования в JavaScript

```javascript
// Регистрация
const register = async (userData) => {
    const response = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
    });
    return response.json();
};

// Вход
const login = async (credentials) => {
    const response = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials)
    });
    return response.json();
};

// Получение профиля
const getProfile = async (accessToken) => {
    const response = await fetch('/api/auth/profile/', {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        }
    });
    return response.json();
};
```
