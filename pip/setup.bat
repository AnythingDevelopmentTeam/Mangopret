@echo off
chcp 65001 > nul
:: Mangopret pip bootstrap for Windows
:: Installs pip + PyQt6 when bundled Python has no pip

set "SCRIPT_DIR=%~dp0"
set "GET_PIP=%SCRIPT_DIR%get-pip.py"
set "BUNDLED_PYTHON=%SCRIPT_DIR%..\python\python.exe"

:: Find Python
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

echo Python not found. Install from https://python.org
pause
exit /b 1

:found_python
echo Using: %PYTHON%

:: Check if pip is available
"%PYTHON%" -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo pip is already available.
    goto :install_pyqt6
)

:: Bootstrap pip from bundled get-pip.py
echo pip not found, bootstrapping from bundled get-pip.py...
if not exist "%GET_PIP%" (
    echo Error: %GET_PIP% not found
    echo Download from https://bootstrap.pypa.io/get-pip.py
    pause
    exit /b 1
)

"%PYTHON%" "%GET_PIP%" --no-warn-script-location
if %errorlevel% neq 0 (
    echo Failed to install pip.
    pause
    exit /b 1
)
echo pip installed successfully.

:install_pyqt6
:: Check PyQt6
"%PYTHON%" -c "import PyQt6" 2>nul
if %errorlevel% equ 0 (
    echo PyQt6 already installed.
    goto :done
)

echo Installing PyQt6...
"%PYTHON%" -m pip install "PyQt6>=6.5" --no-warn-script-location
if %errorlevel% neq 0 (
    echo Failed to install PyQt6.
    pause
    exit /b 1
)
echo PyQt6 installed successfully.

:: Install dev extras if requirements-dev.txt exists
if exist "%SCRIPT_DIR%..\requirements-dev.txt" (
    echo Installing development dependencies...
    "%PYTHON%" -m pip install -r "%SCRIPT_DIR%..\requirements-dev.txt" --no-warn-script-location 2>nul
)

:done
echo.
echo Setup complete. Run: run_gui.bat
pause
