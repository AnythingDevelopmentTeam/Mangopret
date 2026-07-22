@echo off
chcp 65001 > nul
cd /d "%~dp0gui"
python main.py %*
if %errorlevel% neq 0 (
    echo.
    echo If Python is not installed, install it from https://python.org
    echo Then run: pip install -r gui\requirements.txt
    pause
)
