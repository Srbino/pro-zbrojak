"""Prohazování možností A/B/C — a hlavně to, že se tím nesmí nic rozbít.

Nejcitlivější místo celé věci: uživatel klikne na „b)", ale do statistik, SRS
i vyhodnocení zkoušky musí jít písmeno z katalogu. Kdyby se tohle rozešlo,
aplikace by tiše počítala špatné výsledky a ověření proti PDF by to neodhalilo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ui.shuffle import (  # noqa: E402
    CANONICAL_KEYS,
    display_letter,
    option_order,
    to_canonical,
    to_shown,
)

QUESTIONS = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))


def test_order_is_a_permutation_of_all_options() -> None:
    """Nesmí se ztratit ani zdvojit možnost — u žádné z 837 otázek."""
    for q in QUESTIONS:
        order = option_order(q, user_email="kdokoli@example.com")
        assert sorted(order) == sorted(q["options"]), f"otázka #{q['pdf_number']}"


def test_order_is_stable_for_same_user_and_day() -> None:
    """Dvakrát vykreslená otázka musí mít stejné pořadí.

    Kdyby se losovalo při každém překreslení, možnosti by se přeskládaly
    člověku pod rukama uprostřed odpovídání.
    """
    q = QUESTIONS[0]
    first = option_order(q, user_email="a@b.cz", epoch="2026-07-29")
    for _ in range(20):
        assert option_order(q, user_email="a@b.cz", epoch="2026-07-29") == first


def test_order_differs_across_days_or_users() -> None:
    """Přes den se pořadí otočí — jinak by šlo naučit se polohu."""
    sample = QUESTIONS[:60]
    same_day_other_user = sum(
        option_order(q, user_email="a@b.cz", epoch="2026-07-29")
        != option_order(q, user_email="c@d.cz", epoch="2026-07-29")
        for q in sample
    )
    other_day = sum(
        option_order(q, user_email="a@b.cz", epoch="2026-07-29")
        != option_order(q, user_email="a@b.cz", epoch="2026-07-30")
        for q in sample
    )
    # Se třemi možnostmi je 1/6 shoda náhodou; na 60 otázkách musí většina lišit.
    assert same_day_other_user > len(sample) // 2
    assert other_day > len(sample) // 2


def test_roundtrip_shown_and_canonical_agree() -> None:
    """Klik na zobrazené písmeno → katalogové písmeno → a zpátky."""
    for q in QUESTIONS[:200]:
        order = option_order(q, user_email="tester@example.com")
        for position, canonical in enumerate(order):
            shown = display_letter(position)
            assert to_canonical(order, shown) == canonical
            assert to_shown(order, canonical) == shown


def test_displayed_text_belongs_to_canonical_answer() -> None:
    """Text u zobrazeného písmene musí patřit tomu, co se pak zapíše."""
    for q in QUESTIONS[:200]:
        order = option_order(q, user_email="tester@example.com")
        for position, canonical in enumerate(order):
            shown_text = q["options"][to_canonical(order, display_letter(position))]
            assert shown_text == q["options"][canonical]


def test_correct_answer_is_not_always_in_the_same_place() -> None:
    """Smysl celé věci: správná odpověď nesmí zůstat pod jedním písmenem."""
    positions = {k: 0 for k in CANONICAL_KEYS}
    for q in QUESTIONS:
        order = option_order(q, user_email="tester@example.com")
        positions[to_shown(order, q["correct"])] += 1
    total = sum(positions.values())
    for key, count in positions.items():
        share = count / total
        assert 0.2 < share < 0.47, f'správná odpověď je pod {key} v {share:.0%} případů'


def test_shuffle_can_be_switched_off() -> None:
    """Vypínač pro testy a ladění (PRO_ZBROJAK_SHUFFLE=0)."""
    import src.ui.shuffle as shuffle_module

    original = shuffle_module._ENABLED
    try:
        shuffle_module._ENABLED = False
        assert option_order(QUESTIONS[0], user_email="x@y.cz") == ["A", "B", "C"]
    finally:
        shuffle_module._ENABLED = original


def test_source_data_keeps_official_order() -> None:
    """Katalog se míchat NESMÍ — na jeho pořadí stojí ověření proti PDF i zákonu."""
    for q in QUESTIONS:
        assert list(q["options"].keys()) == [
            k for k in CANONICAL_KEYS if k in q["options"]
        ], f"otázka #{q['pdf_number']} má v datech přeházené možnosti"
