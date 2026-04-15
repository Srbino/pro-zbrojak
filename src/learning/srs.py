"""SRS (Spaced Repetition System) — wrapper kolem knihovny `fsrs`."""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import sqlite_utils
from fsrs import Card, Rating, Scheduler, State

ROOT = Path(__file__).resolve().parent.parent.parent

# Mapping uzivatelske volby v UI → FSRS Rating
RATING_LABELS = {
    Rating.Again: "Znovu",
    Rating.Hard: "Tezke",
    Rating.Good: "Dobre",
    Rating.Easy: "Snadne",
}


def _ensure_schema(db: sqlite_utils.Database):
    if "srs_state" not in db.table_names():
        db["srs_state"].create({
            "question_id": str,
            "card_json": str,   # JSON-serialized Card object
            "next_due": int,
            "reps": int,
            "lapses": int,
            "last_review": int,
        }, pk="question_id")
        db["srs_state"].create_index(["next_due"])


def _scheduler() -> Scheduler:
    return Scheduler()


def _serialize_card(card: Card) -> str:
    return json.dumps(card.to_dict(), default=str)


def _deserialize_card(s: str) -> Card:
    return Card.from_dict(json.loads(s))


def get_card(db: sqlite_utils.Database, question_id: str) -> Card | None:
    _ensure_schema(db)
    try:
        row = db["srs_state"].get(question_id)
    except sqlite_utils.db.NotFoundError:
        return None
    return _deserialize_card(row["card_json"])


def review(db: sqlite_utils.Database, question_id: str, rating: Rating) -> Card:
    """Zaregistruje review podle FSRS, ulozi novy stav a vrati updatovanou Card."""
    _ensure_schema(db)
    sch = _scheduler()
    card = get_card(db, question_id) or Card()
    now = dt.datetime.now(dt.timezone.utc)
    card, _log = sch.review_card(card, rating, now)
    row = {
        "question_id": question_id,
        "card_json": _serialize_card(card),
        "next_due": int(card.due.timestamp()),
        "reps": _safe_attr(card, "reps", 0),
        "lapses": _safe_attr(card, "lapses", 0),
        "last_review": int(now.timestamp()),
    }
    db["srs_state"].insert(row, pk="question_id", replace=True)
    return card


def _safe_attr(obj, name, default):
    return getattr(obj, name, default)


def due_today(db: sqlite_utils.Database, *, limit: int = 30) -> list[str]:
    """Vrati IDcka otazek, kterym dnes vyprsi review (next_due <= now)."""
    _ensure_schema(db)
    now = int(time.time())
    rows = db.query(
        "SELECT question_id FROM srs_state WHERE next_due <= ? ORDER BY next_due ASC LIMIT ?",
        [now, limit],
    )
    return [r["question_id"] for r in rows]


def upcoming_count(db: sqlite_utils.Database, days: int = 1) -> int:
    """Pocet otazek, ktere vyprsi v nasledujicich N dnech."""
    _ensure_schema(db)
    horizon = int(time.time()) + days * 86400
    row = next(db.query("SELECT COUNT(*) AS n FROM srs_state WHERE next_due <= ?", [horizon]))
    return row["n"] or 0


def total_cards(db: sqlite_utils.Database) -> int:
    _ensure_schema(db)
    row = next(db.query("SELECT COUNT(*) AS n FROM srs_state"))
    return row["n"] or 0


def queue_for_unseen(db: sqlite_utils.Database, all_question_ids: list[str], limit: int = 20) -> list[str]:
    """Vrati IDcka otazek, ktere uzivatel jeste nikdy neoznackoval (nemaji srs zaznam)."""
    _ensure_schema(db)
    seen = {r["question_id"] for r in db["srs_state"].rows_where(select="question_id")}
    return [qid for qid in all_question_ids if qid not in seen][:limit]
