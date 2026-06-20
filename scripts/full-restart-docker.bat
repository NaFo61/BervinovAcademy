@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0.."

echo ========================================
echo   Docker full restart (DB reset)
echo ========================================
echo.

where docker >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Docker not found. Start Docker Desktop.
    pause
    exit /b 1
)

if not exist logs mkdir logs

echo [1/8] Stopping containers...
docker compose down
if errorlevel 1 (
    echo [ERROR] docker compose down failed
    pause
    exit /b 1
)
echo [OK] Containers stopped

echo.
timeout /t 3 /nobreak >nul

echo [2/8] Removing volumes...
docker compose down -v
if errorlevel 1 (
    echo [ERROR] docker compose down -v failed
    pause
    exit /b 1
)
echo [OK] Volumes removed

echo.
timeout /t 5 /nobreak >nul

echo [3/8] Pruning images and build cache...
docker image prune -f
docker builder prune -af
echo [OK] Prune done

echo.
timeout /t 2 /nobreak >nul

echo [4/8] Building and starting...
docker compose up --build -d
if errorlevel 1 (
    echo [ERROR] docker compose up failed
    pause
    exit /b 1
)
echo [OK] Containers started

echo.
echo [5/8] Waiting 15s for services...
timeout /t 15 /nobreak >nul
docker compose ps

echo.
echo [6/8] seed_data...
docker compose exec -T backend python manage.py seed_data --clear
if errorlevel 1 (
    echo [ERROR] seed_data failed
    pause
    exit /b 1
)
echo [OK] seed_data done

echo.
echo [7/8] pytest...
docker compose exec -T backend pytest -v --reuse-db --no-migrations
if errorlevel 1 (
    echo [ERROR] tests failed
    docker compose logs --tail=50 backend
    pause
    exit /b 1
)
echo [OK] tests passed

echo.
echo Checking migrations...
docker compose exec -T backend python manage.py makemigrations --check --dry-run
if errorlevel 1 (
    echo [ERROR] pending migrations
    pause
    exit /b 1
)
echo [OK] migrations ok

echo.
echo [8/8] Saving logs...
for %%s in (db redis backend celery celery-beat frontend) do (
    docker compose ps %%s 2>nul | findstr /C:"Up" >nul
    if !errorlevel! equ 0 (
        docker compose logs %%s > logs\%%s.log 2>&1
        echo [OK] logs\%%s.log
    ) else (
        echo [WARNING] %%s not running
    )
)

echo.
echo ========================================
echo   Done
echo ========================================
docker compose ps

docker compose ps | findstr /C:"Exit" >nul
if errorlevel 0 (
    echo [WARNING] Some containers exited
    docker compose ps | findstr /C:"Exit"
) else (
    echo [OK] All containers up
)

echo.
pause
endlocal
