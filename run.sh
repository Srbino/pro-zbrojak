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

echo "→ Spouštím aplikaci na http://127.0.0.1:8080"
.venv/bin/python app.py
