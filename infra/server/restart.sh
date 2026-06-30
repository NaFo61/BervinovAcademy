#!/usr/bin/env bash
# Перезапуск стека на сервере (БД и volumes сохраняются).
# Запуск: /opt/bervinov_academy/restart.sh
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

if ! command -v docker >/dev/null 2>&1; then
  print_error "Docker не найден."
  exit 1
fi

wait_for_health() {
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS "http://127.0.0.1:18080/health/" >/dev/null; then
      print_success "Health check OK"
      return 0
    fi
    echo "Ожидание backend... ($i/10)"
    sleep 10
  done
  print_error "Health check не прошёл"
  docker compose ps
  docker compose logs --tail=50 backend nginx
  return 1
}

echo "========================================"
echo "  Перезапуск сервера (БД сохраняется)"
echo "========================================"
echo

echo "[1/4] Загружаем образы..."
docker compose pull
print_success "Образы обновлены"

echo
echo "[2/4] Подтягиваем образ песочницы..."
docker compose run --rm code-check-sandbox true
print_success "Образ code-check-sandbox готов"

echo
echo "[3/4] Перезапускаем контейнеры..."
docker compose up -d --remove-orphans
print_success "Контейнеры запущены"

echo
echo "[4/4] Проверка health..."
wait_for_health

echo
docker image prune -f >/dev/null
docker compose ps
print_success "Перезапуск завершён"
