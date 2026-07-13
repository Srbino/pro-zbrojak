#!/usr/bin/env python3
"""
Pro Zbroják — český trenažér testových otázek pro zkoušku odborné způsobilosti
k vydání zbrojního průkazu (ZOZ). Podle zákona č. 90/2024 Sb. a NV č. 238/2025 Sb.

Spuštění: python app.py  →  http://127.0.0.1:8080
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from nicegui import app, ui

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


# Konfigurace přes prostředí — lokálně (dvojklik) fungují výchozí hodnoty,
# v kontejneru (Coolify/Docker) se přepíší přes env: HOST=0.0.0.0, SHOW=false.
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8080"))
SHOW = _env_bool("SHOW", default=True)

# Tajemství pro podpis session cookie (app.storage.user — drží přihlášení).
# V nasazení nastav přes env STORAGE_SECRET, ať sessions přežijí restart.
STORAGE_SECRET = os.environ.get("STORAGE_SECRET", "pro-zbrojak-local-dev-secret")

# Questions content is bundled in the repo (data/questions.json + images/).
# If missing, user has a broken clone — fail fast with clear message.
QUESTIONS_JSON = ROOT / "data" / "questions.json"
if not QUESTIONS_JSON.exists():
    print(
        f"CHYBA: Chybí {QUESTIONS_JSON}.\n"
        "Obsah aplikace má být součástí repa. Zkontroluj klon nebo spusť "
        "`make parse` (vyžaduje oficiální PDF MV ČR — jen pro maintainery).",
        file=sys.stderr,
    )
    sys.exit(1)

# Static files (obrazky extrahovane z PDF)
app.add_static_files("/images", str(ROOT / "images"))


# Health-check endpoint pro Coolify / reverse proxy (Traefik).
@app.get("/healthz")
def _healthz():
    return {"status": "ok"}


# Registrace vsech stranek (import ma side effect @ui.page)
from src.ui import pages  # noqa: F401, E402

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host=HOST,
        port=PORT,
        title="Pro Zbroják",
        reload=False,
        show=SHOW,
        favicon="🎯",
        dark=None,
        storage_secret=STORAGE_SECRET,
    )
