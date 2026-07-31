"""Vzorce v testu — strukturní pravidla a jejich výjimky.

Data generuje `scripts/gen_patterns.py`. Aplikace je jen čte: režim „Vzorce"
z nich staví přehled pravidel a trénink na otázky, kde pravidlo NEPLATÍ.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PATH = ROOT / "data" / "patterns.json"


@lru_cache(maxsize=1)
def _data() -> dict:
    if not PATH.exists():
        return {}
    try:
        return json.loads(PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def rules() -> list[dict]:
    """Pravidla seřazená podle toho, kolik otázek pokryjí."""
    return sorted(_data().get("pravidla", []), key=lambda p: -p.get("pouzito", 0))


def rule(rule_id: str) -> dict | None:
    return next((p for p in rules() if p.get("id") == rule_id), None)


def not_working() -> list[dict]:
    """Pravidla, která se změřila a neplatí — ať se jimi nikdo nezdržuje."""
    return _data().get("nefunguje", [])


def exception_numbers(rule_id: str | None = None) -> set[int]:
    """Čísla otázek, kde pravidlo neplatí. Bez `rule_id` napříč všemi."""
    if rule_id:
        r = rule(rule_id)
        return {int(n) for n in (r or {}).get("vyjimky", [])}
    return {int(n) for p in rules() for n in p.get("vyjimky", [])}


def count() -> int:
    return len(rules())
