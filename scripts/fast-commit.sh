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

# Сохраняем корневую директорию проекта
ROOT_DIR=$(git rev-parse --show-toplevel)
cd "$ROOT_DIR"
print_info "Корень проекта: $ROOT_DIR"

# Проверка что мы в git репозитории
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Не git репозиторий!"
    exit 1
fi

# Получаем сообщение коммита
COMMIT_MSG="$*"
if [ -z "$COMMIT_MSG" ]; then
    print_error "Укажите сообщение коммита!"
    echo "Использование: ./scripts/fast-commit.sh \"ваше сообщение\""
    exit 1
fi

# Проверка наличия pre-commit
check_pre_commit() {
    if ! command -v pre-commit &> /dev/null; then
        print_error "pre-commit не установлен!"
        print_info "Активируйте виртуальное окружение:"
        echo "  source .venv/Scripts/activate"
        exit 1
    fi
    
    if [ ! -f ".pre-commit-config.yaml" ]; then
        print_error "Файл .pre-commit-config.yaml не найден в корне проекта!"
        exit 1
    else
        print_success "Pre-commit config найден"
    fi
}

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
check_pre_commit

# Получаем список файлов в стейдже
STAGED_FILES_LIST=$(git diff --cached --name-only)

if [ -n "$STAGED_FILES_LIST" ]; then
    # Запускаем pre-commit на всех файлах в стейдже
    if ! pre-commit run --files $STAGED_FILES_LIST; then
        print_warning "   Pre-commit hooks вернули ошибки"
    else
        print_success "   Pre-commit hooks выполнены успешно"
    fi
else
    print_warning "   Нет файлов в стейдже для проверки"
fi
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

if git commit -m "$COMMIT_MSG"; then
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
