#!/usr/bin/env bash
# Полный перезапуск: удаление volumes и старых образов, seed_data.
# Запуск: /opt/bervinov_academy/full-restart.sh
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

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
docker image prune -af
print_success "Старые образы удалены"

echo
echo "[4/7] Загружаем свежие образы..."
docker compose pull
print_success "Образы загружены"

echo
echo "[5/7] Подтягиваем образ песочницы..."
docker compose run --rm code-check-sandbox true
print_success "Образ code-check-sandbox готов"

echo
echo "[6/7] Запускаем стек..."
docker compose up -d --remove-orphans
print_success "Контейнеры запущены"

echo
echo "Ожидание миграций и health check..."
wait_for_health

echo
echo "[7/7] Наполнение БД (seed_data)..."
docker compose exec -T backend python manage.py seed_data --clear
print_success "seed_data выполнен"

echo
docker compose ps
print_success "Полный перезапуск завершён"
