"""Overi ze kazdy Material Icon glyph v src/ui/icons.py::I se v browseru
skutecne vyrenderuje (ma visible width > 0). Pokud ne, font tu ikonu neobsahuje
a je potreba zvolit jiny glyph.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_ui_e2e import server, browser  # noqa: F401, E402


def test_every_icon_glyph_renders(server, browser):
    """Pro kazdou ikonu z I dict overi, ze jeji glyph ma visible width > 0.

    Material Icons (stara sada v Quasar) neobsahuje vsechny glyphy Material Symbols
    — pokud glyph chybi, renderuje se jako text (napr. 'target' — 6 znaku misto ikony),
    ale reakce: nekdy text je vypnut a pole je prazdne = width ~0.
    """
    from src.ui.icons import I

    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()

    # Vytvor HTML stranku s vsemi ikonami pres Material Icons font
    glyphs_html = "".join(
        f'<span class="material-icons icon-test" data-key="{key}" style="font-size:24px;">{glyph}</span>'
        for key, glyph in I.items()
    )
    page.set_content(f"""
    <!doctype html>
    <html><head>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    </head><body>{glyphs_html}</body></html>
    """)
    # Wait for font to load
    page.wait_for_timeout(2000)

    results = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('.icon-test').forEach(el => {
            const r = el.getBoundingClientRect();
            out.push({
                key: el.dataset.key,
                glyph: el.textContent,
                width: r.width,
                height: r.height,
                // Material icons glyphs render as 24x24 ligatures, wider = text fallback
                is_icon: r.width >= 20 && r.width <= 30,
            });
        });
        return out;
    }""")
    ctx.close()

    broken = [r for r in results if not r["is_icon"]]
    if broken:
        lines = "\n".join(
            f"  {r['key']:20s} glyph={r['glyph']!r:25s} width={r['width']:.1f}"
            for r in broken
        )
        pytest.fail(
            f"Nasledujici Material Icons glyphy se nerenderuji spravne (sirka != 20-30px):\n"
            f"{lines}\n"
            "Nahrad je v src/ui/icons.py za validni glyph z Material Icons."
        )
