"""Pravidla zkoušky odborné způsobilosti.

Úspěšnost podle NV č. 238/2025 Sb.: 26 správných z 30 pro standardní zbrojní
oprávnění, 28 z 30 pro rozšířené.
"""
from __future__ import annotations

import math

OFFICIAL_TOTAL = 30
OFFICIAL_THRESHOLD: dict[str, int] = {"standard": 26, "extended": 28}


def threshold_for(level: str, total: int) -> int:
    """Kolik správných odpovědí je potřeba při daném počtu otázek.

    Simulace dovolí 5 až 100 otázek, takže se hranice musí přepočítat —
    jinak u šestiotázkového kola vyjde „chybělo 24".
    """
    base = OFFICIAL_THRESHOLD.get(level, OFFICIAL_THRESHOLD["standard"])
    if total <= 0:
        return 0
    if total == OFFICIAL_TOTAL:
        return base
    return min(total, math.ceil(total * base / OFFICIAL_TOTAL))


def passed(level: str, score: int, total: int) -> bool:
    return score >= threshold_for(level, total)
