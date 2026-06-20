@echo off
setlocal EnableExtensions

cd /d "%~dp0.."

echo ========================================
echo   Docker restart (DB preserved)
echo ========================================
echo.

where docker >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Docker not found. Start Docker Desktop.
    pause
    exit /b 1
)

echo [1/2] Stopping containers...
docker compose down
if errorlevel 1 (
    echo [ERROR] docker compose down failed
    pause
    exit /b 1
)
echo [OK] Containers stopped

echo.
echo [2/2] Starting containers...
docker compose up -d
if errorlevel 1 (
    echo [ERROR] docker compose up failed
    pause
    exit /b 1
)
echo [OK] Containers started

echo.
docker compose ps
echo.
pause
endlocal
