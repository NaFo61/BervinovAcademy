#!/bin/bash

echo "========================================"
echo "  Полная перезагрузка Docker окружения"
echo "========================================"
echo

# Перейти в корень проекта
cd "$(dirname "$0")/.." || exit 1

echo "[1/6] Останавливаем контейнеры..."
docker compose down || {
    echo "Ошибка при остановке контейнеров"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}

echo
echo "Ожидание 3 секунды..."
sleep 3

echo "[2/6] Удаляем volumes..."
docker compose down -v || {
    echo "Ошибка при удалении volumes"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}

echo
echo "Ожидание 5 секунд..."
sleep 5

echo "[3/6] Удаляем старые образы (опционально)..."
docker image prune -f

echo
echo "Ожидание 2 секунды..."
sleep 2

echo "[4/6] Собираем и запускаем контейнеры..."
docker compose up --build -d || {
    echo "Ошибка при запуске контейнеров"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}

echo
echo "[5/6] Ждем запуска сервисов (30 секунд)..."
echo "Проверяем состояние контейнеров..."
sleep 10

echo
docker compose ps

sleep 20

echo
echo "[6/6] Сохраняем логи celery в файл..."
docker compose logs celery > web_development_logs.txt 2>&1 || {
    echo "Логи celery могут быть пустыми (сервис еще не запущен)"
}

echo
echo "========================================"
echo "  Готово! Все контейнеры перезапущены"
echo "========================================"
echo
echo "Текущие контейнеры:"
docker compose ps

echo
echo "Можно посмотреть логи всех сервисов:"
echo "docker compose logs -f"
echo

read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."