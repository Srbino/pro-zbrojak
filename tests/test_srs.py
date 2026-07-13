"""Testy SRS layeru (multi-user)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fsrs import Rating

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

U = "test@example.cz"
U2 = "druhy@example.cz"


@pytest.fixture
def srs(tmp_path, monkeypatch):
    import src.db.store as store
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test.db")
    db = store.get_db()
    from src.learning import srs as srs_mod
    return srs_mod, db


def test_review_creates_state(srs):
    srs_mod, db = srs
    card = srs_mod.review(db, U, "q1", Rating.Good)
    assert card is not None
    again = srs_mod.get_card(db, U, "q1")
    assert again is not None
    assert again.due == card.due


def test_due_today_returns_due(srs):
    srs_mod, db = srs
    srs_mod.review(db, U, "q1", Rating.Again)
    due = srs_mod.due_today(db, U)
    assert isinstance(due, list)


def test_total_cards_grows(srs):
    srs_mod, db = srs
    assert srs_mod.total_cards(db, U) == 0
    srs_mod.review(db, U, "q1", Rating.Good)
    srs_mod.review(db, U, "q2", Rating.Hard)
    assert srs_mod.total_cards(db, U) == 2


def test_queue_for_unseen_respects_limit(srs):
    srs_mod, db = srs
    all_ids = [f"q{i}" for i in range(10)]
    srs_mod.review(db, U, "q3", Rating.Good)
    queue = srs_mod.queue_for_unseen(db, U, all_ids, limit=5)
    assert "q3" not in queue
    assert len(queue) == 5


def test_srs_user_isolation(srs):
    """SRS karty jednoho uživatele nesmí ovlivnit druhého."""
    srs_mod, db = srs
    srs_mod.review(db, U, "q1", Rating.Good)
    srs_mod.review(db, U, "q2", Rating.Good)
    assert srs_mod.total_cards(db, U) == 2
    assert srs_mod.total_cards(db, U2) == 0
    assert srs_mod.get_card(db, U2, "q1") is None
    # každý uživatel má vlastní kartu pro stejné qid
    srs_mod.review(db, U2, "q1", Rating.Again)
    assert srs_mod.total_cards(db, U2) == 1
    assert srs_mod.total_cards(db, U) == 2
