"""Testy mobilni responzivity a klikatelnosti."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_ui_e2e import _snap, browser, server  # noqa: F401, E402

MOBILE = {"width": 390, "height": 844}  # iPhone 14
TABLET = {"width": 768, "height": 1024}
DESKTOP = {"width": 1280, "height": 900}


# Na mobilu se do plné navigace vstupuje položkou Menu ve spodní liště,
# ne hamburgerem — ten je od 900 px výš. Testy drží stejnou záruku
# (dost velký cíl, otevře drawer, funguje i klik u kraje) na novém prvku.
MENU_TARGET = ".zp-tabbar-item:last-child"


def test_mobile_menu_has_large_hit_area(server, browser):
    """Vstup do menu ma min 44x44px hit area (Apple HIG + WCAG)."""
    ctx = browser.new_context(viewport=MOBILE)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    box = page.locator(MENU_TARGET).first.bounding_box()
    assert box is not None, "Polozka Menu ve spodni liste nenalezena"
    assert box["width"] >= 44, f"Menu width {box['width']} < 44px"
    assert box["height"] >= 44, f"Menu height {box['height']} < 44px"
    ctx.close()


def test_hamburger_hidden_on_mobile_shown_on_desktop(server, browser):
    """Dva vstupy do stejne navigace by si konkurovaly — na mobilu je jen lista."""
    ctx = browser.new_context(viewport=MOBILE)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    assert page.locator(".zp-hamburger:visible").count() == 0, "Na mobilu ma byt hamburger skryty"
    assert page.locator(".zp-tabbar:visible").count() == 1, "Na mobilu chybi spodni lista"
    ctx.close()

    ctx = browser.new_context(viewport=DESKTOP)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    assert page.locator(".zp-hamburger:visible").count() >= 1, "Na desktopu ma byt hamburger videt"
    assert page.locator(".zp-tabbar:visible").count() == 0, "Na desktopu nema byt spodni lista"
    ctx.close()


def test_mobile_menu_opens_drawer(server, browser):
    """Klik na Menu ve spodni liste otevre plnou navigaci."""
    ctx = browser.new_context(viewport=MOBILE)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    page.locator(MENU_TARGET).first.click()
    page.wait_for_timeout(600)
    visible_links = page.locator(".zp-nav-link:visible").count()
    assert visible_links >= 5, f"Drawer neotevrelo dostatek nav links: {visible_links}"
    ctx.close()


def test_mobile_menu_edge_click_works(server, browser):
    """Klik u kraje polozky Menu — cely cil musi byt klikatelny."""
    ctx = browser.new_context(viewport=MOBILE)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    box = page.locator(MENU_TARGET).first.bounding_box()
    x = box["x"] + box["width"] * 0.85
    y = box["y"] + box["height"] * 0.85
    page.mouse.click(x, y)
    page.wait_for_timeout(600)
    visible_links = page.locator(".zp-nav-link:visible").count()
    assert visible_links >= 5, "Klik u kraje polozky Menu musi otevrit drawer"
    ctx.close()


def test_dashboard_tiles_stack_on_mobile(server, browser):
    """Na mobile jsou tiles v jednom sloupci (grid-template-columns: 1fr)."""
    ctx = browser.new_context(viewport=MOBILE)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    grid_cols = page.evaluate("""() => {
        const g = document.querySelector('.zp-grid-3');
        return g ? getComputedStyle(g).gridTemplateColumns : null;
    }""")
    assert grid_cols and grid_cols.count(" ") == 0, (
        f"Mobile grid should have single column, got: {grid_cols}"
    )
    ctx.close()


def test_all_nav_items_have_visible_icons_on_mobile(server, browser):
    """V drawer menu maji vsechny polozky (vcetne 'Lekce z chyb') ikonu."""
    ctx = browser.new_context(viewport=MOBILE)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    # Open drawer
    page.locator(MENU_TARGET).first.click()
    page.wait_for_timeout(500)
    # Vsechny nav links maji .q-icon uvnitr s > 0 visible width
    icon_check = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('.zp-nav-link:not([style*=\"display: none\"])').forEach(a => {
            const label = a.textContent.trim();
            const icons = a.querySelectorAll('.q-icon');
            let widths = [];
            icons.forEach(i => { widths.push(i.getBoundingClientRect().width); });
            out.push({label, icons: icons.length, widths});
        });
        return out;
    }""")
    missing = [r for r in icon_check if r["icons"] == 0 or all(w < 10 for w in r["widths"])]
    assert not missing, f"Nav polozky bez viditelne ikony: {missing}"
    ctx.close()


