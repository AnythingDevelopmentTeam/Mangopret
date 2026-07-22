@echo off
chcp 65001 > nul
cd /d "%~dp0gui"
python convert_strategies.py %*
echo.
pause
