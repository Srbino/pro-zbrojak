"""Centrální cesty aplikace.

Runtime data (SQLite DB `stats.db`, vygenerované exporty) lze při nasazení
do kontejneru přesunout na persistentní volume přes proměnnou prostředí
``PRO_ZBROJAK_STATE_DIR`` — např. ``/state`` na Coolify. Lokální chování
(dvojklik na start.command) zůstává beze změny: když proměnná není nastavená,
STATE_DIR = kořen repa a data se ukládají do ``data/`` a ``exports/`` jako dřív.

Bundlovaný obsah (``data/questions.json`` + ``images/``) se čte VŽDY z kořene
repa (viz ``src/db/questions.py``), takže případný volume nad STATE_DIR nikdy
nepřekryje otázky.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Kam se ukládají uživatelská data. Lokálně = kořen repa; v kontejneru
# nastav PRO_ZBROJAK_STATE_DIR=/state a namontuj tam persistentní volume.
STATE_DIR = Path(os.environ.get("PRO_ZBROJAK_STATE_DIR", ROOT)).resolve()

DATA_DIR = STATE_DIR / "data"
DB_PATH = DATA_DIR / "stats.db"
EXPORT_DIR = STATE_DIR / "exports"
