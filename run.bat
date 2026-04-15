@echo off
REM Spousteci skript pro Windows (alternative k `make run`).
cd /d "%~dp0"

if not exist ".venv" (
  echo Vytvarim virtualni prostredi...
  python -m venv .venv
)

echo Instaluji zavislosti...
.venv\Scripts\pip install --quiet --upgrade pip
.venv\Scripts\pip install --quiet -e .

echo Spoustim aplikaci na http://127.0.0.1:8080
.venv\Scripts\python app.py
