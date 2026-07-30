"""Prohazování pořadí možností A/B/C.

PROČ
----
Když je správná odpověď pořád pod stejným písmenem, člověk se místo látky naučí
polohu. U ostré zkoušky mu to k ničemu není — otázky tam přijdou v jiném pořadí.

KDE SE TO DĚJE
--------------
Výhradně při vykreslování. `data/questions.json` si drží pořadí přesně tak, jak
je v oficiálním PDF MV ČR, a nikdy se nepřepisuje — na tom stojí ověření odpovědí
proti PDF (`tests/test_all_answers_vs_pdf.py`) i proti zákonu
(`scripts/validate_vs_zakon.py`). Míchá se až úplně nahoře, v UI, a zpět do
statistik se vždycky zapisuje původní (kanonické) písmeno.

STABILITA
---------
Pořadí je odvozené, ne náhodné: pro danou dvojici uživatel + otázka vyjde v rámci
dne vždycky stejné. Kdyby se losovalo při každém překreslení, mohly by se možnosti
přeskládat člověku pod rukama uprostřed odpovídání. Přes den se pořadí otočí, takže
při dalším setkání s otázkou je jiné.
"""
from __future__ import annotations

import os
import random
from datetime import date

CANONICAL_KEYS = ("A", "B", "C")

# Vypínač — testy a ladění chtějí předvídatelné pořadí.
_ENABLED = os.environ.get("PRO_ZBROJAK_SHUFFLE", "1").strip().lower() not in {
    "0", "false", "no", "off",
}


def is_enabled() -> bool:
    return _ENABLED


def option_order(
    question: dict,
    *,
    user_email: str = "",
    epoch: str | None = None,
) -> list[str]:
    """Vrátí kanonická písmena v pořadí, v jakém se mají zobrazit.

    Např. ``["C", "A", "B"]`` znamená: na prvním místě (jako „a)") je text
    původní možnosti C. Vždy obsahuje všechna písmena, která otázka má.
    """
    keys = [k for k in CANONICAL_KEYS if k in question.get("options", {})]
    if not _ENABLED or len(keys) < 2:
        return keys

    seed = f"{epoch or date.today().isoformat()}|{user_email}|{question.get('id', '')}"
    order = keys[:]
    random.Random(seed).shuffle(order)
    return order


def display_letter(position: int) -> str:
    """0 → „A", 1 → „B", 2 → „C" — písmeno, které uživatel na dané pozici vidí."""
    return CANONICAL_KEYS[position]


def to_canonical(order: list[str], shown: str) -> str:
    """Písmeno, na které uživatel klikl → původní písmeno z katalogu."""
    return order[CANONICAL_KEYS.index(shown)]


def to_shown(order: list[str], canonical: str) -> str:
    """Původní písmeno z katalogu → písmeno, pod kterým je zobrazené."""
    return CANONICAL_KEYS[order.index(canonical)]
