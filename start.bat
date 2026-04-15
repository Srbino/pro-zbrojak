@echo off
REM Pro Zbrojak — dvojklikovy launcher pro Windows.
REM V Exploreru dvojklik -> otevre cmd a spusti aplikaci.

cd /d "%~dp0"
color 0A
cls

echo ========================================
echo   Pro Zbrojak - trenazer ZOZ
echo ========================================
echo.

REM Python check
where python >nul 2>&1
if errorlevel 1 (
    color 0C
    echo CHYBA: Nemas nainstalovany Python.
    echo Stahni z https://www.python.org/downloads/ (verze 3.11+^)
    echo Pri instalaci zaskrtni "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM Venv
if not exist ".venv" (
    echo Prvni spusteni - instaluji zavislosti ^(~ 1-2 min^)...
    python -m venv .venv
    .venv\Scripts\pip install --quiet --upgrade pip
    .venv\Scripts\pip install --quiet -e .
    if errorlevel 1 (
        color 0C
        echo Chyba pri instalaci. Zkus rucne: .venv\Scripts\pip install -e .
        pause
        exit /b 1
    )
    echo Nainstalovano.
) else (
    echo Virtualni prostredi OK.
)

REM Content check
if not exist "data\questions.json" (
    color 0C
    echo CHYBA: Chybi data\questions.json.
    echo Zkontroluj ze je klon repa kompletni.
    pause
    exit /b 1
)

echo.
echo Spoustim aplikaci - prohlizec se otevre automaticky
echo URL: http://127.0.0.1:8080
echo.
echo Pro ukonceni stiskni Ctrl+C.
echo.

.venv\Scripts\python app.py
