#!/bin/bash

echo "========================================"
echo "  Полная перезагрузка Docker окружения"
echo "========================================"
echo

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции для вывода
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# Перейти в корень проекта
cd "$(dirname "$0")/.." || exit 1

print_info "Рабочая директория: $(pwd)"
echo

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker не найден. Убедитесь, что Docker установлен и запущен."
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
fi

# Создание директории для логов
mkdir -p logs

echo "[1/7] Останавливаем контейнеры..."
docker compose down || {
    print_error "Ошибка при остановке контейнеров"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}
print_success "Контейнеры остановлены"

echo
echo "Ожидание 3 секунды..."
sleep 3

echo "[2/7] Удаляем volumes..."
docker compose down -v || {
    print_error "Ошибка при удалении volumes"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}
print_success "Volumes удалены"

echo
echo "Ожидание 5 секунд..."
sleep 5

echo "[3/7] Удаляем старые образы (опционально)..."
docker image prune -f
print_success "Старые образы удалены"

echo
echo "Ожидание 2 секунды..."
sleep 2

echo "[4/7] Собираем и запускаем контейнеры..."
docker compose up --build -d || {
    print_error "Ошибка при запуске контейнеров"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
}
print_success "Контейнеры собраны и запущены"

echo
echo "[5/7] Ожидание запуска сервисов 15 секунд..."
print_info "Ожидание 15 секунд..."
sleep 15

echo
echo "Текущее состояние контейнеров:"
docker compose ps

echo
echo "[6/7] Запуск всех тестов..."
echo "----------------------------------------"

# Запуск всех тестов без маркеров
print_info "1. Запуск всех тестов..."
echo "----------------------------------------"
if docker compose exec -T backend pytest -v --reuse-db --no-migrations; then
    print_success "Все тесты успешно пройдены"
else
    print_error "Некоторые тесты не пройдены!"
    print_info "Логи backend для диагностики:"
    docker compose logs --tail=50 backend
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
fi

echo
print_info "2. Проверка миграций..."
echo "----------------------------------------"
if docker compose exec -T backend python manage.py makemigrations --check --dry-run; then
    print_success "Миграции в порядке"
else
    print_error "Обнаружены непримененные миграции!"
    print_info "Запустите: docker compose exec backend python manage.py makemigrations"
    read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
    exit 1
fi

echo
print_info "3. Проверка статических файлов..."
echo "----------------------------------------"
if docker compose exec -T backend python manage.py collectstatic --no-input --dry-run > /dev/null 2>&1; then
    print_success "Статические файлы в порядке"
else
    print_warning "Проблемы со статическими файлами"
fi

echo
echo "----------------------------------------"
echo "[7/7] Сохраняем логи в файлы..."
echo "----------------------------------------"

# Сохраняем логи всех сервисов
for service in db redis backend celery celery-beat; do
    if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
        docker compose logs "$service" > "logs/${service}.log" 2>&1
        print_success "Логи $service сохранены в logs/${service}.log"
    else
        print_warning "Сервис $service не запущен, логи не сохраняются"
    fi
done

# Краткий отчет о тестировании
echo
echo "========================================"
echo "  📊 Краткий отчет о тестировании"
echo "========================================"
echo
print_info "Результаты тестов:"
echo "  ✓ Все тесты: проверка всего функционала"
echo "  ✓ Миграции: проверка целостности БД"
echo "  ✓ Staticfiles: проверка статических файлов"
echo
echo "----------------------------------------"
echo "  Готово! Все контейнеры перезапущены"
echo "========================================"
echo
print_info "Текущие контейнеры:"
docker compose ps

echo
print_info "Полезные команды:"
echo "  docker compose logs -f              # Просмотр всех логов"
echo "  docker compose exec backend pytest  # Запуск тестов вручную"
echo "  docker compose exec backend bash    # Вход в контейнер"
echo "  cat logs/backend.log                 # Просмотр сохраненных логов"
echo

# Проверяем только запущены ли контейнеры (без healthcheck)
if docker compose ps | grep -q "Exit"; then
    print_warning "Некоторые контейнеры остановлены. Проверьте логи:"
    docker compose ps | grep "Exit"
else
    print_success "Все контейнеры успешно запущены!"
fi

echo
read -n 1 -s -r -p "Нажмите любую клавишу для продолжения..."
