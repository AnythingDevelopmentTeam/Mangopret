@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set VERSION=%1
if "%VERSION%"=="" set VERSION=v2.2.0
set DIST=mangopret-%VERSION%-win64

echo === Building Mangopret %VERSION% for Windows ===
echo.

if not exist python\python.exe (
    echo [1/5] Downloading portable Python...
    if not exist pip\get-pip.py (
        echo ERROR: pip\get-pip.py not found. Run bootstrap first.
        exit /b 1
    )
    echo   Manual step needed: download cpython-3.11.11 from
    echo   https://github.com/niess/python-build-standalone/releases/tag/20250312
    echo   Extract to .\python\ so that python\python.exe exists.
    exit /b 1
)

echo [2/5] Ensuring PyQt6...
python\python.exe -m pip install PyQt6>=6.5 --no-warn-script-location

echo [3/5] Creating distribution directory...
if exist "%DIST%" rmdir /s /q "%DIST%"
mkdir "%DIST%"
xcopy /E /I /Q python "%DIST%\python\" >nul
xcopy /E /I /Q gui "%DIST%\gui\" >nul
xcopy /E /I /Q lists "%DIST%\lists\" >nul
xcopy /E /I /Q bin "%DIST%\bin\" >nul
xcopy /E /I /Q pip "%DIST%\pip\" >nul
copy run.bat "%DIST%\" >nul
copy run_gui.bat "%DIST%\" >nul
copy README.md "%DIST%\" >nul
copy README.en.md "%DIST%\" >nul
copy LICENSE.txt "%DIST%\" >nul 2>nul

echo [4/5] Creating ZIP archive...
powershell -NoProfile -Command "Compress-Archive -Path '%DIST%\*' -DestinationPath '%DIST%.zip' -Force"
echo   Created: %DIST%.zip

if exist "packaging\windows\mangopret-installer.nsi" (
    echo [5/5] Building NSIS installer...
    if exist "%PROGRAMFILES(x86)%\NSIS\makensis.exe" (
        "%PROGRAMFILES(x86)%\NSIS\makensis.exe" "-DVERSION=%VERSION%" "packaging\windows\mangopret-installer.nsi"
        if exist "mangopret-%VERSION%-setup.exe" (
            move /Y "mangopret-%VERSION%-setup.exe" "%DIST%-setup.exe" >nul
            echo   Created: %DIST%-setup.exe
        )
    ) else (
        echo   NSIS not found at %%PROGRAMFILES(x86)%%\NSIS\makensis.exe. Skipping installer.
    )
)

echo.
echo === Done! Artifacts in current directory: ===
dir /B mangopret-%VERSION%-win64.* 2>nul
echo.
echo To create a GitHub release, run:
echo   gh release create %VERSION^% mangopret-%VERSION%-win64.zip mangopret-%VERSION%-win64-setup.exe --generate-notes
