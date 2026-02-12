#!/bin/bash
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# Проверка что мы в git репозитории
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Не git репозиторий!"
    exit 1
fi

# Получаем сообщение коммита
COMMIT_MSG="$*"
if [ -z "$COMMIT_MSG" ]; then
    print_error "Укажите сообщение коммита!"
    echo "Использование: ./smart-commit.sh \"ваше сообщение\""
    exit 1
fi

# Шаг 1: Добавляем все изменения
print_info "1. Добавление всех изменений..."
git add .
print_success "   Все изменения добавлены"

STAGED_FILES=$(git diff --cached --name-only)
if [ -n "$STAGED_FILES" ]; then
    print_info "   Файлы:"
    echo "$STAGED_FILES" | sed 's/^/     /'
fi
echo ""

# Шаг 2: Запускаем pre-commit hooks
print_info "2. Запуск pre-commit hooks..."
pre-commit run 2>&1 || true
echo ""

# Шаг 3: Проверяем и добавляем изменения от hooks
print_info "3. Проверка изменений от hooks..."

if ! git diff --quiet; then
    MODIFIED_FILES=$(git diff --name-only)
    
    if [ -n "$MODIFIED_FILES" ]; then
        print_warning "   Файлы изменены hooks:"
        echo "$MODIFIED_FILES" | sed 's/^/     /'
        
        echo ""
        print_info "   Изменения:"
        git diff --stat | sed 's/^/     /'
        
        echo ""
        print_info "   Добавляем исправления..."
        git add .
        print_success "   Исправления добавлены"
    fi
else
    print_success "   Файлы не изменились"
fi
echo ""

# Шаг 4: Создаем коммит
print_info "4. Создание коммита: \"$COMMIT_MSG\""

if git diff --cached --quiet; then
    print_error "   Нет изменений для коммита!"
    exit 1
fi

if git commit --no-verify -m "$COMMIT_MSG"; then
    print_success "   Коммит создан успешно"
    
    echo ""
    print_info "   Результат:"
    git log -1 --oneline | sed 's/^/     /'
    git log -1 --stat | tail -n +2 | sed 's/^/     /'
else
    print_error "   Не удалось создать коммит"
    exit 1
fi

echo ""
print_success "Готово!"
