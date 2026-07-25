#!/usr/bin/env bash
# Полный перезапуск: удаление volumes и старых образов, seed_data.
# Запуск: /opt/bervinov-academy/full-restart.sh
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "${APP_DIR}/lib.sh"
cd "$APP_DIR"

if ! command -v docker >/dev/null 2>&1; then
  print_error "Docker не найден."
  exit 1
fi

echo "========================================"
echo "  Полный перезапуск (сброс БД и данных)"
echo "========================================"
print_warning "Будут удалены volumes: postgres, redis, media, static"
echo

read -r -p "Продолжить? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Отменено."
  exit 0
fi

echo
echo "[1/7] Останавливаем контейнеры..."
docker compose down
print_success "Контейнеры остановлены"

echo
echo "[2/7] Удаляем volumes..."
docker compose down -v
print_success "Volumes удалены"

echo
echo "[3/7] Удаляем неиспользуемые образы..."
docker image prune -af || true
print_success "Старые образы удалены"

echo
echo "[4/7] Загружаем свежие образы (с повторами)..."
compose_pull
print_success "Образы загружены"

echo
echo "[5/7] Подтягиваем образ песочницы..."
warmup_sandbox
print_success "Образ code-check-sandbox готов"

echo
echo "[6/7] Запускаем стек..."
docker compose up -d --remove-orphans
print_success "Контейнеры запущены"

echo
echo "Ожидание миграций и health check..."
if ! wait_for_health "http://127.0.0.1:18080/health/" 15; then
  print_error "Health check не прошёл"
  docker compose ps
  docker compose logs --tail=50 backend nginx
  exit 1
fi

echo
echo "[7/7] Наполнение БД (seed_data)..."
docker compose exec -T backend python manage.py seed_data --clear
print_success "seed_data выполнен"

echo
docker compose ps
print_success "Полный перезапуск завершён"
