@echo off
chcp 65001 > nul

:: -------------------------------------------------------
:: Mangopret CLI launcher for Windows
:: Uses bundled portable Python if available, else system Python
:: -------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "BUNDLED_PYTHON=%SCRIPT_DIR%python\python.exe"
set "GUI_DIR=%SCRIPT_DIR%gui"

:: Find Python: bundled > system python > system python3
set "PYTHON="

if exist "%BUNDLED_PYTHON%" (
    set "PYTHON=%BUNDLED_PYTHON%"
    goto :found_python
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON=python"
    goto :found_python
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON=python3"
    goto :found_python
)

echo.
echo Python not found.
echo.
echo Install from https://python.org
echo Or extract the release archive - it includes portable Python.
echo.
pause
exit /b 1

:found_python
cd /d "%GUI_DIR%"
"%PYTHON%" main.py %*
