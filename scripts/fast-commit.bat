@echo off
setlocal enabledelayedexpansion

:: Цвета для Windows
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

:: Функции для вывода сообщений
goto :main

:print_success
echo %GREEN%✓ %~1%NC%
exit /b 0

:print_error
echo %RED%✗ %~1%NC%
exit /b 0

:print_warning
echo %YELLOW%⚠ %~1%NC%
exit /b 0

:print_info
echo %BLUE%ℹ %~1%NC%
exit /b 0

:main

:: Проверяем наличие git
where git >nul 2>nul
if %errorlevel% neq 0 (
    call :print_error "Git не установлен или не добавлен в PATH!"
    exit /b 1
)

:: Переходим в корень репозитория
for /f "tokens=*" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "GIT_ROOT=%%i"
if "%GIT_ROOT%"=="" (
    call :print_error "Не удалось найти корень git репозитория!"
    exit /b 1
)
cd /d "%GIT_ROOT%"

:: Проверяем наличие сообщения коммита
set "COMMIT_MSG=%*"
if "%COMMIT_MSG%"=="" (
    call :print_error "Укажите сообщение коммита!"
    echo Использование: %~nx0 "Ваше сообщение коммита"
    exit /b 1
)

call :print_info "Добавляем изменения..."
git add .
call :print_success "Готово"
echo.

:: Проверяем наличие pre-commit и его конфига
where pre-commit >nul 2>nul
if %errorlevel% equ 0 (
    if exist ".pre-commit-config.yaml" (
        call :print_info "Pre-commit хуки:"
        echo.

        :: Запускаем pre-commit на всех staged файлах
        pre-commit run

        :: Проверяем были ли изменения после pre-commit
        git diff --quiet >nul 2>nul
        if %errorlevel% neq 0 (
            echo.
            git add .
            call :print_success "Исправления добавлены"
        )
    ) else (
        call :print_warning "Файл .pre-commit-config.yaml не найден"
    )
) else (
    call :print_warning "Pre-commit не установлен"
)
echo.

:: Проверяем есть ли изменения для коммита
git diff --cached --quiet
if %errorlevel% equ 0 (
    call :print_error "Нет изменений для коммита!"
    exit /b 1
)

:: Выполняем коммит
git commit -m "%COMMIT_MSG%"
if %errorlevel% equ 0 (
    echo.
    call :print_success "Результат:"
    echo.

    :: Показываем последний коммит (без sed)
    echo Последний коммит:
    echo --------------------------------
    git log -1 --pretty=format:"%%h %%s%%nAuthor: %%an <%%ae>%%nDate: %%ad%%n%%n%%b" --date=local
    echo --------------------------------
    echo.

    :: Показываем статистику изменений
    git show --stat --pretty=format:""
)

exit /b 0
