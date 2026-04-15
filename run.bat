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

if not exist "data\questions.json" (
  dir MV-Soubor_testovych_otazek_*.pdf >nul 2>&1
  if errorlevel 1 (
    echo CHYBA: Chybi oficialni PDF MV CR. Viz README.
    exit /b 1
  )
  echo Parsuji PDF...
  .venv\Scripts\python parse_pdf.py
)

echo Spoustim aplikaci na http://127.0.0.1:8080
.venv\Scripts\python app.py
