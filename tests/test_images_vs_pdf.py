"""Obrázky otázek musí zachytit VŠECHNU grafiku, která k otázce v PDF patří.

Některé otázky mají v PDF víc samostatných obrázků pod sebou — otázka 609 má
tři znehodnocovací značky, každou jako vlastní objekt. Extrakce původně brala
jen první z nich, takže se zobrazila jedna značka ze tří a zadání mluvící
o „obrazcích" v množném čísle nedávalo smysl. Tenhle test to hlídá u všech.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pymupdf = pytest.importorskip("pymupdf")
Image = pytest.importorskip("PIL.Image")

QUESTIONS_PATH = ROOT / "data" / "questions.json"
IMAGES_DIR = ROOT / "images"
RENDER_DPI = 170
TOLERANCE_PX = 2  # zaokrouhlení při rasterizaci


def _pdf_path() -> Path | None:
    hits = sorted(ROOT.glob("docs/MV-Soubor*.pdf")) + sorted(ROOT.glob("MV-Soubor*.pdf"))
    return hits[0] if hits else None


@pytest.fixture(scope="module")
def questions() -> list[dict]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def doc():
    path = _pdf_path()
    if path is None:
        pytest.skip("Zdrojové PDF MV ČR v repu není — jen pro maintainery.")
    d = pymupdf.open(path)
    yield d
    d.close()


def _image_rects(page) -> list:
    seen: set[tuple[int, int, int, int]] = set()
    rects = []
    for img in page.get_images(full=True):
        try:
            found = page.get_image_rects(img[0])
        except Exception:
            found = []
        for r in found:
            key = (int(r.x0), int(r.y0), int(r.x1), int(r.y1))
            if key not in seen:
                seen.add(key)
                rects.append(r)
    return sorted(rects, key=lambda r: r.y0)


def test_q609_ma_vsechny_tri_znacky(questions, doc):
    """Regrese na konkrétní nález: otázka 609 měla jen první ze tří značek."""
    q = next(x for x in questions if x["pdf_number"] == 609)
    page = doc[q["source_page"] - 1]
    rects = _image_rects(page)
    assert len(rects) == 3, f"na straně {q['source_page']} čekáme 3 obrázky, je {len(rects)}"

    with Image.open(ROOT / q["image"]) as im:
        width, height = im.size

    zoom = RENDER_DPI / 72.0
    span = (max(r.y1 for r in rects) - min(r.y0 for r in rects)) * zoom
    assert height >= span - TOLERANCE_PX, (
        f"obrázek je vysoký {height} px, ale tři značky zabírají {span:.0f} px "
        "— vyrenderovala se jen část"
    )
    # Sanity: výrazně vyšší než jedna značka.
    jedna = (rects[0].y1 - rects[0].y0) * zoom
    assert height > jedna * 2, "výška odpovídá jediné značce"
    assert width > 0


def test_kazdy_obrazek_pokryva_celou_grafiku_otazky(questions, doc):
    """Pro všech 71 otázek s obrázkem: výška PNG musí sednout na rozsah
    obrázkových objektů, které na stránce k otázce patří."""
    with_image = [q for q in questions if q.get("image")]
    assert with_image, "žádné otázky s obrázkem"

    # Kolik otázek začíná na které stránce — kvůli spodní hranici výřezu.
    by_page: dict[int, list[dict]] = {}
    for q in questions:
        by_page.setdefault(q["source_page"], []).append(q)

    kratke = []
    for q in with_image:
        page = doc[q["source_page"] - 1]
        rects = _image_rects(page)
        if not rects:
            continue
        # Otázka je na stránce sama → všechny obrázky patří jí.
        if len(by_page.get(q["source_page"], [])) != 1:
            continue
        path = ROOT / q["image"]
        if not path.exists():
            kratke.append((q["pdf_number"], "soubor chybí"))
            continue
        with Image.open(path) as im:
            height = im.size[1]
        zoom = RENDER_DPI / 72.0
        span = (max(r.y1 for r in rects) - min(r.y0 for r in rects)) * zoom
        if height < span - TOLERANCE_PX:
            kratke.append((q["pdf_number"], f"{height} px < {span:.0f} px"))

    assert not kratke, f"oříznuté obrázky: {kratke}"


def test_vsechny_obrazky_maji_rozumne_rozmery(questions):
    """Nulové nebo pásové rozměry znamenají špatný výřez."""
    spatne = []
    for q in (x for x in questions if x.get("image")):
        path = ROOT / q["image"]
        if not path.exists():
            spatne.append((q["pdf_number"], "chybí"))
            continue
        with Image.open(path) as im:
            w, h = im.size
        if w < 40 or h < 20:
            spatne.append((q["pdf_number"], f"{w}×{h}"))
    assert not spatne, f"podezřelé rozměry: {spatne}"
