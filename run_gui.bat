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
if %errorlevel% equ 0 goto :launch_gui

:: PyQt6 missing — try pip install
echo.
echo PyQt6 not found. Installing...

"%PYTHON%" -m pip install PyQt6 2>nul
if %errorlevel% equ 0 (
    echo PyQt6 installed successfully.
    goto :launch_gui
)

:: pip itself may be missing — bootstrap from bundled get-pip.py
echo pip not available, bootstrapping from bundled get-pip.py...
set "GET_PIP=%SCRIPT_DIR%pip\get-pip.py"
if not exist "%GET_PIP%" (
    echo Error: %GET_PIP% not found
    goto :pip_failed
)

"%PYTHON%" "%GET_PIP%" --no-warn-script-location 2>nul
if %errorlevel% neq 0 (
    echo Failed to bootstrap pip.
    goto :pip_failed
)

:: Now retry PyQt6 install
"%PYTHON%" -m pip install PyQt6 --no-warn-script-location 2>nul
if %errorlevel% neq 0 (
    goto :pip_failed
)
echo PyQt6 installed successfully.
goto :launch_gui

:pip_failed
echo.
echo Failed to install PyQt6 automatically.
echo.
echo Try running: pip\setup.bat
echo Or run CLI mode: run.bat
echo.
pause
exit /b 1

:launch_gui

:: Launch GUI
cd /d "%GUI_DIR%"
"%PYTHON%" main_gui.py %*
