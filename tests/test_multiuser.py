"""Víceuživatelský provoz — data jednoho uživatele nesmí prosáknout k druhému.

Aplikace se nasazuje za Cloudflare Access, kde identitu určuje hlavička.
Každý řádek v DB nese `user_email`; tenhle test hlídá, že se podle něj
opravdu filtruje — ve všech tabulkách, ne jen v pokusech.
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

ANA = "ana@example.com"
BOB = "bob@example.com"


@pytest.fixture()
def db(monkeypatch):
    """Čerstvá DB v dočasném souboru — testy nesmí sahat na data uživatele."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.db"
        monkeypatch.setattr(store, "DB_PATH", path)
        yield store.get_db()


def _answer(db, email: str, qid: str, correct: bool, mode: str = "random") -> None:
    store.record_attempt(
        db, user_email=email, question_id=qid,
        chosen="A", correct="A" if correct else "B", mode=mode,
    )


# ---------------------------------------------------------------- pokusy

def test_statistiky_se_nemichaji(db):
    for i in range(5):
        _answer(db, ANA, f"q{i}", correct=True)
    for i in range(3):
        _answer(db, BOB, f"q{i}", correct=False)

    ana = store.stats_overall(db, ANA)
    bob = store.stats_overall(db, BOB)
    assert ana["attempts"] == 5 and ana["correct"] == 5
    assert bob["attempts"] == 3 and bob["correct"] == 0


def test_chyby_vidi_jen_vlastnik(db):
    _answer(db, ANA, "q1", correct=False)
    _answer(db, BOB, "q2", correct=False)
    assert store.question_ids_with_mistakes(db, ANA) == ["q1"]
    assert store.question_ids_with_mistakes(db, BOB) == ["q2"]


def test_neznamy_uzivatel_nevidi_nic(db):
    _answer(db, ANA, "q1", correct=True)
    cizi = store.stats_overall(db, "nikdo@example.com")
    assert cizi["attempts"] == 0


# ---------------------------------------------------------------- záložky

def test_zalozky_jsou_oddelene(db):
    store.set_bookmark(db, ANA, "q1", flagged=True)
    assert store.all_flagged(db, ANA) == ["q1"]
    assert store.all_flagged(db, BOB) == []

    # Bob si označí tutéž otázku — nesmí to přepsat Anin záznam.
    store.set_bookmark(db, BOB, "q1", flagged=True)
    store.set_bookmark(db, BOB, "q1", flagged=False)
    assert store.all_flagged(db, ANA) == ["q1"], "Bobova změna sáhla na Aniny záložky"


# ---------------------------------------------------------------- marathon

def test_marathon_ma_kazdy_vlastni(db):
    store.start_marathon(db, user_email=ANA, total=100)
    assert store.get_active_marathon(db, ANA) is not None
    assert store.get_active_marathon(db, BOB) is None


# ---------------------------------------------------------------- zkoušky

def test_vysledky_zkousek_jsou_oddelene(db):
    store.record_exam(db, user_email=ANA, level="standard", score=27, total=30, duration_s=600)
    assert len(store.list_exams(db, ANA)) == 1
    assert store.list_exams(db, BOB) == []


# ---------------------------------------------------------------- reset

def test_reset_smaze_jen_sva_data(db):
    for i in range(4):
        _answer(db, ANA, f"q{i}", correct=True)
        _answer(db, BOB, f"q{i}", correct=True)
    store.set_bookmark(db, ANA, "q1", flagged=True)
    store.set_bookmark(db, BOB, "q1", flagged=True)
    store.record_exam(db, user_email=BOB, level="standard", score=20, total=30, duration_s=300)

    store.reset_all(db, ANA)

    assert store.stats_overall(db, ANA)["attempts"] == 0
    assert store.all_flagged(db, ANA) == []
    # Bobovi musí zůstat všechno
    assert store.stats_overall(db, BOB)["attempts"] == 4
    assert store.all_flagged(db, BOB) == ["q1"]
    assert len(store.list_exams(db, BOB)) == 1


# ---------------------------------------------------------------- schéma

def test_kazda_uzivatelska_tabulka_ma_user_email(db):
    """Nová tabulka bez `user_email` by tiše sdílela data mezi lidmi."""
    ocekavane = {
        "attempts", "marathon_runs", "bookmarks",
        "exam_results", "study_state",
    }
    existujici = set(db.table_names())
    chybi = ocekavane - existujici
    assert not chybi, f"tabulky se nevytvořily: {chybi}"
    for t in ocekavane & existujici:
        assert "user_email" in db[t].columns_dict, f"{t} nemá user_email"


def test_uzivatelske_tabulky_maji_index_na_user_email(db):
    """Bez indexu by se s rostoucím počtem uživatelů zpomalovalo všechno."""
    bez_indexu = []
    for t in ("attempts", "marathon_runs", "exam_results", "study_state"):
        if t not in db.table_names():
            continue
        indexovane = {
            col for idx in db[t].indexes for col in idx.columns
        }
        pk = set(db[t].pks)
        if "user_email" not in indexovane | pk:
            bez_indexu.append(t)
    assert not bez_indexu, f"chybí index na user_email: {bez_indexu}"
