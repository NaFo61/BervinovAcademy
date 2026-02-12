#!/bin/bash
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

cd "$(git rev-parse --show-toplevel)"

COMMIT_MSG="$*"
if [ -z "$COMMIT_MSG" ]; then
    print_error "Укажите сообщение коммита!"
    exit 1
fi

print_info "Добавляем изменения..."
git add .
print_success "Готово"
echo ""

if command -v pre-commit &> /dev/null && [ -f ".pre-commit-config.yaml" ]; then
    print_info "Pre-commit хуки:"
    echo ""
    
    STAGED_FILES=$(git diff --cached --name-only)
    if [ -n "$STAGED_FILES" ]; then
        pre-commit run --files $STAGED_FILES
    fi
    
    if ! git diff --quiet; then
        echo ""
        git add .
        print_success "Исправления добавлены"
    fi
else
    print_warning "Pre-commit не настроен"
fi
echo ""

if git diff --cached --quiet; then
    print_error "Нет изменений для коммита!"
    exit 1
fi

if git commit -m "$COMMIT_MSG"; then
    echo ""
    print_success "Результат:"
    echo ""
    git log -1 --stat --pretty=format:"%h %s%nAuthor: %an <%ae>%nDate:   %ad%n%n    %b" --date=local | sed 's/^/     /'
    echo ""
fi
