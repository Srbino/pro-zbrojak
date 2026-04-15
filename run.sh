#!/usr/bin/env bash
# Spousteci skript pro macOS / Linux (alternative k `make run`).
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "→ Vytvářím virtuální prostředí…"
  python3 -m venv .venv
fi

echo "→ Instaluji závislosti…"
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e .

if [ ! -f "data/questions.json" ]; then
  PDF=$(ls MV-Soubor_testovych_otazek_*.pdf 2>/dev/null | head -1)
  if [ -z "$PDF" ]; then
    echo "CHYBA: Chybí oficiální PDF MV ČR. Viz README, sekce „Stažení PDF"."
    exit 1
  fi
  echo "→ Parsuji PDF (jednorázově)…"
  .venv/bin/python parse_pdf.py
fi

echo "→ Spouštím aplikaci na http://127.0.0.1:8080"
.venv/bin/python app.py
