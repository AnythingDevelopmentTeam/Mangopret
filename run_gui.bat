@echo off
chcp 65001 > nul

:: -------------------------------------------------------
:: Mangopret GUI launcher for Windows
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
:: Check PyQt6
"%PYTHON%" -c "import PyQt6" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo PyQt6 not found. Installing...

    :: Try pip
    "%PYTHON%" -m pip install PyQt6 2>nul
    if %errorlevel% neq 0 (
        echo.
        echo Failed to install PyQt6 automatically.
        echo.
        echo Install manually:
        echo   "%PYTHON%" -m pip install PyQt6
        echo.
        echo Or run CLI mode:
        echo   run.bat install
        echo.
        pause
        exit /b 1
    )
    echo PyQt6 installed successfully.
)

:: Launch GUI
cd /d "%GUI_DIR%"
"%PYTHON%" main_gui.py %*
