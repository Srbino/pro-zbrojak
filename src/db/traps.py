"""Chytáky — otázky, kde je distraktor jen drobně upravená správná odpověď.

Data generuje `scripts/gen_traps.py` (viz tam, jak se poznají). Aplikace je jen
čte: režim „Chytáky" z nich staví balík na trénink a po odpovědi ukáže, co přesně
tam bylo nastražené.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TRAPS_PATH = ROOT / "data" / "traps.json"


@lru_cache(maxsize=1)
def _traps() -> dict[str, dict]:
    if not TRAPS_PATH.exists():
        return {}
    try:
        return json.loads(TRAPS_PATH.read_text(encoding="utf-8")).get("otazky", {})
    except (json.JSONDecodeError, OSError):
        return {}


def trap_for(pdf_number: int) -> dict | None:
    """Popis pastí u otázky: {'shoda', 'spravne', 'pasti': [...]} nebo None."""
    return _traps().get(str(pdf_number))


# Tři druhy pastí — skript je detekuje třemi různými signály a jsou to tři
# různé způsoby, jak se dá u zkoušky šlápnout vedle. Házet je na jednu hromadu
# 309 otázek zahazuje informaci, která z nich se člověk má učit jak.
KINDS: dict[str, tuple[str, str]] = {
    "odpoved": ("Rozdíl v odpovědi", "pasti"),
    "zadani":  ("Past v zadání", "zadani"),
    "dvojce":  ("Dvojče", "dvojnici"),
}


def trap_numbers(kind: str | None = None) -> set[int]:
    """Čísla otázek s pastí. `kind` je klíč z KINDS, None = všechny."""
    field = KINDS.get(kind, (None, None))[1] if kind else None
    return {
        int(n) for n, rec in _traps().items()
        if field is None or rec.get(field)
    }


def stem_markers(pdf_number: int) -> list[str]:
    """Slova v zadání, která obracejí smysl otázky („nepatří", „nejméně")."""
    rec = trap_for(pdf_number) or {}
    return [m["slovo"] for m in rec.get("zadani", []) if m.get("slovo")]


def twins(pdf_number: int) -> list[int]:
    """Otázky se skoro stejným zadáním, ale jinou správnou odpovědí."""
    rec = trap_for(pdf_number) or {}
    return [int(n) for n in rec.get("dvojnici", [])]


def count(kind: str | None = None) -> int:
    return len(trap_numbers(kind))
