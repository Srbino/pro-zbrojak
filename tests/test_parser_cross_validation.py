"""Cross-validacni test: pro nahodne vybrane otazky znovu prectu PDF a porovnam,
zda parser-detekovana spravna odpoved skutecne sedi se sedym pozadim v PDF.

Toto je robustni test napric celym katalogem (ne jen rucne vybrane fixtury).
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pdfplumber
import pytest

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "MV-Soubor_testovych_otazek_pro_teoretickou_cast_ZOZ_a_komisionalni_zkousku_-_20251215.pdf"
QUESTIONS_PATH = ROOT / "data" / "questions.json"

GRAY_TARGET = 0.827
GRAY_TOL = 0.05
RE_OPTION = re.compile(r"^([ABCabc])\)\s+")
RE_QSTART = re.compile(r"^(\d{1,4})\.")


def _is_gray(rect: dict) -> bool:
    fill = rect.get("non_stroking_color")
    if isinstance(fill, (int, float)):
        return abs(float(fill) - GRAY_TARGET) <= GRAY_TOL
    if isinstance(fill, (list, tuple)) and len(fill) == 1:
        return abs(float(fill[0]) - GRAY_TARGET) <= GRAY_TOL
    return False


def _detect_correct_for_question(page, q_pdf_num: int) -> str | None:
    """Najde otazku N na strance a vrati pismeno (A/B/C) varianty, pod kterou je sede pozadi."""
    words = page.extract_words(use_text_flow=True)
    # Group by line
    lines: dict[float, list[dict]] = {}
    for w in words:
        key = round(w["top"])
        lines.setdefault(key, []).append(w)

    sorted_keys = sorted(lines)

    # Find start of this question and start of next-numbered question
    q_start_top = None
    next_q_top = None
    for key in sorted_keys:
        text = " ".join(w["text"] for w in sorted(lines[key], key=lambda x: x["x0"]))
        m = RE_QSTART.match(text)
        if not m:
            continue
        n = int(m.group(1))
        if n == q_pdf_num and q_start_top is None:
            q_start_top = key
        elif q_start_top is not None and n != q_pdf_num and key > q_start_top:
            next_q_top = key
            break

    if q_start_top is None:
        return None
    if next_q_top is None:
        next_q_top = max(sorted_keys) + 1000

    # Find option lines within this question's vertical range
    opt_tops: dict[str, tuple[float, float]] = {}
    for key in sorted_keys:
        if key < q_start_top or key >= next_q_top:
            continue
        first_word = sorted(lines[key], key=lambda x: x["x0"])[0]
        text = " ".join(w["text"] for w in sorted(lines[key], key=lambda x: x["x0"]))
        m = RE_OPTION.match(text)
        if m:
            letter = m.group(1).upper()
            top = min(w["top"] for w in lines[key])
            bottom = max(w["bottom"] for w in lines[key])
            opt_tops[letter] = (top, bottom)

    if not opt_tops or len(opt_tops) < 3:
        return None

    # Score gray rect overlap per option
    scores = {k: 0.0 for k in "ABC"}
    for r in page.rects:
        if not _is_gray(r):
            continue
        r_top, r_bot = r["top"], r["bottom"]
        for letter, (o_top, o_bot) in opt_tops.items():
            ov = max(0.0, min(r_bot, o_bot) - max(r_top, o_top))
            scores[letter] += ov

    if max(scores.values()) < 1.0:
        return None
    return max(scores.items(), key=lambda kv: kv[1])[0]


@pytest.fixture(scope="module")
def questions() -> list[dict]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pdf():
    p = pdfplumber.open(PDF_PATH)
    yield p
    p.close()


def test_random_sample_correct_answers_match_pdf(questions, pdf):
    """Pro 50 nahodne vybranych otazek znovu nacti PDF a porovnej spravnou odpoved.

    Pro otazky s obrazkem (typicky kratke "Vyberte spravnou odpoved:") se
    cross-check muze hodit jinak — tady jdeme po obecnych textovych otazkach.
    """
    rng = random.Random(20260415)  # deterministicke pro stabilni CI
    text_qs = [q for q in questions if not q.get("image")]
    sample = rng.sample(text_qs, k=50)

    mismatches = []
    for q in sample:
        page = pdf.pages[q["source_page"] - 1]
        detected = _detect_correct_for_question(page, q["pdf_number"])
        if detected is None:
            # Question may span multiple pages — skip if cross-validation can't determine
            continue
        if detected != q["correct"]:
            mismatches.append((q["pdf_number"], q["source_page"], q["correct"], detected))

    assert not mismatches, f"Cross-validace selhala u {len(mismatches)} otazek: {mismatches}"


def test_image_questions_have_short_question_text(questions):
    """Otazky s obrazkem maji typicky kratky text: 'Vyberte spravnou odpoved:' nebo podobne."""
    img_qs = [q for q in questions if q.get("image")]
    short_count = sum(1 for q in img_qs if len(q["question"]) < 80)
    assert short_count >= len(img_qs) * 0.5, "Vetsina otazek s obrazkem by mela mit kratky text otazky"
