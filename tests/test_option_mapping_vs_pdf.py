"""Sedí TEXT za písmenem? Mapování A/B/C → znění proti oficiálnímu PDF MV ČR.

Ostatní testy hlídají něco jiného:
  * `test_all_answers_vs_pdf` — že správné PÍSMENO odpovídá šedému zvýraznění,
  * strukturní testy — že možnosti nejsou prázdné a `correct` míří na existující.

Ani jeden ale neověřuje, že to, co máme uložené pod „A", je opravdu text,
který je v příručce za `a)`. Kdyby se možnosti při parsování prohodily,
klíč odpovědí by pořád seděl, jen by ukazoval na jiné znění — a to je přesně
ta chyba, která by se u zkoušky projevila nejhůř.

Tenhle test vytáhne z PDF text pod a)/b)/c) nezávisle a porovná znak po znaku.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

import pytest

pdfplumber = pytest.importorskip("pdfplumber")

ROOT = Path(__file__).resolve().parent.parent
PDF_NAME = "MV-Soubor_testovych_otazek_pro_teoretickou_cast_ZOZ_a_komisionalni_zkousku_-_20251215.pdf"
PDF_PATH = next((p for p in (ROOT / "docs" / PDF_NAME, ROOT / PDF_NAME) if p.exists()),
                ROOT / "docs" / PDF_NAME)
QUESTIONS_PATH = ROOT / "data" / "questions.json"

RE_OPT = re.compile(r"^([abc])\)\s*(.*)$", re.I)
RE_Q = re.compile(r"^(\d{1,4})\.\s*(.*)$")

# pdfplumber vrací za ligaturu „ti/tí" náhradní znak; patička stránky se
# v extrakci vloží doprostřed možnosti, která přetéká na další stranu.
LIGATURE = "�"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = s.replace(LIGATURE, "ti").replace("­", "").replace("‑", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def _lines(page) -> list[str]:
    buckets: dict[int, list] = {}
    for w in page.extract_words(use_text_flow=True):
        buckets.setdefault(round(w["top"] / 2), []).append(w)
    out = []
    for key in sorted(buckets):
        words = sorted(buckets[key], key=lambda x: x["x0"])
        out.append(" ".join(w["text"] for w in words))
    return out


def _options_from_pdf(pdf, qnum: int, page_idx: int) -> dict[str, str] | None:
    """Znění a)/b)/c) přímo z PDF. Bere i následující stranu kvůli zlomu."""
    lines = _lines(pdf.pages[page_idx])
    if page_idx + 1 < len(pdf.pages):
        lines += _lines(pdf.pages[page_idx + 1])

    start = None
    for i, line in enumerate(lines):
        m = RE_Q.match(line.strip())
        if m and int(m.group(1)) == qnum:
            start = i
            break
    if start is None:
        return None

    opts: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in lines[start + 1:]:
        text = line.strip()
        mq = RE_Q.match(text)
        if mq and int(mq.group(1)) != qnum and current:
            break
        mo = RE_OPT.match(text)
        if mo:
            if current:
                opts[current] = " ".join(buf)
            current, buf = mo.group(1).upper(), [mo.group(2)]
        elif current:
            if re.fullmatch(r"\d{1,3}", text):   # patička se stránkováním
                continue
            buf.append(text)
    if current:
        opts[current] = " ".join(buf)
    return opts


@pytest.fixture(scope="module")
def questions() -> list[dict]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pdf():
    if not PDF_PATH.exists():
        pytest.skip("Zdrojové PDF MV ČR v repu není (licenční důvody).")
    doc = pdfplumber.open(PDF_PATH)
    yield doc
    doc.close()


def test_kazda_moznost_sedi_na_sve_pismeno(questions, pdf):
    """Všech 2511 možností: text pod A/B/C se musí shodovat s PDF."""
    nesedi: list[tuple] = []
    nenalezeno: list[int] = []
    porovnano = 0

    for q in questions:
        z_pdf = _options_from_pdf(pdf, q["pdf_number"], q["source_page"] - 1)
        if not z_pdf:
            nenalezeno.append(q["pdf_number"])
            continue
        for key, ours in q["options"].items():
            theirs = z_pdf.get(key)
            if theirs is None:
                nesedi.append((q["pdf_number"], key, "v PDF chybí"))
                continue
            porovnano += 1
            a, b = _norm(ours), _norm(theirs)
            if a == b:
                continue
            ratio = difflib.SequenceMatcher(None, a, b).ratio()
            nesedi.append((q["pdf_number"], key, round(ratio, 3), a[:70], b[:70]))

    assert not nenalezeno, f"otázka se v PDF nenašla: {nenalezeno[:20]}"
    assert not nesedi, f"{len(nesedi)} možností nesedí: {nesedi[:10]}"
    assert porovnano == sum(len(q["options"]) for q in questions)


def test_spravna_odpoved_ukazuje_na_shodne_zneni(questions, pdf):
    """Text správné odpovědi musí sedět s tím, co je v PDF pod jejím písmenem.

    Kdyby se možnosti prohodily, klíč by pořád seděl — jen by ukazoval jinam.
    """
    spatne = []
    for q in questions:
        z_pdf = _options_from_pdf(pdf, q["pdf_number"], q["source_page"] - 1)
        if not z_pdf:
            continue
        letter = q["correct"]
        theirs = z_pdf.get(letter)
        if theirs is None or _norm(q["options"][letter]) != _norm(theirs):
            spatne.append((q["pdf_number"], letter))
    assert not spatne, f"správná odpověď míří na jiné znění: {spatne[:10]}"


def test_pocet_moznosti_sedi(questions, pdf):
    """V PDF musí být u každé otázky přesně tři možnosti."""
    divne = []
    for q in questions:
        z_pdf = _options_from_pdf(pdf, q["pdf_number"], q["source_page"] - 1)
        if z_pdf is not None and set(z_pdf) != {"A", "B", "C"}:
            divne.append((q["pdf_number"], sorted(z_pdf)))
    assert not divne, f"jiný počet možností než 3: {divne[:10]}"
