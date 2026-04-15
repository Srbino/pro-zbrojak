"""End-to-end UI testy pomoci Playwright.

Spusti realny prohlizec, otevre kazdou stranku, vezme screenshot, overi kriticka UI.
Screenshoty se ukladaji do tests/screenshots/.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = ROOT / "tests" / "screenshots"
PORT = 8765  # test port (different from 8080 to not collide)


@pytest.fixture(scope="module")
def server():
    """Spusti app.py na test portu, zabije na konci."""
    SCREENSHOTS.mkdir(exist_ok=True)
    wrapper_code = (
        "import sys, os\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        f"os.chdir({str(ROOT)!r})\n"
        "# Import app to register pages; app.py won't run ui.run because __name__ is 'app'\n"
        "import app\n"
        "from nicegui import ui\n"
        f"ui.run(host='127.0.0.1', port={PORT}, show=False, reload=False, title='ZP Test')\n"
    )
    import os
    env = {**os.environ}
    # NiceGUI auto-detects pytest and expects NICEGUI_SCREEN_TEST_PORT; provide it or remove detection
    env["NICEGUI_SCREEN_TEST_PORT"] = str(PORT)
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("PYTEST_VERSION", None)
    proc = subprocess.Popen(
        [sys.executable, "-c", wrapper_code],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    # Wait for ready
    for _ in range(40):
        if proc.poll() is not None:
            out = proc.stdout.read().decode() if proc.stdout else ""
            raise RuntimeError(f"server died: {out[-2000:]}")
        time.sleep(0.25)
        try:
            import urllib.request
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1)
            break
        except Exception:
            continue
    yield f"http://127.0.0.1:{PORT}"
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _snap(page: Page, name: str):
    page.screenshot(path=str(SCREENSHOTS / f"{name}.png"), full_page=True)


def test_dashboard_renders_hero_and_tiles(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(800)
    _snap(page, "01_dashboard")

    # Header title must be visible with proper contrast
    hdr = page.evaluate("""() => {
        const t = document.querySelector('.zp-header-title');
        if (!t) return {found: false};
        const s = getComputedStyle(t);
        return {found: true, text: t.innerText, color: s.color, visible: t.offsetParent !== null};
    }""")
    assert hdr["found"] and hdr["visible"], f"Header title not visible: {hdr}"
    assert hdr["text"], "Header title should have text"
    # Color should be dark (sum of RGB < 300 for 'dark' text in light mode)
    import re as _re
    m = _re.search(r"rgb\((\d+),\s*(\d+),\s*(\d+)", hdr["color"])
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        assert r + g + b < 300, f"Header title color too light: {hdr['color']}"

    # Hero title vizible
    expect(page.locator(".zp-h1").first).to_be_visible(timeout=5000)
    # At least one tile
    assert page.locator(".zp-tile").count() >= 5, "dashboard should have at least 5 tiles"
    # Stat cards present
    assert page.locator(".zp-metric").count() >= 3, "should have 3 stat metrics"
    ctx.close()


def test_marathon_page_renders_quiz(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    # Start fresh marathon
    page.goto(server + "/marathon", wait_until="networkidle")
    page.wait_for_timeout(500)
    # Click "Začít nový marathon" (may be present if no active run)
    start_btn = page.get_by_text("Začít nový marathon")
    if start_btn.count():
        start_btn.first.click()
        page.wait_for_timeout(500)
    _snap(page, "02_marathon")

    # Question card visible
    expect(page.locator(".zp-card").first).to_be_visible(timeout=5000)
    # 3 option buttons visible
    assert page.locator(".zp-opt").count() == 3, "should have 3 option buttons"
    ctx.close()


def test_quiz_click_shows_feedback(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/random", wait_until="networkidle")
    page.wait_for_timeout(800)
    # Click first option
    page.locator(".zp-opt").first.click()
    page.wait_for_timeout(400)
    _snap(page, "03_quiz_answered")
    # After click, one option should be .correct or .wrong
    marked = page.locator(".zp-opt.correct, .zp-opt.wrong").count()
    assert marked >= 1, "clicking answer should mark correct/wrong"
    ctx.close()


def test_exam_setup_page(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/exam", wait_until="networkidle")
    page.wait_for_timeout(500)
    _snap(page, "04_exam_setup")
    # Should have a "Spustit simulaci" button
    assert page.get_by_text("Spustit simulaci").count() >= 1
    ctx.close()


def test_srs_empty_state(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/srs", wait_until="networkidle")
    page.wait_for_timeout(500)
    _snap(page, "05_srs")
    # Should either show queue or empty state or completed banner
    ctx.close()


def test_mastery_page_shows_sections(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/mastery", wait_until="networkidle")
    page.wait_for_timeout(500)
    _snap(page, "06_mastery")
    # Should have all section cards and progress bars
    assert page.locator(".zp-progress").count() >= 3
    ctx.close()


def test_settings_page(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/settings", wait_until="networkidle")
    page.wait_for_timeout(500)
    _snap(page, "07_settings")
    # Reset button present
    assert page.get_by_text("Reset historie").count() >= 1
    ctx.close()


def test_export_page(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/export", wait_until="networkidle")
    page.wait_for_timeout(500)
    _snap(page, "08_export")
    assert page.get_by_text("Vygenerovat Markdown").count() >= 1
    ctx.close()


def test_dark_mode_toggle(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    # Click dark mode toggle (icon button in header)
    page.locator('button:has(.q-icon:has-text("dark_mode"))').first.click()
    page.wait_for_timeout(800)
    # Debug: print body classes and resolved css var
    info = page.evaluate("""() => ({
        bodyCls: document.body.className,
        htmlCls: document.documentElement.className,
        surfaceVar: getComputedStyle(document.body).getPropertyValue('--zp-surface').trim(),
        bg: getComputedStyle(document.body).backgroundColor,
    })""")
    print("DARK_MODE_DEBUG:", info)
    _snap(page, "09_dark_mode")
    ctx.close()


def test_exam_complete_flow_shows_result(server, browser):
    """Spusti rychlou simulaci (3 otazky, 120 s) a over hero pass/fail banner."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/exam", wait_until="networkidle")
    page.wait_for_timeout(800)
    # Set small exam: 3 questions
    # Click into "Počet otázek" input and set to 3
    count_input = page.locator('input[aria-label="Počet otázek"]').first
    count_input.click()
    count_input.fill("3")
    time_input = page.locator('input[aria-label="Časový limit (min)"]').first
    time_input.click()
    time_input.fill("5")
    page.wait_for_timeout(300)
    # Click Spustit simulaci
    page.get_by_text("Spustit simulaci").click()
    page.wait_for_timeout(1000)
    # Answer 3 questions (click first option each time)
    for i in range(3):
        page.wait_for_selector(".zp-opt:not(.disabled)", timeout=5000)
        page.locator(".zp-opt:not(.disabled)").first.click()
        page.wait_for_timeout(1200)
    _snap(page, "11a_before_finish")
    # If not auto-finished, click "Ukoncit simulaci" fallback
    if page.locator(".zp-hero-success, .zp-hero-danger").count() == 0:
        ukoncit = page.get_by_text("Ukončit simulaci")
        if ukoncit.count():
            ukoncit.first.click()
            page.wait_for_timeout(800)
    page.wait_for_selector(".zp-hero-success, .zp-hero-danger", timeout=10000)
    _snap(page, "11_exam_result")
    # Must contain the "Nová simulace" button
    assert page.get_by_text("Nová simulace").count() >= 1
    ctx.close()


def test_marathon_answer_flow(server, browser):
    """Overi ze po odpovedi v marathonu se objevi Dalsi button a barvy spravne/spatne."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(server + "/marathon", wait_until="networkidle")
    page.wait_for_timeout(500)
    start_btn = page.get_by_text("Začít nový marathon")
    if start_btn.count():
        start_btn.first.click()
        page.wait_for_timeout(500)
    # Click an option
    page.locator(".zp-opt").first.click()
    page.wait_for_timeout(400)
    _snap(page, "12_marathon_answered")
    # Next button appeared
    assert page.get_by_text("Další").count() >= 1
    # Either correct or wrong class visible
    assert page.locator(".zp-opt.correct, .zp-opt.wrong").count() >= 1
    ctx.close()


def test_responsive_mobile(server, browser):
    ctx = browser.new_context(viewport={"width": 375, "height": 800})
    page = ctx.new_page()
    page.goto(server + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    _snap(page, "10_mobile")
    ctx.close()
