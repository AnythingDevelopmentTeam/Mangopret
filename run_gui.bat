@echo off
chcp 65001 > nul
cd /d "%~dp0"
python gui\app.py
if %errorlevel% neq 0 (
    echo Python not found. Install Python 3.8+ from https://www.python.org/downloads/
    pause
)
