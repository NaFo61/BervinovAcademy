FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    gettext \
    curl \
    vim-tiny \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Копируем pyproject.toml из корня
COPY pyproject.toml /app/

# Копируем backend код
COPY backend/ /app/backend/

# Устанавливаем зависимости из корня
RUN pip install --upgrade pip \
    && pip install -e /app[dev,test]

WORKDIR /app/backend

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000
