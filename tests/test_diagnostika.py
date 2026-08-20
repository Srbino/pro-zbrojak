"""Startovní diagnostika a /healthz.

Vzniklo po hledání „rozbitých obrázků" na nasazené instanci, kde se nakonec
ukázalo, že server je v pořádku a chyba byla ve staré otevřené záložce
mluvící na `/socket.io/` (NiceGUI 2.x) místo `/_nicegui_ws/socket.io/`.
Bez těchhle údajů se to nedalo poznat jinak než dohadem.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_ui_e2e import browser, server  # noqa: F401, E402


def _healthz(server: str) -> dict:
    with urllib.request.urlopen(server + "/healthz", timeout=5) as r:
        return json.loads(r.read())


def test_healthz_odpovida(server):
    assert _healthz(server)["status"] == "ok"


def test_healthz_rekne_co_bezi(server):
    """`curl /healthz` musí stačit k určení, co je nasazené."""
    d = _healthz(server)
    for klic in ("verze_aplikace", "nicegui", "socket_io", "otazek",
                 "obrazku", "host", "port", "vlastni_storage_secret"):
        assert klic in d, f"v /healthz chybí {klic}"


def test_healthz_hlasi_spravnou_cestu_socketu(server):
    """Cesta se mezi NiceGUI 2.x a 3.x změnila — proto je v diagnostice."""
    d = _healthz(server)
    cesta = d["socket_io"]
    with urllib.request.urlopen(
        f"{server}{cesta}?EIO=4&transport=polling", timeout=5
    ) as r:
        assert r.status == 200, "ohlášená cesta socketu neodpovídá"


def test_healthz_pocty_sedi_s_daty(server):
    d = _healthz(server)
    otazky = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    obrazky = list((ROOT / "images").glob("*.png"))
    assert d["otazek"] == len(otazky)
    assert d["obrazku"] == len(obrazky)


def test_vsechny_obrazky_jsou_dostupne_pres_http(server):
    """Kdyby se některý nedal stáhnout, projeví se to jako rozbitý obrázek."""
    otazky = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    spatne = []
    for q in otazky:
        if not q.get("image"):
            continue
        try:
            with urllib.request.urlopen(f"{server}/{q['image']}", timeout=5) as r:
                if r.status != 200 or r.headers.get_content_type() != "image/png":
                    spatne.append((q["pdf_number"], r.status))
                elif len(r.read()) < 1000:
                    spatne.append((q["pdf_number"], "podezřele malý"))
        except Exception as e:  # noqa: BLE001
            spatne.append((q["pdf_number"], str(e)[:40]))
    assert not spatne, f"nedostupné obrázky: {spatne[:10]}"


def test_stranka_diagnostiky_zkontroluje_vsechny_obrazky(server, browser):
    """Kontrola musí proběhnout v prohlížeči — server umí říct jen to, že
    soubor odeslal, ne že se vykreslil."""
    ctx = browser.new_context(viewport={"width": 1300, "height": 1000})
    page = ctx.new_page()
    page.goto(server + "/diagnostika", wait_until="networkidle")
    page.wait_for_timeout(5000)

    otazky = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    ocekavano = sum(1 for q in otazky if q.get("image"))

    assert page.locator(".zp-diag-item").count() == ocekavano
    chybne = page.locator(".zp-diag-item.bad").count()
    assert chybne == 0, f"{chybne} obrázků se v prohlížeči nenačetlo"
    assert "se načetlo" in page.locator("#zp-diag-souhrn").inner_text()


def test_skript_diagnostiky_je_v_tele_stranky(server):
    """Vložený přes ui.html by se nespustil — script z innerHTML prohlížeč
    neprovádí. Tenhle test to hlídá, protože selhání by bylo tiché."""
    # Bez identity vrátí stránka přihlášení — hlavička je stejná, jakou
    # v provozu nastavuje Cloudflare Access.
    from tests.test_ui_e2e import TEST_USER_EMAIL, TEST_USER_HEADER
    req = urllib.request.Request(
        server + "/diagnostika", headers={TEST_USER_HEADER: TEST_USER_EMAIL}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        html = r.read().decode()
    # Kontejnery vykreslí NiceGUI přes socket; skript musí být ve statickém
    # HTML, aby se spustil i bez něj a chybějící kontejnery si doplnil sám.
    assert "<script>" in html and "naturalWidth" in html
    assert "zp-diag-souhrn" in html, "skript neumí kontejner vyrobit sám"
