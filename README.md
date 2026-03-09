# Bervinov Academy - Educational Platform
![Bervinov Academy](https://via.placeholder.com/800x200/2D3748/FFFFFF?text=Bervinov+Academy+-+Modern+Learning+Platform)

Bervinov Academy - это современная образовательная платформа с менторской поддержкой, построенная по принципам Stepik. Платформа предоставляет интерактивные курсы по программированию с автоматической проверкой заданий и персональными менторами.

### 🎯 Основные возможности

- **📚 Структурированные курсы** с модулями и уроками
- **👨‍🏫 Менторская поддержка** для каждого студента
- **💻 Автоматическая проверка** кодовых заданий
- **📊 Отслеживание прогресса** с детальной статистикой
- **💬 Система коммуникации** между студентами и менторами
- **💰 Гибкая система подписок**

## 🏗️ Архитектура проекта

### ER-диаграмма базы данных

![ER Diagram](docs/images/er-diagram.png)

*Примечание: Добавьте скриншот вашей ER-диграммы в папку `docs/images/`*

### Структура приложений Django

```
backend/
├── users/                 # Пользователи и аутентификация
├── subscriptions/         # Планы и подписки
├── education/            # Курсы, модули, уроки, задания
├── progress/             # Прогресс студентов, выполнения заданий
├── mentoring/            # Менторы и связи ментор-студент
├── content/              # Технологии и теги
└── communication/        # Комментарии, сообщения, закладки
```

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.9+
- Git
- Virtualenv

### Установка и запуск

1. **Клонирование репозитория**
```bash
git clone <your-repository-url>
cd BervinovAcademy
```

2. **Активация виртуального окружения**
```bash
# Создание виртуального окружения (если еще не создано)
python -m venv .venv

# Активация на Windows
.venv\Scripts\activate

# Активация на macOS/Linux
source .venv/bin/activate
```

3. **Установка зависимостей**
```bash
pip install -e .
```

4. **Настройка окружения**
```bash
# Копируем пример файла окружения
copy .env.example .env

# Редактируем настройки (при необходимости)
# Отредактируйте .env файл под ваши нужды
```

5. **Настройка базы данных**
```bash
# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser
```

6. **Запуск сервера разработки**
```bash
python manage.py runserver
```

7. **Откройте в браузере**
```
http://localhost:8000/
```

Админ-панель: `http://localhost:8000/admin/`

## 🗃️ Наполнение тестовыми данными

Для заполнения базы тестовыми данными выполните:

```bash
python manage.py loaddata fixtures/initial_data.json
```

Или используйте кастомные команды:

```bash
python manage.py create_sample_data
```

## 🛠️ Разработка

### Структура проекта

```
BervinovAcademy/
├── backend/                 # Django проект
│   ├── school/             # Настройки проекта
│   ├── users/              # Приложение пользователей
│   ├── education/          # Образовательный контент
│   ├── progress/           # Отслеживание прогресса
│   ├── mentoring/          # Менторская система
│   ├── subscriptions/      # Подписки и платежи
│   ├── content/            # Технологии и теги
│   └── communication/      # Коммуникации
├── frontend/               # React/Vue фронтенд (будущее)
├── docs/                   # Документация
├── scripts/                # Вспомогательные скрипты
└── .github/                # GitHub workflows
```

### Полезные команды

```bash
# Создание миграций
python manage.py makemigrations

# Проверка миграций
python manage.py makemigrations --check --dry-run

# Запуск тестов
python manage.py test

# Проверка кода
python manage.py check
```

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 📊 Модели данных

### Основные сущности

- **Users** - Пользователи системы (студенты, менторы, администраторы)
- **Courses** - Курсы с модульной структурой
- **Assignments** - Задания с автоматической проверкой
- **StudentAssignments** - Выполнения заданий студентами
- **Mentor-Student** - Связи между менторами и студентами
- **Subscriptions** - Подписки и тарифные планы

## 🧪 Тестирование

```bash
# Запуск всех тестов
python manage.py test

# Запуск тестов конкретного приложения
python manage.py test users
python manage.py test education

# Запуск с покрытием
coverage run manage.py test
coverage report
```

## 📝 API Endpoints

*Документация API будет добавлена после реализации REST API*

## 🚀 Деплой

### Продакшен настройки

```python
# В settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
```

### Docker развертывание

```dockerfile
# Dockerfile будет добавлен позже
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте feature ветку (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - смотрите файл [LICENSE](LICENSE) для деталей.

## 📞 Поддержка

Если у вас возникли вопросы:

- Создайте Issue в репозитории
- Напишите на email: support@bervinovacademy.com
- Обратитесь к технической документации в папке `docs/`

---

**Bervinov Academy** © 2024 - Modern Education Platform
