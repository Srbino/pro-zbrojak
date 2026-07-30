"""Hranice úspěšnosti simulace zkoušky."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.learning.exam import (  # noqa: E402
    OFFICIAL_THRESHOLD,
    OFFICIAL_TOTAL,
    passed,
    threshold_for,
)


def test_official_thresholds_unchanged():
    """NV č. 238/2025 Sb. — 26 z 30 standard, 28 z 30 rozšířené."""
    assert threshold_for("standard", OFFICIAL_TOTAL) == 26
    assert threshold_for("extended", OFFICIAL_TOTAL) == 28
    assert OFFICIAL_THRESHOLD == {"standard": 26, "extended": 28}


def test_threshold_scales_with_question_count():
    """Kratší simulace nesmí chtít víc bodů, než kolik má otázek."""
    for level in ("standard", "extended"):
        for n in range(1, 101):
            need = threshold_for(level, n)
            assert 0 < need <= n, f"{level} {n} -> {need}"


def test_threshold_is_never_easier_than_official():
    """Zaokrouhluje se nahoru — kratší simulace nesmí být mírnější než zkouška.

    Odchylka směrem vzhůru je nejvýš jedna otázka: to je nutný důsledek toho,
    že počet správných odpovědí je celé číslo.
    """
    for level, base in OFFICIAL_THRESHOLD.items():
        ratio = base / OFFICIAL_TOTAL
        for n in range(5, 101):
            got = threshold_for(level, n) / n
            assert got >= ratio - 1e-9, f"{level} {n}: {got:.3f} < oficiálních {ratio:.3f}"
            assert got - ratio <= 1 / n + 1e-9, f"{level} {n}: přísnější o víc než 1 otázku"


def test_unknown_level_falls_back_to_standard():
    assert threshold_for("nesmysl", 30) == 26


def test_zero_questions_is_not_a_crash():
    assert threshold_for("standard", 0) == 0


def test_passed_matches_threshold():
    assert passed("standard", 26, 30)
    assert not passed("standard", 25, 30)
    assert passed("extended", 28, 30)
    assert not passed("extended", 27, 30)
    # Šest otázek: hranice 6, ne 26 — to byla ta chyba.
    assert threshold_for("standard", 6) == 6
    assert not passed("standard", 2, 6)
