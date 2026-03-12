FROM python:3.11-slim

WORKDIR /app

# Добавляем curl и vim для дебага
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    gettext \
    curl \
    vim-tiny \
    && rm -rf /var/lib/apt/lists/*

# Оптимизация переменных окружения Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Копируем pyproject.toml в корень
COPY pyproject.toml /app/

# Копируем весь backend со всеми поддиректориями
COPY backend/ /app/backend/

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install -e .[dev,test]

WORKDIR /app/backend

# Healthcheck для мониторинга
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000
