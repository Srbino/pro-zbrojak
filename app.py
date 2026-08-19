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

from src.version import VERSION as APP_VERSION  # noqa: E402


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
DEV_SECRET = "pro-zbrojak-local-dev-secret"
STORAGE_SECRET = os.environ.get("STORAGE_SECRET", DEV_SECRET)

# Zástupné hodnoty z šablon. Kontrolovat jen DEV_SECRET nestačilo — kdo
# nasadil compose a proměnnou v Coolify nevyplnil, dostal veřejně známé
# „change-me-in-coolify" a pojistka ho pustila dál.
_SLABA_TAJEMSTVI = {
    DEV_SECRET, "change-me", "change-me-in-coolify", "changeme", "secret",
}
_MIN_DELKA = 16

# Známé tajemství + poslech mimo localhost = kdokoli si může podepsat vlastní
# session cookie a vydávat se za jiného uživatele. Radši nenastartovat.
_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
_slabe = STORAGE_SECRET in _SLABA_TAJEMSTVI or len(STORAGE_SECRET) < _MIN_DELKA
if _slabe and HOST not in _LOCAL_HOSTS:
    duvod = ("je zástupná hodnota ze šablony"
             if STORAGE_SECRET in _SLABA_TAJEMSTVI
             else f"má jen {len(STORAGE_SECRET)} znaků (potřeba aspoň {_MIN_DELKA})")
    print(
        f"CHYBA: aplikace poslouchá na {HOST} a STORAGE_SECRET {duvod}.\n"
        "S uhodnutelným tajemstvím si kdokoli podepíše cizí session.\n"
        "Nastav vlastní, například:\n"
        '    STORAGE_SECRET="$(python3 -c \'import secrets;print(secrets.token_urlsafe(32))\')"\n'
        "Viz README, sekce Nasazení na server.",
        file=sys.stderr,
    )
    sys.exit(1)

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


def _diagnostika() -> dict:
    """Co má provoz vědět, aby se nemusel hádat, co je vlastně nasazené.

    Vzniklo po hledání „rozbitých obrázků", které se nakonec ukázalo jako
    stará otevřená záložka mluvící se starým NiceGUI na `/socket.io/`.
    Bez těchhle údajů se to nedalo poznat jinak než dohadem.
    """
    import nicegui

    def spocitej(cesta: Path, vzor: str = "*") -> int:
        return len(list(cesta.glob(vzor))) if cesta.is_dir() else 0

    try:
        import json
        otazek = len(json.loads(QUESTIONS_JSON.read_text(encoding="utf-8")))
    except Exception:
        otazek = -1

    return {
        "status": "ok",
        "verze_aplikace": APP_VERSION,
        "nicegui": nicegui.__version__,
        # Klient starší verze si žádá /socket.io/ a dostane 404 — tohle je
        # cesta, na které socket opravdu je.
        "socket_io": "/_nicegui_ws/socket.io/",
        "otazek": otazek,
        "obrazku": spocitej(ROOT / "images", "*.png"),
        "odkazu_na_zakon": spocitej(ROOT / "data", "law_refs.json"),
        "host": HOST,
        "port": PORT,
        "state_dir": os.environ.get("PRO_ZBROJAK_STATE_DIR", str(ROOT)),
        "vlastni_storage_secret": STORAGE_SECRET != DEV_SECRET,
        "adminu": len([e for e in os.environ.get("PRO_ZBROJAK_ADMINS", "").split(",") if e.strip()]),
    }


# Health-check endpoint pro Coolify / reverse proxy (Traefik).
# Vrací i diagnostiku — `curl https://…/healthz` řekne, co přesně běží.
@app.get("/healthz")
def _healthz():
    return _diagnostika()


# Registrace vsech stranek (import ma side effect @ui.page)
from src.ui import pages  # noqa: F401, E402

if __name__ in {"__main__", "__mp_main__"}:
    # Rozpis do logu kontejneru — první, co se hledá, když něco nefunguje.
    _d = _diagnostika()
    print("Pro Zbroják — start", flush=True)
    for klic in ("verze_aplikace", "nicegui", "socket_io", "otazek", "obrazku",
                 "host", "port", "state_dir", "vlastni_storage_secret", "adminu"):
        print(f"   {klic:24} {_d[klic]}", flush=True)
    if not _d["vlastni_storage_secret"]:
        print("   POZOR: běží s vývojovým STORAGE_SECRET", flush=True)
    if _d["obrazku"] == 0:
        print("   POZOR: v images/ nejsou žádné obrázky", flush=True)

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
