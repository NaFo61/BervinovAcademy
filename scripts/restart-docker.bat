@echo off
cd /d "%~dp0.."  :: Переходим в корень проекта
echo ========================================
echo   Полная перезагрузка Docker окружения
echo ========================================
echo.

:: Цвета для Windows (опционально)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

:: Проверка наличия Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo %RED%[ERROR] Docker не найден. Убедитесь, что Docker установлен и запущен.%NC%
    pause
    exit /b 1
)

:: Создание директории для логов
if not exist logs mkdir logs

echo [1/7] Останавливаем контейнеры...
docker compose down
if %errorlevel% neq 0 (
    echo %RED%[ERROR] Ошибка при остановке контейнеров%NC%
    pause
    exit /b 1
)
echo %GREEN%[OK] Контейнеры остановлены%NC%

echo.
echo Ожидание 3 секунды...
timeout /t 3 /nobreak >nul

echo [2/7] Удаляем volumes...
docker compose down -v
if %errorlevel% neq 0 (
    echo %RED%[ERROR] Ошибка при удалении volumes%NC%
    pause
    exit /b 1
)
echo %GREEN%[OK] Volumes удалены%NC%

echo.
echo Ожидание 5 секунд...
timeout /t 5 /nobreak >nul

echo [3/7] Удаляем старые образы (опционально)...
docker image prune -f
echo %GREEN%[OK] Старые образы удалены%NC%

echo.
echo Ожидание 2 секунды...
timeout /t 2 /nobreak >nul

echo [4/7] Собираем и запускаем контейнеры...
docker compose up --build -d
if %errorlevel% neq 0 (
    echo %RED%[ERROR] Ошибка при запуске контейнеров%NC%
    pause
    exit /b 1
)
echo %GREEN%[OK] Контейнеры собраны и запущены%NC%

echo.
echo [5/7] Ожидание запуска сервисов 15 секунд...
timeout /t 15 /nobreak >nul

echo.
echo Текущее состояние контейнеров:
docker compose ps

echo.
echo [6/7] Запуск всех тестов...
echo ----------------------------------------

echo.
echo 1. Запуск всех тестов...
echo ----------------------------------------
docker compose exec -T backend pytest -v --reuse-db --no-migrations
if %errorlevel% equ 0 (
    echo %GREEN%[OK] Все тесты успешно пройдены%NC%
) else (
    echo %RED%[ERROR] Некоторые тесты не пройдены!%NC%
    echo %BLUE%[INFO] Логи backend для диагностики:%NC%
    docker compose logs --tail=50 backend
    pause
    exit /b 1
)

echo.
echo 2. Проверка миграций...
echo ----------------------------------------
docker compose exec -T backend python manage.py makemigrations --check --dry-run
if %errorlevel% equ 0 (
    echo %GREEN%[OK] Миграции в порядке%NC%
) else (
    echo %RED%[ERROR] Обнаружены непримененные миграции!%NC%
    echo %BLUE%[INFO] Запустите: docker compose exec backend python manage.py makemigrations%NC%
    pause
    exit /b 1
)

echo.
echo 3. Проверка статических файлов...
echo ----------------------------------------
docker compose exec -T backend python manage.py collectstatic --no-input --dry-run >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%[OK] Статические файлы в порядке%NC%
) else (
    echo %YELLOW%[WARNING] Проблемы со статическими файлами%NC%
)

echo.
echo ----------------------------------------
echo [7/7] Сохраняем логи в файлы...
echo ----------------------------------------

:: Сохраняем логи всех сервисов
setlocal enabledelayedexpansion

for %%s in (db redis backend celery celery-beat) do (
    docker compose ps %%s 2>nul | findstr /C:"Up" >nul
    if !errorlevel! equ 0 (
        docker compose logs %%s > logs\%%s.log 2>&1
        echo %GREEN%[OK] Логи %%s сохранены в logs\%%s.log%NC%
    ) else (
        echo %YELLOW%[WARNING] Сервис %%s не запущен, логи не сохраняются%NC%
    )
)

:: Краткий отчет о тестировании
echo.
echo ========================================
echo   📊 Краткий отчет о тестировании
echo ========================================
echo.
echo %BLUE%[INFO] Результаты тестов:%NC%
echo   ✓ Все тесты: проверка всего функционала
echo   ✓ Миграции: проверка целостности БД
echo   ✓ Staticfiles: проверка статических файлов
echo.
echo ----------------------------------------
echo   Готово! Все контейнеры перезапущены
echo ========================================
echo.
echo %BLUE%[INFO] Текущие контейнеры:%NC%
docker compose ps

echo.
echo %BLUE%[INFO] Полезные команды:%NC%
echo   docker compose logs -f              - Просмотр всех логов
echo   docker compose exec backend pytest  - Запуск тестов вручную
echo   docker compose exec backend bash    - Вход в контейнер
echo   type logs\backend.log               - Просмотр сохраненных логов
echo.

:: Проверяем только запущены ли контейнеры (без healthcheck)
docker compose ps | findstr /C:"Exit" >nul
if %errorlevel% equ 0 (
    echo %YELLOW%[WARNING] Некоторые контейнеры остановлены. Проверьте логи:%NC%
    docker compose ps | findstr /C:"Exit"
) else (
    echo %GREEN%[OK] Все контейнеры успешно запущены!%NC%
)

echo.
pause
endlocal
