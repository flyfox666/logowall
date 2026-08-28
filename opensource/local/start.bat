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

REM Auto-release the configured port if it is already in use
echo Checking port %PORT%...
set "_KILLED="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%PORT% "') do (
    echo   Port %PORT% is held by PID %%p, terminating...
    taskkill /F /PID %%p >nul 2>&1
    if not errorlevel 1 set "_KILLED=1"
)
if defined _KILLED (
    timeout /t 1 /nobreak >nul
    echo   Port %PORT% released.
) else (
    echo   Port %PORT% is free.
)

echo.
echo ========================================================
echo   Starting on port %PORT%... (addresses will show below)
echo   Config file: config.env (PORT / ADMIN_TOKEN)
echo ========================================================
echo.

python server\app.py
pause
