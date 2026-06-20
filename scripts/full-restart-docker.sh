#!/bin/bash

echo "========================================"
echo "  Полная перезагрузка Docker (сброс БД)"
echo "========================================"
echo

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

cd "$(dirname "$0")/.." || exit 1

print_info "Рабочая директория: $(pwd)"
echo

if ! command -v docker &> /dev/null; then
    print_error "Docker не найден. Убедитесь, что Docker установлен и запущен."
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
fi

mkdir -p logs

echo "[1/8] Останавливаем контейнеры..."
docker compose down || {
    print_error "Ошибка при остановке контейнеров"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}
print_success "Контейнеры остановлены"

echo
echo "Ожидание 3 секунды..."
sleep 3

echo "[2/8] Удаляем volumes..."
docker compose down -v || {
    print_error "Ошибка при удалении volumes"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}
print_success "Volumes удалены"

echo
echo "Ожидание 5 секунд..."
sleep 5

echo "[3/8] Удаляем старые образы и кэш сборки..."
docker image prune -f
docker builder prune -af
print_success "Старые образы и кэш сборки удалены"

echo
echo "Ожидание 2 секунды..."
sleep 2

echo "[4/8] Собираем и запускаем контейнеры..."
docker compose up --build -d || {
    print_error "Ошибка при запуске контейнеров"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}
print_success "Контейнеры собраны и запущены"

echo
echo "[5/8] Ожидание запуска сервисов 15 секунд..."
sleep 15

echo
echo "Текущее состояние контейнеров:"
docker compose ps

echo
echo "[6/8] Наполнение БД (seed_data)..."
if docker compose exec -T backend python manage.py seed_data --clear; then
    print_success "seed_data выполнен"
else
    print_error "seed_data завершился с ошибкой"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
fi

echo
echo "[7/8] Запуск всех тестов..."
if docker compose exec -T backend pytest -v --reuse-db --no-migrations; then
    print_success "Все тесты успешно пройдены"
else
    print_error "Некоторые тесты не пройдены!"
    docker compose logs --tail=50 backend
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
fi

echo
if docker compose exec -T backend python manage.py makemigrations --check --dry-run; then
    print_success "Миграции в порядке"
else
    print_error "Обнаружены непримененные миграции!"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
fi

echo
echo "[8/8] Сохраняем логи в файлы..."
for service in db redis backend celery celery-beat frontend; do
    if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
        docker compose logs "$service" > "logs/${service}.log" 2>&1
        print_success "Логи $service сохранены в logs/${service}.log"
    else
        print_warning "Сервис $service не запущен, логи не сохраняются"
    fi
done

echo
echo "========================================"
echo "  Готово! Полная перезагрузка завершена"
echo "========================================"
docker compose ps

if docker compose ps | grep -q "Exit"; then
    print_warning "Некоторые контейнеры остановлены:"
    docker compose ps | grep "Exit"
else
    print_success "Все контейнеры успешно запущены!"
fi

echo
read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
