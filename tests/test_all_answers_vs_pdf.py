"""Ověření SPRÁVNOSTI VŠECH odpovědí proti oficiálnímu PDF MV ČR.

Pro každou z 837 otázek nezávisle z PDF detekuje, pod kterou variantou (A/B/C)
je šedé pozadí = správná odpověď, a porovná s uloženou odpovědí v questions.json.
Zvládá i otázky přes zlom stránky (kombinuje source_page + následující).

PDF není v repu (licenční důvody), takže se test bez něj přeskočí. Maintainer,
který regeneruje data z nového PDF, ho spustí a MUSÍ projít s 0 nesrovnalostmi.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pdfplumber = pytest.importorskip("pdfplumber")

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "MV-Soubor_testovych_otazek_pro_teoretickou_cast_ZOZ_a_komisionalni_zkousku_-_20251215.pdf"
QUESTIONS_PATH = ROOT / "data" / "questions.json"

GRAY_TARGET = 0.827
GRAY_TOL = 0.05
RE_OPT = re.compile(r"^([ABCabc])\)\s+")
RE_Q = re.compile(r"^(\d{1,4})\.")


def _is_gray(rect: dict) -> bool:
    fill = rect.get("non_stroking_color")
    if isinstance(fill, (int, float)):
        return abs(float(fill) - GRAY_TARGET) <= GRAY_TOL
    if isinstance(fill, (list, tuple)) and len(fill) == 1:
        return abs(float(fill[0]) - GRAY_TARGET) <= GRAY_TOL
    return False


def _lines(page) -> dict[int, list]:
    d: dict[int, list] = {}
    for w in page.extract_words(use_text_flow=True):
        d.setdefault(round(w["top"]), []).append(w)
    return d


def _detect(pdf, qnum: int, page_idx: int) -> str | None:
    """Detekuje správnou odpověď; kombinuje source_page + následující (přes zlom)."""
    p1 = pdf.pages[page_idx]
    h1 = float(p1.height)
    opt: dict[str, tuple[float, float]] = {}
    grays: list[tuple[float, float]] = []

    l1 = _lines(p1)
    qtop = None
    for k in sorted(l1):
        txt = " ".join(w["text"] for w in sorted(l1[k], key=lambda x: x["x0"]))
        m = RE_Q.match(txt)
        if m and int(m.group(1)) == qnum:
            qtop = k
            break
    if qtop is None:
        return None
    for k in sorted(l1):
        if k < qtop:
            continue
        txt = " ".join(w["text"] for w in sorted(l1[k], key=lambda x: x["x0"]))
        m = RE_OPT.match(txt)
        if m and m.group(1).upper() not in opt:
            opt[m.group(1).upper()] = (min(w["top"] for w in l1[k]), max(w["bottom"] for w in l1[k]))
    for r in p1.rects:
        if _is_gray(r) and r["top"] >= qtop - 1:
            grays.append((r["top"], r["bottom"]))

    # pokračování na další straně
    if page_idx + 1 < len(pdf.pages):
        p2 = pdf.pages[page_idx + 1]
        l2 = _lines(p2)
        stop = None
        for k in sorted(l2):
            txt = " ".join(w["text"] for w in sorted(l2[k], key=lambda x: x["x0"]))
            if RE_Q.match(txt):
                stop = k
                break
        for k in sorted(l2):
            if stop is not None and k >= stop:
                break
            txt = " ".join(w["text"] for w in sorted(l2[k], key=lambda x: x["x0"]))
            m = RE_OPT.match(txt)
            if m and m.group(1).upper() not in opt:
                opt[m.group(1).upper()] = (
                    min(w["top"] for w in l2[k]) + h1, max(w["bottom"] for w in l2[k]) + h1
                )
        for r in p2.rects:
            if _is_gray(r) and (stop is None or r["top"] < stop):
                grays.append((r["top"] + h1, r["bottom"] + h1))

    if len(opt) < 3 or not grays:
        return None
    scores = {k: 0.0 for k in "ABC"}
    for gt, gb in grays:
        for L, (ot, ob) in opt.items():
            scores[L] += max(0.0, min(gb, ob) - max(gt, ot))
    if max(scores.values()) < 1.0:
        return None
    return max(scores.items(), key=lambda kv: kv[1])[0]


@pytest.fixture(scope="module")
def questions() -> list[dict]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pdf():
    if not PDF_PATH.exists():
        pytest.skip("Zdrojové PDF MV ČR v repu není (licenční důvody) — jen pro maintainery.")
    p = pdfplumber.open(PDF_PATH)
    yield p
    p.close()


def test_all_correct_answers_match_official_pdf(questions, pdf):
    """VŠECH 837 odpovědí musí sedět s oficiálním PDF (0 nesrovnalostí)."""
    mismatches = []
    undetected = []
    for q in questions:
        pi = q["source_page"] - 1
        if not (0 <= pi < len(pdf.pages)):
            undetected.append(q["pdf_number"])
            continue
        detected = _detect(pdf, q["pdf_number"], pi)
        if detected is None:
            undetected.append(q["pdf_number"])
            continue
        if detected != q["correct"]:
            mismatches.append((q["pdf_number"], q["source_page"], q["correct"], detected))

    assert not mismatches, (
        f"{len(mismatches)} odpovědí NESEDÍ s oficiálním PDF "
        f"(otazka, strana, nase, pdf): {mismatches}"
    )
    # Pokrytí: metoda musí ověřit drtivou většinu (jinak je detekce rozbitá).
    assert len(undetected) < 20, f"Příliš mnoho neověřených ({len(undetected)}): {undetected[:20]}"
