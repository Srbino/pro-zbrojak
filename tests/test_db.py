"""Smoke testy DB layeru (multi-user)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

U = "test@example.cz"       # výchozí testovací uživatel
U2 = "druhy@example.cz"     # druhý uživatel (izolace)


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Použij dočasnou DB pro každý test."""
    db_path = tmp_path / "test.db"
    import src.db.store as store
    monkeypatch.setattr(store, "DB_PATH", db_path)
    yield store


def test_db_schema_creates(temp_db):
    db = temp_db.get_db()
    assert {"users", "attempts", "marathon_runs", "bookmarks", "exam_results"}.issubset(
        set(db.table_names())
    )


def test_record_attempt_and_stats(temp_db):
    db = temp_db.get_db()
    temp_db.record_attempt(db, user_email=U, question_id="q1", chosen="A", correct="A", mode="random")
    temp_db.record_attempt(db, user_email=U, question_id="q1", chosen="B", correct="A", mode="random")
    temp_db.record_attempt(db, user_email=U, question_id="q2", chosen="C", correct="C", mode="marathon")
    s = temp_db.stats_overall(db, U)
    assert s["attempts"] == 3
    assert s["correct"] == 2


def test_marathon_lifecycle(temp_db):
    db = temp_db.get_db()
    rid = temp_db.start_marathon(db, U, total=100)
    assert temp_db.get_active_marathon(db, U) is not None
    temp_db.update_marathon(db, rid, position=10, correct_inc=8)
    run = temp_db.get_active_marathon(db, U)
    assert run["position"] == 10
    assert run["correct"] == 8
    temp_db.finish_marathon(db, rid)
    assert temp_db.get_active_marathon(db, U) is None


def test_bookmark_toggle(temp_db):
    db = temp_db.get_db()
    temp_db.set_bookmark(db, U, "q1", flagged=True, note="zajímavé")
    bm = temp_db.get_bookmark(db, U, "q1")
    assert bm["flagged"] == 1
    assert bm["note"] == "zajímavé"
    temp_db.set_bookmark(db, U, "q1", flagged=False)
    bm2 = temp_db.get_bookmark(db, U, "q1")
    assert bm2["flagged"] == 0
    assert bm2["note"] == "zajímavé"  # note preserved


def test_question_ids_with_mistakes(temp_db):
    db = temp_db.get_db()
    temp_db.record_attempt(db, user_email=U, question_id="q1", chosen="A", correct="A", mode="random")
    temp_db.record_attempt(db, user_email=U, question_id="q2", chosen="B", correct="A", mode="random")
    temp_db.record_attempt(db, user_email=U, question_id="q3", chosen="C", correct="C", mode="random")
    bad = temp_db.question_ids_with_mistakes(db, U)
    assert "q2" in bad
    assert "q1" not in bad
    assert "q3" not in bad


def test_exam_passing_thresholds(temp_db):
    db = temp_db.get_db()
    temp_db.record_exam(db, user_email=U, level="standard", score=26, total=30, duration_s=2000)
    temp_db.record_exam(db, user_email=U, level="standard", score=25, total=30, duration_s=2000)
    temp_db.record_exam(db, user_email=U, level="extended", score=28, total=30, duration_s=2000)
    temp_db.record_exam(db, user_email=U, level="extended", score=27, total=30, duration_s=2000)
    rows = temp_db.list_exams(db, U)
    assert len(rows) == 4
    for r in rows:
        if r["level"] == "standard":
            assert r["passed"] == (1 if r["score"] >= 26 else 0)
        else:
            assert r["passed"] == (1 if r["score"] >= 28 else 0)


def test_reset_all_clears_only_my_data(temp_db):
    db = temp_db.get_db()
    temp_db.record_attempt(db, user_email=U, question_id="q1", chosen="A", correct="A", mode="random")
    temp_db.start_marathon(db, U, total=10)
    temp_db.set_bookmark(db, U, "q1", flagged=True)
    temp_db.record_exam(db, user_email=U, level="standard", score=20, total=30, duration_s=1000)
    # druhý uživatel má vlastní data
    temp_db.record_attempt(db, user_email=U2, question_id="q9", chosen="A", correct="A", mode="random")

    temp_db.reset_all(db, U)
    assert temp_db.stats_overall(db, U)["attempts"] == 0
    assert temp_db.get_active_marathon(db, U) is None
    assert not temp_db.all_flagged(db, U)
    assert not temp_db.list_exams(db, U)
    # data druhého uživatele zůstala nedotčená
    assert temp_db.stats_overall(db, U2)["attempts"] == 1


def test_user_isolation(temp_db):
    """Data jednoho uživatele nesmí být vidět u druhého."""
    db = temp_db.get_db()
    temp_db.record_attempt(db, user_email=U, question_id="q1", chosen="A", correct="B", mode="random")
    temp_db.set_bookmark(db, U, "q1", flagged=True)
    temp_db.record_exam(db, user_email=U, level="standard", score=27, total=30, duration_s=500)

    assert temp_db.stats_overall(db, U2)["attempts"] == 0
    assert temp_db.question_ids_with_mistakes(db, U2) == []
    assert temp_db.all_flagged(db, U2) == []
    assert temp_db.list_exams(db, U2) == []
    # a naopak U vidí svoje
    assert temp_db.all_flagged(db, U) == ["q1"]
    assert temp_db.question_ids_with_mistakes(db, U) == ["q1"]


def test_ensure_user_and_admin(temp_db):
    db = temp_db.get_db()
    temp_db.ensure_user(db, U, "Test", False)
    temp_db.ensure_user(db, U2, "Admin", True)
    users = {u["email"]: u for u in temp_db.list_users(db)}
    assert users[U]["is_admin"] == 0
    assert users[U2]["is_admin"] == 1
