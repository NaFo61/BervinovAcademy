#!/usr/bin/env bash
# Генерация scripts/project_prompt.txt для контекста LLM.
# Запуск из любой директории: ./scripts/generate-prompt.sh

set -euo pipefail

echo "============================================================================"
echo "Генерация промта проекта Bervinov Academy"
echo "Результат: scripts/project_prompt.txt"
echo "============================================================================"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1

pick_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo python3
  elif command -v python >/dev/null 2>&1; then
    echo python
  else
    echo ""
  fi
}

PY="$(pick_python)"
if [[ -z "$PY" ]]; then
  echo "Ошибка: не найден Python. Установите Python 3.11+ (команда python3 или python)."
  exit 1
fi

echo "Используется: $PY"
echo

set +e
"$PY" scripts/generate-prompt.py
EXIT_CODE=$?
set -e

echo
echo "============================================================================"
if [[ $EXIT_CODE -eq 0 ]]; then
  echo "Готово!"
else
  echo "Ошибка генерации (код $EXIT_CODE)."
fi
echo "============================================================================"

exit "$EXIT_CODE"
