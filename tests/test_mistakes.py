"""Lekce z chyb — statistiky, řazení a filtrování.

Dřív se fronta jen zamíchala, takže se skákalo mezi oblastmi a nedalo se
poznat, co člověk plete nejčastěji. Tenhle test hlídá, že pořadí, které si
uživatel zvolí, opravdu platí.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

sqlite_utils = pytest.importorskip("sqlite_utils")

from src.db import store  # noqa: E402
from src.ui.pages.practice import RAZENI  # noqa: E402

UZIVATEL = "chyby@example.com"


@pytest.fixture()
def db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(store, "DB_PATH", Path(tmp) / "t.db")
        yield store.get_db()


def _odpoved(db, qid: str, spravne: bool) -> None:
    store.record_attempt(db, user_email=UZIVATEL, question_id=qid,
                         chosen="A", correct="A" if spravne else "B", mode="random")


def test_statistiky_pocitaji_chyby_i_pokusy(db):
    for _ in range(3):
        _odpoved(db, "q1", spravne=False)
    _odpoved(db, "q1", spravne=True)
    _odpoved(db, "q2", spravne=False)

    s = store.mistake_stats(db, UZIVATEL)
    assert s["q1"]["chyb"] == 3
    assert s["q1"]["pokusu"] == 4
    assert s["q1"]["podil"] == 0.75
    assert s["q2"]["chyb"] == 1


def test_spravne_zodpovezena_otazka_v_chybach_neni(db):
    _odpoved(db, "q1", spravne=True)
    assert "q1" not in store.mistake_stats(db, UZIVATEL)


def test_jednou_chybna_otazka_zustava(db):
    """I když ji člověk potom dá správně — plete se, tak ať se vrací."""
    _odpoved(db, "q1", spravne=False)
    for _ in range(5):
        _odpoved(db, "q1", spravne=True)
    assert store.mistake_stats(db, UZIVATEL)["q1"]["chyb"] == 1


def test_statistiky_jsou_per_uzivatel(db):
    _odpoved(db, "q1", spravne=False)
    store.record_attempt(db, user_email="nikdo@example.com", question_id="q2",
                         chosen="A", correct="B", mode="random")
    assert set(store.mistake_stats(db, UZIVATEL)) == {"q1"}


# ------------------------------------------------------------------ řazení

VZOROVE = {
    "a": {"chyb": 5, "podil": 0.5, "posledni_chyba": 100},
    "b": {"chyb": 1, "podil": 1.0, "posledni_chyba": 300},
    "c": {"chyb": 3, "podil": 0.3, "posledni_chyba": 200},
}
OTAZKY = [{"id": "a", "pdf_number": 10}, {"id": "b", "pdf_number": 5},
          {"id": "c", "pdf_number": 20}]


def _serad(klic: str) -> list[str]:
    return [q["id"] for q in sorted(OTAZKY, key=lambda q: RAZENI[klic][1](q, VZOROVE[q["id"]]))]


def test_razeni_podle_poctu_chyb():
    assert _serad("nejvic") == ["a", "c", "b"]


def test_razeni_podle_pomeru():
    """Otázka s 1 chybou z 1 pokusu je naléhavější než 5 chyb z 10."""
    assert _serad("podil") == ["b", "a", "c"]


def test_razeni_podle_cerstvosti():
    assert _serad("cerstve") == ["b", "c", "a"]


def test_razeni_po_poradi():
    assert _serad("cislo") == ["b", "a", "c"]


def test_vsechna_razeni_maji_nazev():
    for klic, (nazev, funkce) in RAZENI.items():
        assert nazev and callable(funkce), klic


# ------------------------------------------------------------------ fronta

def test_quizsession_bez_michani_zachova_poradi():
    """Se `shuffle=False` musí fronta zůstat tak, jak ji volající předal."""
    from src.ui.components import QuizSession
    pool = [{"id": f"q{i}", "pdf_number": i} for i in range(20)]
    s = QuizSession(pool=pool, mode="mistakes", shuffle=False)
    assert s.shuffle is False
    # výchozí chování ostatních režimů se nemění
    assert QuizSession(pool=pool, mode="random").shuffle is True
