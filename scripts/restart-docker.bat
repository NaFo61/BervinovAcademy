@echo off
cd /d "%~dp0.."  # Переходим в корень проекта
echo ========================================
echo   Полная перезагрузка Docker окружения
echo ========================================
echo.

echo [1/6] Останавливаем контейнеры...
docker compose down
if %errorlevel% neq 0 (
    echo Ошибка при остановке контейнеров
    pause
    exit /b 1
)

echo.
echo Ожидание 3 секунды...
timeout /t 3 /nobreak >nul

echo [2/6] Удаляем volumes...
docker compose down -v
if %errorlevel% neq 0 (
    echo Ошибка при удалении volumes
    pause
    exit /b 1
)

echo.
echo Ожидание 5 секунд...
timeout /t 5 /nobreak >nul

echo [3/6] Удаляем старые образы (опционально)...
docker image prune -f

echo.
echo Ожидание 2 секунды...
timeout /t 2 /nobreak >nul

echo [4/6] Собираем и запускаем контейнеры...
docker compose up --build -d
if %errorlevel% neq 0 (
    echo Ошибка при запуске контейнеров
    pause
    exit /b 1
)

echo.
echo [5/6] Ждем запуска сервисов (30 секунд)...
echo Проверяем состояние контейнеров...
timeout /t 10 /nobreak >nul

echo.
docker compose ps

timeout /t 20 /nobreak >nul

echo.
echo [6/6] Сохраняем логи celery в файл...
docker compose logs celery > web_development_logs.txt
if %errorlevel% neq 0 (
    echo Логи celery могут быть пустыми (сервис еще не запущен)
) else (
    echo Логи успешно сохранены в web_development_logs.txt
)

echo.
echo ========================================
echo   Готово! Все контейнеры перезапущены
echo ========================================
echo.
echo Текущие контейнеры:
docker compose ps

echo.
echo Можно посмотреть логи всех сервисов:
echo docker compose logs -f
echo.
pause