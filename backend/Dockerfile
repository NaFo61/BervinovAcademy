FROM python:3.11-slim

# --- Базовые настройки ---
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# --- Системные зависимости ---
# gcc оставляем на случай, если есть .tar.gz (если только wheels — можно убрать)
RUN set -eux; \
    success=0; \
    for i in 1 2 3 4 5; do \
        if apt-get update && apt-get install -y --no-install-recommends \
            postgresql-client \
            build-essential \
            gettext \
            curl \
            vim-tiny; then \
            success=1; break; \
        fi; \
        echo "apt failed, retry $i/5..."; sleep 10; \
    done; \
    test "$success" -eq 1; \
    rm -rf /var/lib/apt/lists/*

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
