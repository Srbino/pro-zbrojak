"""Strukturální integrita katalogu otázek (nevyžaduje PDF — běží i v CI).

Chrání před tichým poškozením dat: chybějící/duplicitní otázky, prázdné možnosti,
neplatná správná odpověď, rozbité odkazy na obrázky, neznámé sekce.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))

VALID_SECTIONS = {
    "pravo", "provadeci_predpisy", "jine_predpisy",
    "nauka_o_zbranich", "zdravotni_minimum",
}

# Známé kazy PŘÍMO v oficiálním PDF MV ČR (ověřeno vizuálně) — nejsou to naše chyby,
# katalog je věrně reprodukuje. Testy je proto tolerují, ale hlídají, že nepřibudou další.
SOURCE_DUPLICATE_QUESTIONS = [523, 529, 587, 590]   # dvě dvojice obsahově identických otázek
SOURCE_IDENTICAL_OPTIONS = {211}                     # v PDF má Q211 shodné znění B a C


def test_exactly_837_questions():
    assert len(QUESTIONS) == 837


def test_pdf_numbers_unique_and_contiguous():
    nums = sorted(q["pdf_number"] for q in QUESTIONS)
    assert len(nums) == len(set(nums)), "duplicitní pdf_number"
    assert nums[0] == 1
    assert nums == list(range(nums[0], nums[-1] + 1)), "chybí/přebývá číslo otázky (nesouvislé)"


def test_ids_collide_only_for_identical_content():
    """id = content-hash: sdílené id smí mít jen otázky s DOSLOVA stejným obsahem.

    Katalog MV ČR obsahuje 2 dvojice identických duplicitních otázek (523≡529,
    587≡590) — sdílené id je pro ně korektní. Kolize mezi RŮZNÝM obsahem = chyba.
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for q in QUESTIONS:
        groups[q["id"]].append(q)
    for qid, grp in groups.items():
        if len(grp) > 1:
            ref = (grp[0]["question"], grp[0]["options"])
            for g in grp[1:]:
                assert (g["question"], g["options"]) == ref, \
                    f"id {qid[:10]}… sdílí RŮZNÉ otázky {[x['pdf_number'] for x in grp]}"
    dup_nums = sorted(x["pdf_number"] for g in groups.values() if len(g) > 1 for x in g)
    assert dup_nums == SOURCE_DUPLICATE_QUESTIONS, f"neočekávané duplikáty: {dup_nums}"


def test_every_question_has_three_nonempty_options():
    bad = []
    for q in QUESTIONS:
        opts = q.get("options") or {}
        if set(opts.keys()) != {"A", "B", "C"}:
            bad.append((q["pdf_number"], "chybí varianta"))
            continue
        for k in "ABC":
            if not (opts[k] or "").strip():
                bad.append((q["pdf_number"], f"prázdná {k}"))
    assert not bad, f"Problémové možnosti: {bad[:20]}"


def test_options_distinct_except_known_source_quirks():
    """Možnosti v otázce mají být různé — kromě známého kazu PDF (Q211: B≡C)."""
    dupes = set()
    for q in QUESTIONS:
        vals = [(q["options"][k] or "").strip() for k in "ABC"]
        if len(set(vals)) != 3:
            dupes.add(q["pdf_number"])
    new = dupes - SOURCE_IDENTICAL_OPTIONS
    assert not new, f"Nové otázky s duplicitními možnostmi (mimo kazy PDF): {sorted(new)}"


def test_correct_is_valid_and_points_to_real_option():
    bad = []
    for q in QUESTIONS:
        c = q.get("correct")
        if c not in {"A", "B", "C"}:
            bad.append((q["pdf_number"], f"correct={c!r}"))
        elif not (q["options"].get(c) or "").strip():
            bad.append((q["pdf_number"], f"correct {c} ukazuje na prázdnou možnost"))
    assert not bad, f"Neplatná správná odpověď: {bad[:20]}"


def test_question_text_nonempty():
    bad = [q["pdf_number"] for q in QUESTIONS if not (q.get("question") or "").strip()]
    assert not bad, f"Prázdný text otázky: {bad}"


def test_section_valid():
    bad = [(q["pdf_number"], q.get("section")) for q in QUESTIONS
           if q.get("section") not in VALID_SECTIONS]
    assert not bad, f"Neznámá sekce: {bad[:20]}"


def test_image_files_exist():
    missing = []
    for q in QUESTIONS:
        img = q.get("image")
        if img and not (ROOT / img).exists():
            missing.append((q["pdf_number"], img))
    assert not missing, f"Chybějící obrázky: {missing[:20]}"


def test_answer_letter_distribution_reasonable():
    """Sanity: žádné písmeno nesmí dominovat (obrana proti systematickému default bugu)."""
    from collections import Counter
    c = Counter(q["correct"] for q in QUESTIONS)
    total = sum(c.values())
    for letter in "ABC":
        share = c[letter] / total
        assert 0.20 < share < 0.50, f"Podezřelé rozložení {letter}: {share:.0%}"
