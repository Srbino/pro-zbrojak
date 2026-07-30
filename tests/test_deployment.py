"""Nasaditelnost — aby si aplikaci mohl rozjet kdokoli, ne jen autor.

Hlídá tři věci, na kterých se to nejčastěji láme:
  1. ve zdrojácích nejsou natvrdo konkrétní lidé,
  2. slabé session tajemství neprojde do veřejného provozu,
  3. konfigurace z prostředí se čte tak, jak README slibuje.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Zdrojový kód aplikace — dokumentace a data se nekontrolují.
CODE_DIRS = ("src", "scripts")
CODE_FILES = ("app.py", "parse_pdf.py")

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
# Adresy, které do kódu patří: příklady, zástupné hodnoty, testovací identity.
ALLOWED = {
    "noreply@", "example.com", "example.org", "user@", "mail@",
    "@pro-zbrojak", "pro-zbrojak.local", "a.cz", "b.cz",
}


def _source_files() -> list[Path]:
    out = [ROOT / f for f in CODE_FILES]
    for d in CODE_DIRS:
        out.extend(sorted((ROOT / d).rglob("*.py")))
    return [p for p in out if p.exists()]


def test_zdrojaky_neobsahuji_konkretni_lidi():
    """E-mail v kódu = cizí admin a zveřejněná adresa u každého, kdo si to nasadí."""
    nalezy = []
    for path in _source_files():
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for mail in EMAIL.findall(line):
                if any(a in mail for a in ALLOWED):
                    continue
                nalezy.append(f"{path.relative_to(ROOT)}:{i}  {mail}")
    assert not nalezy, "konkrétní e-maily ve zdrojácích:\n  " + "\n  ".join(nalezy)


def test_admini_se_berou_z_prostredi(monkeypatch):
    monkeypatch.setenv("PRO_ZBROJAK_ADMINS", " Sef@Firma.cz , druhy@firma.cz ")
    import importlib

    from src import auth
    importlib.reload(auth)
    assert auth.ADMIN_EMAILS == {"sef@firma.cz", "druhy@firma.cz"}
    assert auth.is_admin("SEF@FIRMA.CZ")
    assert not auth.is_admin("nikdo@firma.cz")


def test_bez_nastaveni_neni_nikdo_admin(monkeypatch):
    monkeypatch.delenv("PRO_ZBROJAK_ADMINS", raising=False)
    import importlib

    from src import auth
    importlib.reload(auth)
    assert auth.ADMIN_EMAILS == set()
    assert not auth.is_admin("kdokoli@firma.cz")


def test_prezdivky_se_ctou_z_prostredi(monkeypatch):
    monkeypatch.setenv("PRO_ZBROJAK_DISPLAY_NAMES", "a@firma.cz=Anna, b@firma.cz=Bob")
    import importlib

    from src import auth
    importlib.reload(auth)
    assert auth.display_name("a@firma.cz") == "Anna"
    assert auth.display_name("B@FIRMA.CZ") == "Bob"
    # bez přezdívky se použije část před zavináčem
    assert auth.display_name("karel@firma.cz") == "karel"


def _run_app(env: dict[str, str], timeout: int = 25):
    """Spustí app.py s daným prostředím a vrátí (returncode, výstup)."""
    prostredi = {**os.environ, **env, "SHOW": "false"}
    # NiceGUI si při běhu pod pytestem sahá po NICEGUI_SCREEN_TEST_PORT.
    # Tady spouštíme skutečnou aplikaci, ne screen test.
    for k in ("PYTEST_CURRENT_TEST", "PYTEST_VERSION"):
        prostredi.pop(k, None)
    proc = subprocess.run(
        [sys.executable, "app.py"],
        cwd=str(ROOT),
        env=prostredi,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, (proc.stdout + proc.stderr)


def test_verejny_provoz_odmitne_vychozi_tajemstvi():
    """Známé STORAGE_SECRET + poslech mimo localhost = kdokoli si podepíše cizí session."""
    code, out = _run_app({
        "HOST": "0.0.0.0",
        "PORT": "8123",
        "STORAGE_SECRET": "pro-zbrojak-local-dev-secret",
    })
    assert code != 0, "aplikace se spustila i s veřejně známým tajemstvím"
    assert "STORAGE_SECRET" in out


def test_lokalni_beh_vychozi_tajemstvi_povoli():
    """Na localhostu je vývojové tajemství v pořádku — jinak by dvojklik nefungoval.

    Aplikace se spustí a poslouchá, takže ji po ověření ukončíme timeoutem.
    """
    with pytest.raises(subprocess.TimeoutExpired):
        _run_app({"HOST": "127.0.0.1", "PORT": "8125"}, timeout=12)


@pytest.mark.parametrize("promenna", [
    "HOST", "PORT", "STORAGE_SECRET", "PRO_ZBROJAK_ADMINS",
    "PRO_ZBROJAK_DISPLAY_NAMES", "PRO_ZBROJAK_LOGIN_CODE",
])
def test_env_promenne_jsou_zdokumentovane(promenna):
    """Co se dá nastavit, musí být v README nebo .env.example — jinak to nikdo nenajde."""
    texty = ""
    for name in ("README.md", ".env.example"):
        p = ROOT / name
        if p.exists():
            texty += p.read_text(encoding="utf-8")
    assert promenna in texty, f"{promenna} není nikde zdokumentovaná"
