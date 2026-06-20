#!/bin/bash

echo "========================================"
echo "  Перезапуск Docker (БД сохраняется)"
echo "========================================"
echo

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

cd "$(dirname "$0")/.." || exit 1

if ! command -v docker &> /dev/null; then
    print_error "Docker не найден. Убедитесь, что Docker установлен и запущен."
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
fi

echo "[1/2] Останавливаем контейнеры..."
docker compose down || {
    print_error "Ошибка при остановке контейнеров"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}
print_success "Контейнеры остановлены"

echo
echo "[2/2] Запускаем контейнеры..."
docker compose up -d || {
    print_error "Ошибка при запуске контейнеров"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}
print_success "Контейнеры запущены"

echo
docker compose ps
echo
read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
