@echo off
title Money Tracking App - Web Dashboard & Telegram Bot
cls
echo ========================================================
echo   MONEY TRACKING APP (WEB DASHBOARD + TELEGRAM + EXCEL)
echo ========================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python belum terinstall atau belum ditambahkan ke PATH.
    echo Silakan install Python 3.10+ terlebih dahulu.
    pause
    exit /b 1
)

:: Run application
echo Menjalankan aplikasi...
python main.py
pause
