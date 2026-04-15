"""E2E overeni ze DOM obsahuje Material Symbols (q-icon / material-icons classes)
misto emoji."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Reuse fixtures from test_ui_e2e
from tests.test_ui_e2e import server, browser  # noqa: F401, E402


def test_nav_uses_q_icons_not_emojis(server, browser):
    """Nav drawer — kazda polozka ma Quasar q-icon, ne emoji text."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    # Open drawer
    page.locator("header button").first.click()
    page.wait_for_timeout(400)
    # Every nav link should contain a .q-icon
    nav_links = page.locator(".zp-nav-link")
    assert nav_links.count() >= 8
    for i in range(nav_links.count()):
        icons = nav_links.nth(i).locator(".q-icon")
        assert icons.count() >= 1, f"Nav link {i} nema q-icon"
    # Nav text nesmi obsahovat typicke emoji znaky
    nav_text = page.locator(".zp-nav-link").all_text_contents()
    joined = "".join(nav_text)
    for bad in "🏃🧠🎲🎯🎓📝⭐📤⚙️📊":
        assert bad not in joined, f"Nav obsahuje emoji {bad!r}"
    ctx.close()


def test_dashboard_tiles_use_q_icons(server, browser):
    """Dashboard tiles — icon bubble obsahuje q-icon (Material Symbol)."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(600)
    tiles = page.locator(".zp-tile")
    assert tiles.count() >= 5
    # At least one tile must contain a q-icon
    for i in range(tiles.count()):
        ql = tiles.nth(i).locator(".q-icon")
        assert ql.count() >= 1, f"Tile {i} nema q-icon"
    ctx.close()


def test_header_brand_has_icon(server, browser):
    """Header — brand ikona (target) je q-icon."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    icons = page.locator("header .q-icon")
    assert icons.count() >= 3  # menu, brand, help, dark_mode
    ctx.close()


def test_quiz_card_has_material_option_keys(server, browser):
    """Quiz option buttons maji key chipy (a/b/c)."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/random", wait_until="networkidle")
    page.wait_for_timeout(800)
    opts = page.locator(".zp-opt")
    assert opts.count() == 3
    key_chips = page.locator(".zp-opt .opt-key")
    assert key_chips.count() == 3
    # Should contain a, b, c
    keys = [k.inner_text().strip() for k in key_chips.all()]
    assert set(keys) == {"a", "b", "c"}
    ctx.close()


def test_rendered_page_has_no_emoji_in_visible_text(server, browser):
    """Rendered body nesmi obsahovat naše kontrolovaná UI emoji (kromě charts legend)."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    body_text = page.evaluate("document.body.innerText")
    for bad in ["🏃", "🧠", "📊", "📤", "⚙️", "🎓", "⭐", "💪"]:
        assert bad not in body_text, f"Rendered text obsahuje emoji {bad!r}"
    ctx.close()
