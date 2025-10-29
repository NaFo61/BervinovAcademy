FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только необходимые зависимости
RUN apt-get update && apt-get install -y postgresql-client gcc && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY ./backend .

EXPOSE 8000