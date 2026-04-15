"""Invariantní testy parseru — drží pro KAŽDOU otázku.

Pokud jakýkoliv test selže, parser produkuje vadná data a aplikace nesmí jít do produkce.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = ROOT / "data" / "questions.json"
UNPARSED_PATH = ROOT / "data" / "unparsed.json"
IMAGES_DIR = ROOT / "images"


@pytest.fixture(scope="module")
def questions() -> list[dict]:
    assert QUESTIONS_PATH.exists(), f"Spusť `python parse_pdf.py` nejdřív. Chybí {QUESTIONS_PATH}"
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def unparsed() -> list[dict]:
    if not UNPARSED_PATH.exists():
        return []
    return json.loads(UNPARSED_PATH.read_text(encoding="utf-8"))


# ---------- Existence & shape ----------

def test_pdf_was_parsed(questions):
    assert len(questions) > 0, "Žádné otázky"


def test_no_unparsed(unparsed):
    assert unparsed == [], f"Parser nedořešil {len(unparsed)} otázek: {[u['pdf_number'] for u in unparsed]}"


def test_question_count_in_expected_range(questions):
    """Oficiální PDF MV ČR z 12/2025 má řádově 800+ otázek."""
    n = len(questions)
    assert 700 <= n <= 1000, f"Podezřelý počet otázek: {n}"


# ---------- Per-question invariants ----------

def test_every_question_has_required_fields(questions):
    required = {"id", "pdf_number", "question", "options", "correct", "source_page", "source_pdf"}
    for q in questions:
        missing = required - q.keys()
        assert not missing, f"Q{q.get('pdf_number')}: chybí pole {missing}"


def test_every_question_has_three_nonempty_options(questions):
    for q in questions:
        opts = q["options"]
        assert set(opts.keys()) == {"A", "B", "C"}, f"Q{q['pdf_number']}: nestandardni klice: {set(opts.keys())}"
        for k in "ABC":
            assert opts[k].strip(), f"Q{q['pdf_number']}: prazdna varianta {k}"
            # Min 1 char — otazky o cislech na obrazku maji odpovedi typu '1', '2', '3'
            assert len(opts[k]) >= 1


def test_correct_is_valid(questions):
    for q in questions:
        assert q["correct"] in ("A", "B", "C"), f"Q{q['pdf_number']}: invalid correct={q['correct']}"


def test_options_are_distinct(questions):
    for q in questions:
        a, b, c = q["options"]["A"], q["options"]["B"], q["options"]["C"]
        # In rare cases two options might overlap legitimately (e.g. "Ano." vs "Ne."),
        # but never all three identical.
        assert not (a == b == c), f"Q{q['pdf_number']}: všechny tři varianty identické"


def test_question_text_not_empty_or_marker(questions):
    """Otázka by neměla být jen číslo nebo varianta odpovědi."""
    for q in questions:
        text = q["question"].strip()
        assert text, f"Q{q['pdf_number']}: prázdná otázka"
        assert not text.startswith(("A)", "B)", "C)", "a)", "b)", "c)")), \
            f"Q{q['pdf_number']}: text začíná variantou — chyba segmentace: {text[:60]}"


def test_no_residual_glyph_garbage(questions):
    """Po normalizaci nesmí žádná otázka obsahovat broken glyphy."""
    bad_chars = ["\ufffd", "\u019f", "\u01a1", "\u014c", "\ufb01", "\ufb00", "\ufb02"]
    for q in questions:
        blob = q["question"] + " ".join(q["options"].values())
        for ch in bad_chars:
            assert ch not in blob, f"Q{q['pdf_number']}: obsahuje broken glyph {ch!r} ({hex(ord(ch))})"


# ---------- ID uniqueness & stability ----------

def test_ids_are_mostly_unique(questions):
    """V PDF jsou bohuzel skutecne duplicitni otazky (Q523=Q529, Q587=Q590).
    Tolerance: max 5 hash-kolizi celkem.
    """
    ids = [q["id"] for q in questions]
    dups = [iid for iid, n in Counter(ids).items() if n > 1]
    # Each duplicated hash counts as 1 collision, even if it appears 2 or 3 times
    assert len(dups) <= 5, f"Prilis mnoho hash-kolizi ({len(dups)}): {dups[:10]}"


def test_known_pdf_duplicates(questions):
    """Q523/Q529 a Q587/Q590 jsou znamy duplikat v PDF MV CR."""
    by_num = {q["pdf_number"]: q for q in questions}
    if 523 in by_num and 529 in by_num:
        assert by_num[523]["id"] == by_num[529]["id"], "Q523 a Q529 by mely mit shodny hash (jsou identicke)"
    if 587 in by_num and 590 in by_num:
        assert by_num[587]["id"] == by_num[590]["id"], "Q587 a Q590 by mely mit shodny hash"


def test_pdf_numbers_unique(questions):
    nums = [q["pdf_number"] for q in questions]
    dups = [n for n, k in Counter(nums).items() if k > 1]
    assert not dups, f"Duplicitní pdf_number: {dups[:5]}"


def test_id_is_sha1_hex(questions):
    import re
    pat = re.compile(r"^[0-9a-f]{40}$")
    for q in questions:
        assert pat.match(q["id"]), f"Q{q['pdf_number']}: invalid hash {q['id']!r}"


# ---------- Section assignment ----------

def test_all_questions_have_section(questions):
    """Sekce by měla být přiřazena pro každou otázku (přes mapping podle stránek)."""
    valid = {"pravo", "provadeci_predpisy", "jine_predpisy", "nauka_o_zbranich", "zdravotni_minimum"}
    for q in questions:
        sec = q.get("section")
        assert sec in valid, f"Q{q['pdf_number']}: invalid section {sec!r}"


def test_section_distribution_reasonable(questions):
    """Žádná z hlavních sekcí nesmí být prázdná."""
    by_sec = Counter(q["section"] for q in questions)
    assert by_sec["pravo"] >= 100, f"Sekce právo má jen {by_sec['pravo']} otázek"
    assert by_sec["nauka_o_zbranich"] >= 50, f"Nauka o zbraních má jen {by_sec['nauka_o_zbranich']}"
    assert by_sec["zdravotni_minimum"] >= 20, f"Zdravotní minimum má jen {by_sec['zdravotni_minimum']}"


# ---------- Correct answer distribution ----------

def test_correct_answer_distribution_balanced(questions):
    """Distribuce A/B/C by měla být zhruba uniformní (každá ~ 33 %, tolerance ±15 %).

    Pokud parser systematicky misdetekuje, distribuce bude vysoce nevyvážená.
    """
    n = len(questions)
    by = Counter(q["correct"] for q in questions)
    for letter in "ABC":
        share = by[letter] / n
        assert 0.18 <= share <= 0.48, (
            f"Podíl správné={letter}: {share:.2%} ({by[letter]}/{n}) — "
            "podezřelá distribuce, parser pravděpodobně misdetekuje"
        )


# ---------- Images ----------

def test_image_files_exist(questions):
    for q in questions:
        if q.get("image"):
            p = ROOT / q["image"]
            assert p.exists(), f"Q{q['pdf_number']}: chybí image soubor {p}"
            assert p.stat().st_size > 1000, f"Q{q['pdf_number']}: image je prázdný/příliš malý"


def test_image_questions_in_expected_range(questions):
    """Otázky s obrázkem jsou typicky v sekci nauka_o_zbranich (poznávání zbraní)."""
    img_qs = [q for q in questions if q.get("image")]
    assert len(img_qs) >= 30, f"Příliš málo otázek s obrázkem: {len(img_qs)}"
    # All image questions should be in 'nauka_o_zbranich' or related
    bad = [q for q in img_qs if q["section"] not in ("nauka_o_zbranich",)]
    # Allow some slack — there might be 1-2 images in other sections
    assert len(bad) < 5, f"Obrázky v neočekávaných sekcích: {[(q['pdf_number'], q['section']) for q in bad]}"
