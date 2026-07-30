"""Odkazy z otázek do e-Sbírky MV ČR.

Znění zákona v repu nedržíme — u otázky si vedeme jen ustanovení, které ji
zakládá, a odkaz na jeho oficiální text. Data generuje `scripts/gen_law_links.py`
a jsou ověřená proti otevřeným datům e-Sbírky (viz tam).

Odkaz existuje jen u části otázek — u těch, kde se dalo strojově doložit, ze
kterého ustanovení odpověď plyne. Chybějící odkaz není chyba, jen se k té otázce
nepodařilo přiřadit ustanovení s dostatečnou jistotou.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LAW_REFS_PATH = ROOT / "data" / "law_refs.json"


@lru_cache(maxsize=1)
def _refs() -> dict[str, dict]:
    if not LAW_REFS_PATH.exists():
        return {}
    try:
        return json.loads(LAW_REFS_PATH.read_text(encoding="utf-8")).get("otazky", {})
    except (json.JSONDecodeError, OSError):
        return {}


def ref_for(pdf_number: int) -> dict | None:
    """Vrátí {'ref', 'url', 'quote'} pro otázku, nebo None."""
    return _refs().get(str(pdf_number))


def count() -> int:
    return len(_refs())
