"""SQLite store using sqlite-utils. Single-user local DB."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

import sqlite_utils

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "stats.db"


def get_db() -> sqlite_utils.Database:
    DB_PATH.parent.mkdir(exist_ok=True)
    db = sqlite_utils.Database(DB_PATH)
    _ensure_schema(db)
    return db


def _ensure_schema(db: sqlite_utils.Database):
    if "attempts" not in db.table_names():
        db["attempts"].create({
            "id": int,
            "question_id": str,
            "chosen": str,
            "correct": str,
            "is_correct": int,
            "confidence": str,
            "mode": str,
            "time_ms": int,
            "ts": int,
        }, pk="id", not_null={"question_id", "chosen", "correct", "is_correct", "mode", "ts"})
        db["attempts"].create_index(["question_id"])
        db["attempts"].create_index(["is_correct"])
        db["attempts"].create_index(["mode"])

    if "marathon_runs" not in db.table_names():
        db["marathon_runs"].create({
            "id": int,
            "started_at": int,
            "finished_at": int,
            "position": int,
            "total": int,
            "correct": int,
            "order_seed": int,  # for reproducible ordering if needed
        }, pk="id", not_null={"started_at", "position", "total"})

    if "bookmarks" not in db.table_names():
        db["bookmarks"].create({
            "question_id": str,
            "flagged": int,
            "note": str,
            "updated_at": int,
        }, pk="question_id", not_null={"question_id", "flagged", "updated_at"})

    if "exam_results" not in db.table_names():
        db["exam_results"].create({
            "id": int,
            "level": str,         # 'standard' | 'extended'
            "score": int,
            "total": int,
            "passed": int,
            "duration_s": int,
            "ts": int,
        }, pk="id", not_null={"level", "score", "total", "passed", "duration_s", "ts"})


# ---------- attempts ----------

def record_attempt(
    db: sqlite_utils.Database,
    *,
    question_id: str,
    chosen: str,
    correct: str,
    mode: str,
    time_ms: int | None = None,
    confidence: str | None = None,
):
    db["attempts"].insert({
        "question_id": question_id,
        "chosen": chosen,
        "correct": correct,
        "is_correct": int(chosen == correct),
        "confidence": confidence,
        "mode": mode,
        "time_ms": time_ms,
        "ts": int(time.time()),
    })


def stats_overall(db: sqlite_utils.Database) -> dict:
    row = next(db.query("SELECT COUNT(*) AS n, SUM(is_correct) AS ok FROM attempts"))
    n = row["n"] or 0
    ok = row["ok"] or 0
    pct = (ok / n * 100) if n else 0.0
    return {"attempts": n, "correct": ok, "pct": round(pct, 1)}


def stats_per_section(db: sqlite_utils.Database, questions: list[dict]) -> dict[str, dict]:
    """Returns {section: {attempts, correct, pct}} based on attempts joined with questions in memory."""
    qid_to_section = {q["id"]: q.get("section") or "unknown" for q in questions}
    out: dict[str, dict] = {}
    for row in db.query("SELECT question_id, is_correct FROM attempts"):
        sec = qid_to_section.get(row["question_id"], "unknown")
        bucket = out.setdefault(sec, {"attempts": 0, "correct": 0})
        bucket["attempts"] += 1
        bucket["correct"] += row["is_correct"]
    for sec, b in out.items():
        b["pct"] = round(b["correct"] / b["attempts"] * 100, 1) if b["attempts"] else 0.0
    return out


def top_mistakes(db: sqlite_utils.Database, limit: int = 20) -> list[dict]:
    sql = """
        SELECT question_id,
               COUNT(*) AS attempts,
               SUM(is_correct) AS correct,
               (COUNT(*) - SUM(is_correct)) AS wrong
        FROM attempts
        GROUP BY question_id
        HAVING wrong > 0
        ORDER BY wrong DESC, attempts DESC
        LIMIT ?
    """
    return list(db.query(sql, [limit]))


def question_ids_with_mistakes(db: sqlite_utils.Database) -> list[str]:
    """All question IDs where user has at least one wrong attempt."""
    sql = """
        SELECT question_id, COUNT(*) - SUM(is_correct) AS wrong
        FROM attempts
        GROUP BY question_id
        HAVING wrong > 0
        ORDER BY wrong DESC
    """
    return [r["question_id"] for r in db.query(sql)]


# ---------- marathon ----------

def get_active_marathon(db: sqlite_utils.Database) -> dict | None:
    rows = list(db.query(
        "SELECT * FROM marathon_runs WHERE finished_at IS NULL ORDER BY started_at DESC LIMIT 1"
    ))
    return rows[0] if rows else None


def start_marathon(db: sqlite_utils.Database, total: int) -> int:
    pk = db["marathon_runs"].insert({
        "started_at": int(time.time()),
        "finished_at": None,
        "position": 0,
        "total": total,
        "correct": 0,
        "order_seed": 0,
    }).last_pk
    return pk


def update_marathon(db: sqlite_utils.Database, run_id: int, *, position: int, correct_inc: int = 0):
    cur = db["marathon_runs"].get(run_id)
    db["marathon_runs"].update(run_id, {
        "position": position,
        "correct": (cur["correct"] or 0) + correct_inc,
    })


def finish_marathon(db: sqlite_utils.Database, run_id: int):
    db["marathon_runs"].update(run_id, {"finished_at": int(time.time())})


def list_marathons(db: sqlite_utils.Database) -> list[dict]:
    return list(db.query("SELECT * FROM marathon_runs ORDER BY started_at DESC"))


# ---------- bookmarks ----------

def get_bookmark(db: sqlite_utils.Database, question_id: str) -> dict | None:
    try:
        return db["bookmarks"].get(question_id)
    except sqlite_utils.db.NotFoundError:
        return None


def set_bookmark(db: sqlite_utils.Database, question_id: str, *, flagged: bool | None = None, note: str | None = None):
    cur = get_bookmark(db, question_id) or {"question_id": question_id, "flagged": 0, "note": ""}
    if flagged is not None:
        cur["flagged"] = int(flagged)
    if note is not None:
        cur["note"] = note
    cur["updated_at"] = int(time.time())
    db["bookmarks"].insert(cur, pk="question_id", replace=True)


def all_flagged(db: sqlite_utils.Database) -> list[str]:
    return [r["question_id"] for r in db.query("SELECT question_id FROM bookmarks WHERE flagged=1")]


# ---------- exam ----------

def record_exam(
    db: sqlite_utils.Database,
    *,
    level: str,
    score: int,
    total: int,
    duration_s: int,
):
    threshold = 26 if level == "standard" else 28
    db["exam_results"].insert({
        "level": level,
        "score": score,
        "total": total,
        "passed": int(score >= threshold),
        "duration_s": duration_s,
        "ts": int(time.time()),
    })


def list_exams(db: sqlite_utils.Database) -> list[dict]:
    return list(db.query("SELECT * FROM exam_results ORDER BY ts DESC"))


# ---------- maintenance ----------

def reset_all(db: sqlite_utils.Database):
    """Smaze VSECHNA user data (attempts, marathons, bookmarks, exam results, SRS state).

    Pouziva raw SQL + explicit commit, protoze sqlite_utils.Table.delete_where()
    neni spolehlive persistovano na disk v nasi konfiguraci.
    """
    tables = ("attempts", "marathon_runs", "bookmarks", "exam_results", "srs_state")
    existing = set(db.table_names())
    for t in tables:
        if t in existing:
            db.conn.execute(f"DELETE FROM {t}")
    db.conn.commit()
