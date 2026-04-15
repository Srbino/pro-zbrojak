#!/usr/bin/env bash
# Pro Zbroják — dvojklikový launcher pro macOS.
# Ulož v kořeni repa; v Finderu dvojklik → otevře Terminál a spustí aplikaci.
# Před prvním použitím: v Terminálu spusť `chmod +x start.command` (nebo `make install`).

set -e
cd "$(dirname "$0")"

# Barvy pro Terminál
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

clear
printf "${BLUE}========================================${NC}\n"
printf "${BLUE}  Pro Zbroják — trenažér ZOZ${NC}\n"
printf "${BLUE}========================================${NC}\n\n"

# --- 1. Python check ---
if ! command -v python3 &> /dev/null; then
    printf "${RED}CHYBA: Nemáš nainstalovaný Python 3.${NC}\n\n"
    printf "Nainstaluj z https://www.python.org/downloads/ (verze 3.11 nebo novější).\n\n"
    read -p "Stiskni Enter pro zavření..."
    exit 1
fi

PY_VER_NUM=$(python3 -c 'import sys; print(sys.version_info[0]*100 + sys.version_info[1])')
if [ "$PY_VER_NUM" -lt 311 ]; then
    printf "${RED}CHYBA: Máš $(python3 --version), potřebuješ Python 3.11 nebo novější.${NC}\n\n"
    printf "Stáhni novou verzi z https://www.python.org/downloads/\n\n"
    read -p "Stiskni Enter pro zavření..."
    exit 1
fi

printf "${GREEN}✓${NC} Python $(python3 --version | cut -d' ' -f2)\n"

# --- 2. Virtuální prostředí ---
if [ ! -d ".venv" ]; then
    printf "${BLUE}→ První spuštění — instaluji závislosti (trvá ~ 1–2 min)…${NC}\n\n"
    python3 -m venv .venv
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet -e . || {
        printf "${RED}Chyba při instalaci. Zkus ručně: ${NC}\n"
        printf "   ${BLUE}.venv/bin/pip install -e .${NC}\n\n"
        read -p "Stiskni Enter pro zavření..."
        exit 1
    }
    printf "${GREEN}✓${NC} Nainstalováno\n"
else
    printf "${GREEN}✓${NC} Virtuální prostředí OK\n"
fi

# --- 3. Kontrola obsahu (mělo by být v repu) ---
if [ ! -f "data/questions.json" ]; then
    printf "${RED}CHYBA: Chybí data/questions.json.${NC}\n"
    printf "Zkontroluj, že je klon repa kompletní.\n\n"
    read -p "Stiskni Enter pro zavření..."
    exit 1
fi

printf "${GREEN}✓${NC} Obsah OK (837 otázek)\n\n"

# --- 4. Spuštění ---
printf "${BLUE}→ Spouštím aplikaci…${NC}\n"
printf "${BLUE}→ Prohlížeč se otevře automaticky na ${GREEN}http://127.0.0.1:8080${NC}\n\n"
printf "${BLUE}Pro ukončení stiskni Ctrl+C a zavři okno.${NC}\n\n"

.venv/bin/python app.py
