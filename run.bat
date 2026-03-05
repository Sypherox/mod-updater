@echo off
title Mod Updater - sypherox.dev

:: Python check
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found or is not added to PATH!
    echo Please install Python from https://www.python.org/downloads/
    echo and make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Auto-install requirements
echo [*] Installing/updating dependencies...
python -m pip install -q requests colorama
if errorlevel 1 (
    echo [ERROR] pip failed to install the required dependencies.
    pause
    exit /b 1
)

echo [*] Starting Mod Updater...
echo.
python mod_updater.py
if errorlevel 1 (
    echo.
    echo [ERROR] The script exited with an error.
    pause
)
