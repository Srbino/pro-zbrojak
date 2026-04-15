#!/usr/bin/env python3
"""
ZP Trenažér — NiceGUI aplikace pro samostudium na zkoušku odborné způsobilosti.
Spuštění: python app.py  →  http://127.0.0.1:8080
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from nicegui import app, ui

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Bootstrap: parser PDF je-li potreba
QUESTIONS_JSON = ROOT / "data" / "questions.json"
if not QUESTIONS_JSON.exists():
    print("questions.json chybí, spouštím parser...")
    subprocess.run([sys.executable, str(ROOT / "parse_pdf.py")], check=True)

# Static files (obrazky extrahovane z PDF)
app.add_static_files("/images", str(ROOT / "images"))

# Registrace vsech stranek (import ma side effect @ui.page)
from src.ui import pages  # noqa: F401, E402


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="127.0.0.1",
        port=8080,
        title="ZP Trenažér",
        reload=False,
        show=True,
        favicon="🎯",
        dark=None,
    )
