"""Responzivni gallery test — kazda stranka × 3 viewporty → screenshot.

Pristup: deviceScaleFactor=1 (ne 3x Retina), zabira skutecnou velikost v pixelech.
Screenshoty do tests/screenshots/responsive/<page>_<viewport>.png.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = ROOT / "tests" / "screenshots" / "responsive"
sys.path.insert(0, str(ROOT))

from tests.test_ui_e2e import server, browser  # noqa: F401, E402


VIEWPORTS = {
    "mobile":  {"width": 390, "height": 844},
    "tablet":  {"width": 768, "height": 1024},
    "desktop": {"width": 1280, "height": 900},
}

PAGES = {
    "dashboard":  "/",
    "marathon":   "/marathon",
    "srs":        "/srs",
    "random":     "/random",
    "mistakes":   "/mistakes",
    "mastery":    "/mastery",
    "exam":       "/exam",
    "flagged":    "/flagged",
    "export":     "/export",
    "settings":   "/settings",
}


@pytest.fixture(scope="module", autouse=True)
def _ensure_dir():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.mark.parametrize("viewport_name", list(VIEWPORTS.keys()))
@pytest.mark.parametrize("page_name", list(PAGES.keys()))
def test_visual_gallery(server, browser, viewport_name, page_name):
    """Screenshot + zakladni sanity kontrola pro viewport × page combination."""
    vp = VIEWPORTS[viewport_name]
    path = PAGES[page_name]
    ctx = browser.new_context(viewport=vp, device_scale_factor=1)
    page = ctx.new_page()
    page.goto(server + path, wait_until="networkidle")
    page.wait_for_timeout(800)

    # Screenshot
    page.screenshot(
        path=str(SCREENSHOTS_DIR / f"{page_name}_{viewport_name}.png"),
        full_page=True,
    )

    # Check: no horizontal overflow (page is wider than viewport)
    overflow = page.evaluate("""() => {
        const doc = document.documentElement;
        // Find elements that cause horizontal overflow
        const culprits = [];
        const vw = window.innerWidth;
        document.querySelectorAll('*').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.right > vw + 5) {
                const tag = el.tagName.toLowerCase();
                const cls = el.className.toString ? el.className.toString() : '';
                const txt = el.textContent ? el.textContent.substring(0, 40).replace(/\\s+/g, ' ').trim() : '';
                culprits.push({tag, cls: cls.substring(0, 60), right: Math.round(r.right), txt});
            }
        });
        return {
            scrollWidth: doc.scrollWidth,
            clientWidth: doc.clientWidth,
            windowInner: vw,
            culprits: culprits.slice(0, 5),
        };
    }""")
    if overflow["scrollWidth"] > overflow["clientWidth"] + 5:
        culprit_lines = "\n".join(
            f"    {c['tag']}.{c['cls']} right={c['right']} txt={c['txt']!r}"
            for c in overflow["culprits"]
        )
        pytest.fail(
            f"{page_name}@{viewport_name}: horizontalni overflow! "
            f"scrollWidth={overflow['scrollWidth']} clientWidth={overflow['clientWidth']}\n"
            f"Culprits:\n{culprit_lines}"
        )

    # Check: header is present and sized
    hdr = page.evaluate("""() => {
        const h = document.querySelector('.q-header');
        if (!h) return null;
        const r = h.getBoundingClientRect();
        return {height: r.height, width: r.width};
    }""")
    if hdr:
        assert hdr["height"] >= 44, f"{page_name}@{viewport_name}: header {hdr['height']}px < 44px"

    ctx.close()
