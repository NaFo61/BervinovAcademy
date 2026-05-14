@echo off
chcp 65001 >nul
REM Генерация scripts\project_prompt.txt для контекста LLM.
REM Запуск: scripts\generate-prompt.bat
REM Без паузы в конце: set NOPAUSE=1 или задайте переменную CI.

echo ============================================================================
echo Генерация промта проекта Bervinov Academy
echo Результат: scripts\project_prompt.txt
echo ============================================================================
echo.

cd /d "%~dp0.." || exit /b 1

set "PYEXE="
python3 --version >nul 2>&1
if not errorlevel 1 set "PYEXE=python3"
if not defined PYEXE (
  python --version >nul 2>&1
  if not errorlevel 1 set "PYEXE=python"
)

if not defined PYEXE (
  echo Ошибка: не найден Python. Установите Python 3.11+ ^(python3 или python в PATH^).
  goto :fail
)

echo Используется: %PYEXE%
echo.

"%PYEXE%" scripts\generate-prompt.py
if errorlevel 1 (
  echo.
  echo ============================================================================
  echo Ошибка генерации.
  echo ============================================================================
  if not defined NOPAUSE if not defined CI pause
  exit /b 1
)

echo.
echo ============================================================================
echo Готово!
echo ============================================================================
if not defined NOPAUSE if not defined CI pause
exit /b 0

:fail
if not defined NOPAUSE if not defined CI pause
exit /b 1
