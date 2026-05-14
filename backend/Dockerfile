FROM python:3.11-slim

# --- Базовые настройки ---
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# --- Системные зависимости ---
# gcc оставляем на случай, если есть .tar.gz (если только wheels — можно убрать)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    gettext \
    curl \
    vim-tiny \
    && rm -rf /var/lib/apt/lists/*

# --- Зависимости (максимальный кэш Docker) ---
# Сначала только requirements + wheels → чтобы не пересобирать каждый раз
COPY requirements.txt /app/
COPY wheels /wheels

RUN pip install --upgrade pip \
    && pip install --prefer-binary --find-links=/wheels -r requirements.txt

# --- Код приложения (после зависимостей) ---
COPY backend/ /app/backend/

WORKDIR /app/backend

# --- Healthcheck ---
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000