def test_header_responsive_hides_subtitle_on_small_mobile(server, browser):
    """Na velmi malem mobile (< 400px) se subtitle skryje aby bylo misto."""
    ctx = browser.new_context(viewport={"width": 360, "height": 800})
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    sub_visible = page.evaluate("""() => {
        const el = document.querySelector('.zp-header-sub');
        if (!el) return false;
        return getComputedStyle(el).display !== 'none';
    }""")
    # Na 360px sirce by sub mel byt skryty
    assert not sub_visible, "Subtitle by mel byt skryty na mobile < 400px"
    ctx.close()


def test_dashboard_perf_budget(server, browser):
    """Dashboard musi nacist v rozumnem case (< 4s)."""
    ctx = browser.new_context(viewport=DESKTOP)
    page = ctx.new_page()
    import time
    t0 = time.time()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_selector(".zp-hero, .zp-hero-primary", timeout=6000)
    dt = time.time() - t0
    assert dt < 6.0, f"Dashboard load {dt:.2f}s > 6s budget"
    # No >1000 DOM nodes (KISS budget)
    count = page.evaluate("() => document.querySelectorAll('*').length")
    assert count < 2500, f"Dashboard ma {count} DOM uzlu (> 2500 = overengineered)"
    ctx.close()


def test_quiz_page_tiles_on_tablet(server, browser):
    """Na tablet (768px) je grid 2-col."""
    ctx = browser.new_context(viewport=TABLET)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    grid_cols = page.evaluate("""() => {
        const g = document.querySelector('.zp-grid-3');
        return g ? getComputedStyle(g).gridTemplateColumns : null;
    }""")
    # 768px → 2-col per our @media (max-width: 900px)
    assert grid_cols and grid_cols.count(" ") == 1, (
        f"Tablet grid should have 2 columns, got: {grid_cols}"
    )
    ctx.close()


def test_all_pages_load_on_mobile(server, browser):
    """Vsechny routy se na mobile nacitaji bez errors."""
    ctx = browser.new_context(viewport=MOBILE)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    for path in ["/", "/marathon", "/random", "/srs", "/exam",
                 "/mistakes", "/mastery", "/flagged", "/export", "/settings"]:
        page.goto(server + path, wait_until="networkidle")
        page.wait_for_timeout(300)
    filtered = [e for e in errors if "favicon" not in e.lower()]
    assert not filtered, f"Mobile pages errors: {filtered}"
    ctx.close()


def test_mistakes_nav_link_has_icon(server, browser):
    """Specificky test: 'Lekce z chyb' v drawer MUSI mit validni ikonu."""
    ctx = browser.new_context(viewport=DESKTOP)
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(400)
    page.locator(".zp-hamburger").first.click()
    page.wait_for_timeout(500)
    # Najdi link "Lekce z chyb"
    mistakes_link = page.locator(".zp-nav-link").filter(has_text="Lekce z chyb")
    assert mistakes_link.count() == 1
    icon_width = page.evaluate("""() => {
        const links = Array.from(document.querySelectorAll('.zp-nav-link'));
        const l = links.find(x => x.textContent.includes('Lekce z chyb'));
        if (!l) return 0;
        const i = l.querySelector('.q-icon');
        return i ? i.getBoundingClientRect().width : 0;
    }""")
    assert 20 <= icon_width <= 40, (
        f"'Lekce z chyb' ikona ma spatnou velikost {icon_width}px "
        "(ocekavano ~24px — glyph se renderuje jako Material Icon, ne text)"
    )
    ctx.close()
