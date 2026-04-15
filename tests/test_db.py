"""Smoke testy DB layeru."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Použij dočasnou DB pro každý test."""
    db_path = tmp_path / "test.db"
    # Reset module-level path
    import src.db.store as store
    monkeypatch.setattr(store, "DB_PATH", db_path)
    yield store


def test_db_schema_creates(temp_db):
    db = temp_db.get_db()
    assert {"attempts", "marathon_runs", "bookmarks", "exam_results"}.issubset(set(db.table_names()))


def test_record_attempt_and_stats(temp_db):
    db = temp_db.get_db()
    temp_db.record_attempt(db, question_id="q1", chosen="A", correct="A", mode="random")
    temp_db.record_attempt(db, question_id="q1", chosen="B", correct="A", mode="random")
    temp_db.record_attempt(db, question_id="q2", chosen="C", correct="C", mode="marathon")
    s = temp_db.stats_overall(db)
    assert s["attempts"] == 3
    assert s["correct"] == 2


def test_marathon_lifecycle(temp_db):
    db = temp_db.get_db()
    rid = temp_db.start_marathon(db, total=100)
    assert temp_db.get_active_marathon(db) is not None
    temp_db.update_marathon(db, rid, position=10, correct_inc=8)
    run = temp_db.get_active_marathon(db)
    assert run["position"] == 10
    assert run["correct"] == 8
    temp_db.finish_marathon(db, rid)
    assert temp_db.get_active_marathon(db) is None


def test_bookmark_toggle(temp_db):
    db = temp_db.get_db()
    temp_db.set_bookmark(db, "q1", flagged=True, note="zajímavé")
    bm = temp_db.get_bookmark(db, "q1")
    assert bm["flagged"] == 1
    assert bm["note"] == "zajímavé"
    temp_db.set_bookmark(db, "q1", flagged=False)
    bm2 = temp_db.get_bookmark(db, "q1")
    assert bm2["flagged"] == 0
    assert bm2["note"] == "zajímavé"  # note preserved


def test_question_ids_with_mistakes(temp_db):
    db = temp_db.get_db()
    temp_db.record_attempt(db, question_id="q1", chosen="A", correct="A", mode="random")
    temp_db.record_attempt(db, question_id="q2", chosen="B", correct="A", mode="random")
    temp_db.record_attempt(db, question_id="q3", chosen="C", correct="C", mode="random")
    bad = temp_db.question_ids_with_mistakes(db)
    assert "q2" in bad
    assert "q1" not in bad
    assert "q3" not in bad


def test_exam_passing_thresholds(temp_db):
    db = temp_db.get_db()
    temp_db.record_exam(db, level="standard", score=26, total=30, duration_s=2000)
    temp_db.record_exam(db, level="standard", score=25, total=30, duration_s=2000)
    temp_db.record_exam(db, level="extended", score=28, total=30, duration_s=2000)
    temp_db.record_exam(db, level="extended", score=27, total=30, duration_s=2000)
    rows = temp_db.list_exams(db)
    assert len(rows) == 4
    # rows are ordered by ts DESC; check passed flags by level+score
    for r in rows:
        if r["level"] == "standard":
            assert r["passed"] == (1 if r["score"] >= 26 else 0)
        else:
            assert r["passed"] == (1 if r["score"] >= 28 else 0)


def test_reset_all_clears_everything(temp_db):
    db = temp_db.get_db()
    temp_db.record_attempt(db, question_id="q1", chosen="A", correct="A", mode="random")
    temp_db.start_marathon(db, total=10)
    temp_db.set_bookmark(db, "q1", flagged=True)
    temp_db.record_exam(db, level="standard", score=20, total=30, duration_s=1000)
    temp_db.reset_all(db)
    assert temp_db.stats_overall(db)["attempts"] == 0
    assert temp_db.get_active_marathon(db) is None
    assert not temp_db.all_flagged(db)
    assert not temp_db.list_exams(db)
