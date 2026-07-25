#!/usr/bin/env bash
# Обновление без сброса БД.
# Запуск: /opt/bervinov-academy/restart.sh
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
echo "  Обновление (БД сохраняется)"
echo "========================================"
echo ""

if [ ! -f .env ]; then
  print_error "Файл .env не найден. Скопируйте .env.prod.example в .env и заполните."
  exit 1
fi

echo "[1/5] Остановка контейнеров..."
docker compose down
print_success "Контейнеры остановлены"

echo "[2/5] Загрузка образов (с повторами)..."
compose_pull
print_success "Образы загружены"

echo "[3/5] Прогрев code-check-sandbox..."
warmup_sandbox
print_success "Sandbox готов"

echo "[4/5] Запуск сервисов..."
docker compose up -d --remove-orphans
print_success "Сервисы запущены"

echo "[5/5] Очистка неиспользуемых образов..."
docker image prune -f || true
print_success "Очистка выполнена"

echo ""
echo "Ожидание готовности backend..."
if wait_for_health "http://127.0.0.1:18080/health/" 15; then
  print_success "Деплой завершён"
  docker compose ps
else
  print_error "Health check не прошёл"
  docker compose ps
  docker compose logs --tail=50 backend nginx
  exit 1
fi
