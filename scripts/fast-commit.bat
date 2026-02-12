@echo off
chcp 65001 >nul

:: Цвета для вывода (используем ANSI escape codes для Windows 10+)
if not defined NOCOLOR (
    if exist "%SystemRoot%\System32\findstr.exe" (
        "%SystemRoot%\System32\findstr.exe" /R /C:"^" 2>nul && (
            set "RED=[91m"
            set "GREEN=[92m"
            set "YELLOW=[93m"
            set "BLUE=[94m"
            set "NC=[0m"
            set "COLOR_ECHO=echo.[%BLUE%]ℹ %NC%"
        ) || (
            set "RED="
            set "GREEN="
            set "YELLOW="
            set "BLUE="
            set "NC="
            set "COLOR_ECHO=echo.ℹ"
        )
    )
)

:: Функции для вывода
set "SUCCESS_ECHO=echo.[%GREEN%]✓ %NC%"
set "ERROR_ECHO=echo.[%RED%]✗ %NC%"
set "WARNING_ECHO=echo.[%YELLOW%]⚠ %NC%"
set "INFO_ECHO=echo.[%BLUE%]ℹ %NC%"

echo.
echo ========================================
echo    Smart Commit - Windows Version
echo ========================================
echo.

:: Проверка что мы в git репозитории
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    %ERROR_ECHO% Не git репозиторий!
    pause
    exit /b 1
)

:: Получаем сообщение коммита
if "%~1"=="" (
    %ERROR_ECHO% Укажите сообщение коммита!
    echo Использование: smart-commit.bat "ваше сообщение"
    pause
    exit /b 1
)

set "COMMIT_MSG=%*"

:: Шаг 1: Добавляем все изменения
%INFO_ECHO% 1. Добавление всех изменений...
git add .
if errorlevel 1 (
    %ERROR_ECHO% Ошибка при добавлении файлов!
    pause
    exit /b 1
)
%SUCCESS_ECHO% Все изменения добавлены

for /f "delims=" %%i in ('git diff --cached --name-only') do set "STAGED_FILES=%%i"
if defined STAGED_FILES (
    %INFO_ECHO% Файлы:
    git diff --cached --name-only | sed "s/^/     /"
)
echo.

:: Шаг 2: Запускаем pre-commit hooks
%INFO_ECHO% 2. Запуск pre-commit hooks...
echo.
call pre-commit run 2>&1
echo.

:: Шаг 3: Проверяем и добавляем изменения от hooks
%INFO_ECHO% 3. Проверка изменений от hooks...
echo.

:: Проверяем есть ли unstaged изменения
git diff --quiet
if errorlevel 1 (
    %WARNING_ECHO% Файлы изменены hooks:
    echo.
    git diff --name-only | sed "s/^/     /"
    echo.
    
    %INFO_ECHO% Изменения:
    echo.
    git diff --stat | sed "s/^/     /"
    echo.
    
    %INFO_ECHO% Добавляем исправления...
    git add .
    if errorlevel 1 (
        %ERROR_ECHO% Ошибка при добавлении исправлений!
        pause
        exit /b 1
    )
    %SUCCESS_ECHO% Исправления добавлены
) else (
    %SUCCESS_ECHO% Файлы не изменились
)
echo.

:: Шаг 4: Создаем коммит
%INFO_ECHO% 4. Создание коммита: "%COMMIT_MSG%"
echo.

:: Проверяем есть ли staged изменения
git diff --cached --quiet
if not errorlevel 1 (
    %ERROR_ECHO% Нет изменений для коммита!
    pause
    exit /b 1
)

:: Создаем коммит
git commit --no-verify -m "%COMMIT_MSG%"
if errorlevel 1 (
    %ERROR_ECHO% Не удалось создать коммит!
    pause
    exit /b 1
)

%SUCCESS_ECHO% Коммит создан успешно
echo.

:: Показываем результат
%INFO_ECHO% Результат:
echo.
for /f "tokens=*" %%i in ('git log -1 --oneline') do echo     %%i
for /f "skip=1 tokens=*" %%i in ('git log -1 --stat') do echo     %%i

echo.
%SUCCESS_ECHO% Готово!
echo.
pause