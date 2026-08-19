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

from tests.test_ui_e2e import server  # noqa: F401, E402


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
