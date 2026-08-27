@echo off
chcp 65001 >nul
title Logo Wall Server
cd /d "%~dp0"

echo ========================================================
echo   Logo Wall - Local Server with Admin Panel
echo ========================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Create venv if missing, then always sync dependencies
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Syncing dependencies...
pip install -r server\requirements.txt

REM Load config.env (PORT / ADMIN_TOKEN) if present, fall back to defaults
if exist "config.env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("config.env") do set "%%a=%%b"
)
if not defined PORT set PORT=8080
if not defined ADMIN_TOKEN set ADMIN_TOKEN=admin123

echo.
echo ========================================================
echo   Starting on port %PORT%... (addresses will show below)
echo   Config file: config.env (PORT / ADMIN_TOKEN)
echo ========================================================
echo.

python server\app.py
pause
