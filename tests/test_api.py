"""Čtecí JSON API.

Nejdůležitější vlastnost: dokud není nastavený token, API neexistuje.
Zapomenutá proměnná nesmí znamenat, že jsou něčí statistiky veřejně na síti.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

TOKEN = "testovaci-token-42"
EMAIL = "api@example.com"


def _klient(token: str | None = TOKEN) -> TestClient:
    if token:
        os.environ["PRO_ZBROJAK_API_TOKEN"] = token
    else:
        os.environ.pop("PRO_ZBROJAK_API_TOKEN", None)
    os.environ["PRO_ZBROJAK_ADMINS"] = EMAIL
    import src.api
    importlib.reload(src.api)
    app = FastAPI()
    src.api.register(app)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def klient():
    c = _klient()
    yield c
    os.environ.pop("PRO_ZBROJAK_API_TOKEN", None)


# ------------------------------------------------------------- přístup

def test_bez_tokenu_api_neexistuje():
    """Nenastavená proměnná = vypnuté API, ne volný přístup."""
    c = _klient(token=None)
    for cesta in ("/api", "/api/stav", "/api/chyby", "/api/kontext"):
        assert c.get(cesta).status_code == 404, cesta


def test_spatny_token_neprojde(klient):
    assert klient.get("/api/stav").status_code == 401
    assert klient.get("/api/stav?token=spatny").status_code == 401
    assert klient.get(
        "/api/stav", headers={"Authorization": "Bearer spatny"}
    ).status_code == 401


def test_token_v_hlavicce_projde(klient):
    r = klient.get("/api/stav", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200


def test_token_v_parametru_projde(klient):
    """Kvůli nástrojům, které neumí hlavičky — v README je to označené
    jako méně vhodné, protože se token zapíše do logů proxy."""
    assert klient.get(f"/api/stav?token={TOKEN}").status_code == 200


def test_prazdny_token_neprojde(klient):
    assert klient.get("/api/stav?token=").status_code == 401


# ------------------------------------------------------------- obsah

def test_rozcestnik_vypise_endpointy(klient):
    d = klient.get(f"/api?token={TOKEN}").json()
    assert "verze" in d
    for cesta in ("/api/stav", "/api/chyby", "/api/kontext"):
        assert cesta in d["endpointy"]


def test_stav_ma_ocekavane_udaje(klient):
    d = klient.get(f"/api/stav?token={TOKEN}").json()
    for klic in ("uzivatel", "otazek_v_katalogu", "pokusu", "uspesnost_pct",
                 "chybnych_otazek", "oblasti"):
        assert klic in d, klic
    assert d["otazek_v_katalogu"] == 837


def test_kontext_nese_pokyn_pro_ai(klient):
    d = klient.get(f"/api/kontext?token={TOKEN}").json()
    assert "pokyn" in d and "nedomýšlej" in d["pokyn"]
    assert "stav" in d and "nejcastejsi_chyby" in d


def test_limit_se_dodrzuje(klient):
    d = klient.get(f"/api/chyby?token={TOKEN}&limit=3").json()
    assert len(d["chyby"]) <= 3


def test_limit_mimo_rozsah_je_odmitnut(klient):
    assert klient.get(f"/api/chyby?token={TOKEN}&limit=0").status_code == 422
    assert klient.get(f"/api/chyby?token={TOKEN}&limit=9999").status_code == 422


def test_bez_emailu_a_bez_admina_srozumitelna_chyba():
    os.environ["PRO_ZBROJAK_API_TOKEN"] = TOKEN
    os.environ["PRO_ZBROJAK_ADMINS"] = ""
    import src.api
    importlib.reload(src.api)
    app = FastAPI()
    src.api.register(app)
    c = TestClient(app, raise_server_exceptions=False)
    r = c.get(f"/api/stav?token={TOKEN}")
    assert r.status_code == 400
    os.environ.pop("PRO_ZBROJAK_API_TOKEN", None)


def test_api_je_jen_ke_cteni(klient):
    """Žádný endpoint nesmí přijímat zápis."""
    for cesta in ("/api", "/api/stav", "/api/chyby", "/api/kontext"):
        assert klient.post(cesta, json={}).status_code in (404, 405)
