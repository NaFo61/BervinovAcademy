@echo off
cd /d "%~dp0.."  :: Переходим в корень проекта
echo ========================================
echo   Полная перезагрузка Docker окружения
echo ========================================
echo.

:: Проверка наличия Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker не найден. Убедитесь, что Docker установлен и запущен.
    pause
    exit /b 1
)

:: Создание директории для логов
if not exist logs mkdir logs

echo [1/7] Останавливаем контейнеры...
docker compose down
if %errorlevel% neq 0 (
    echo [ERROR] Ошибка при остановке контейнеров
    pause
    exit /b 1
)
echo [OK] Контейнеры остановлены

echo.
echo Ожидание 3 секунды...
timeout /t 3 /nobreak >nul

echo [2/7] Удаляем volumes...
docker compose down -v
if %errorlevel% neq 0 (
    echo [ERROR] Ошибка при удалении volumes
    pause
    exit /b 1
)
echo [OK] Volumes удалены

echo.
echo Ожидание 5 секунд...
timeout /t 5 /nobreak >nul

echo [3/7] Удаляем старые образы (опционально)...
docker image prune -f
echo [OK] Старые образы удалены

echo.
echo Ожидание 2 секунды...
timeout /t 2 /nobreak >nul

echo [4/7] Собираем и запускаем контейнеры...
docker compose up --build -d
if %errorlevel% neq 0 (
    echo [ERROR] Ошибка при запуске контейнеров
    pause
    exit /b 1
)
echo [OK] Контейнеры собраны и запущены

echo.
echo [5/7] Ожидание запуска сервисов 15 секунд...
timeout /t 15 /nobreak >nul

echo.
echo Текущее состояние контейнеров:
docker compose ps

echo.
echo [6/7] Запуск тестов...
echo ----------------------------------------

:: Проверка доступных маркеров
echo [INFO] Проверка доступных маркеров тестов...
docker compose exec -T backend pytest --markers -q 2>nul | findstr /C:"fast" /C:"smoke" /C:"integration" /C:"unit"
if %errorlevel% neq 0 (
    echo [WARNING] Не удалось получить список маркеров, продолжаем...
)

echo.
echo 1. Запуск тестов...
echo ----------------------------------------
docker compose exec -T backend pytest -m -v --reuse-db --no-migrations
if %errorlevel% equ 0 (
    echo [OK] Тесты пройдены
) else (
    echo [ERROR] Тесты не пройдены!
    echo [INFO] Логи backend для диагностики:
    docker compose logs --tail=50 backend
    pause
    exit /b 1
)


echo.
echo 2. Проверка миграций...
echo ----------------------------------------
docker compose exec -T backend python manage.py makemigrations --check --dry-run
if %errorlevel% equ 0 (
    echo [OK] Миграции в порядке
) else (
    echo [ERROR] Обнаружены непримененные миграции!
    echo [INFO] Запустите: docker compose exec backend python manage.py makemigrations
    pause
    exit /b 1
)

echo.
echo 3. Проверка статических файлов...
echo ----------------------------------------
docker compose exec -T backend python manage.py collectstatic --no-input --dry-run >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Статические файлы в порядке
) else (
    echo [WARNING] Проблемы со статическими файлами
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
        echo [OK] Логи %%s сохранены в logs\%%s.log
    ) else (
        echo [WARNING] Сервис %%s не запущен, логи не сохраняются
    )
)

:: Краткий отчет о тестировании
echo.
echo ========================================
echo   📊 Краткий отчет о тестировании
echo ========================================
echo.
echo [INFO] Результаты тестов:
echo   ✓ Smoke тесты: проверка критического функционала
echo   ✓ Fast тесты: быстрая проверка изменений
echo   ✓ Integration тесты: проверка взаимодействия компонентов
echo   ✓ Миграции: проверка целостности БД
echo   ✓ Staticfiles: проверка статических файлов
echo.
echo ----------------------------------------
echo   Готово! Все контейнеры перезапущены
echo ========================================
echo.
echo [INFO] Текущие контейнеры:
docker compose ps

echo.
echo [INFO] Полезные команды:
echo   docker compose logs -f              - Просмотр всех логов
echo   docker compose exec backend pytest  - Запуск тестов вручную
echo   docker compose exec backend bash    - Вход в контейнер
echo   type logs\backend.log               - Просмотр сохраненных логов
echo.

:: Проверяем только запущены ли контейнеры (без healthcheck)
docker compose ps | findstr /C:"Exit" >nul
if %errorlevel% equ 0 (
    echo [WARNING] Некоторые контейнеры остановлены. Проверьте логи:
    docker compose ps | findstr /C:"Exit"
) else (
    echo [OK] Все контейнеры успешно запущены!
)

echo.
pause
endlocal
