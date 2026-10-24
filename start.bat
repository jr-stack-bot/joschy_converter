@echo off
setlocal
cd /d "%~dp0"

set PY=
pyw --version >nul 2>&1 && set PY=pyw
if "%PY%"=="" (
    pythonw --version >nul 2>&1 && set PY=pythonw
)
if "%PY%"=="" (
    py --version >nul 2>&1 && set PY=py
)
if "%PY%"=="" (
    python --version >nul 2>&1 && set PY=python
)
if "%PY%"=="" (
    echo.
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte Python 3 von https://www.python.org/downloads/ installieren
    echo und beim Installieren "Add python.exe to PATH" anhaken.
    echo.
    pause
    exit /b 1
)

start "" %PY% kreis_konverter.py
