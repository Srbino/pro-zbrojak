"""SQLite store using sqlite-utils. Multi-user (per e-mail) local DB.

Každý řádek dat (attempts, marathon, bookmarks, exam, SRS) nese `user_email`.
Identita přichází z Cloudflare Access (viz `src/auth.py`); na LAN z fallback loginu.
"""
from __future__ import annotations

import os
import time

import sqlite_utils

from src.paths import DB_PATH

# Vlastník, kterému se při migraci přiřadí stará „single-user" data.
_LEGACY_OWNER = (
    os.environ.get("PRO_ZBROJAK_ADMINS", "srba@unify.cz").split(",")[0] or "srba@unify.cz"
).strip().lower()


def get_db() -> sqlite_utils.Database:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite_utils.Database(DB_PATH)
    _ensure_schema(db)
    _migrate_multiuser(db)
    return db


def _ensure_schema(db: sqlite_utils.Database):
    if "users" not in db.table_names():
        db["users"].create({
            "email": str,
            "name": str,
            "is_admin": int,
            "created_at": int,
            "last_seen": int,
        }, pk="email", not_null={"email", "name"})

    if "attempts" not in db.table_names():
        db["attempts"].create({
            "id": int,
            "user_email": str,
            "question_id": str,
            "chosen": str,
            "correct": str,
            "is_correct": int,
            "confidence": str,
            "mode": str,
            "time_ms": int,
            "ts": int,
        }, pk="id", not_null={"user_email", "question_id", "chosen", "correct", "is_correct", "mode", "ts"})
        db["attempts"].create_index(["user_email"])
        db["attempts"].create_index(["question_id"])
        db["attempts"].create_index(["is_correct"])
        db["attempts"].create_index(["mode"])

    if "marathon_runs" not in db.table_names():
        db["marathon_runs"].create({
            "id": int,
            "user_email": str,
            "started_at": int,
            "finished_at": int,
            "position": int,
            "total": int,
            "correct": int,
            "order_seed": int,
        }, pk="id", not_null={"user_email", "started_at", "position", "total"})
        db["marathon_runs"].create_index(["user_email"])

    if "bookmarks" not in db.table_names():
        db["bookmarks"].create({
            "user_email": str,
            "question_id": str,
            "flagged": int,
            "note": str,
            "updated_at": int,
        }, pk=("user_email", "question_id"), not_null={"user_email", "question_id", "flagged", "updated_at"})

    if "exam_results" not in db.table_names():
        db["exam_results"].create({
            "id": int,
            "user_email": str,
            "level": str,
            "score": int,
            "total": int,
            "passed": int,
            "duration_s": int,
            "ts": int,
        }, pk="id", not_null={"user_email", "level", "score", "total", "passed", "duration_s", "ts"})
        db["exam_results"].create_index(["user_email"])


def _migrate_multiuser(db: sqlite_utils.Database):
    """Doplní `user_email` do starých single-user tabulek a přiřadí je vlastníkovi."""
    changed = False

    # Jednoduché tabulky s pk=id → jen přidat sloupec + backfill.
    for t in ("attempts", "marathon_runs", "exam_results"):
        if t in db.table_names() and "user_email" not in db[t].columns_dict:
            db[t].add_column("user_email", str)
            db.conn.execute(f"UPDATE {t} SET user_email=? WHERE user_email IS NULL", [_LEGACY_OWNER])
            db[t].create_index(["user_email"], if_not_exists=True)
            changed = True

    # bookmarks: pk byl question_id → přidat user_email a překlopit na složený pk.
    if "bookmarks" in db.table_names() and "user_email" not in db["bookmarks"].columns_dict:
        db["bookmarks"].add_column("user_email", str)
        db.conn.execute("UPDATE bookmarks SET user_email=? WHERE user_email IS NULL", [_LEGACY_OWNER])
        db.conn.commit()
        db["bookmarks"].transform(pk=("user_email", "question_id"))
        changed = True

    if changed:
        db.conn.commit()


def ensure_user(db: sqlite_utils.Database, email: str, name: str, is_admin: bool):
    """Upsert uživatele (auto-provisioning — Access už ověřil, že je oprávněný)."""
    now = int(time.time())
    existing = None
    try:
        existing = db["users"].get(email)
    except sqlite_utils.db.NotFoundError:
        pass
    row = {
        "email": email,
        "name": name,
        "is_admin": int(is_admin),
        "created_at": existing["created_at"] if existing else now,
        "last_seen": now,
    }
    db["users"].insert(row, pk="email", replace=True)


def list_users(db: sqlite_utils.Database) -> list[dict]:
    return list(db.query("SELECT * FROM users ORDER BY is_admin DESC, name ASC"))


# ---------- attempts ----------

def record_attempt(
    db: sqlite_utils.Database,
    *,
    user_email: str,
    question_id: str,
    chosen: str,
    correct: str,
    mode: str,
    time_ms: int | None = None,
    confidence: str | None = None,
):
    db["attempts"].insert({
        "user_email": user_email,
        "question_id": question_id,
        "chosen": chosen,
        "correct": correct,
        "is_correct": int(chosen == correct),
        "confidence": confidence,
        "mode": mode,
        "time_ms": time_ms,
        "ts": int(time.time()),
    })


def stats_overall(db: sqlite_utils.Database, user_email: str) -> dict:
    row = next(db.query(
        "SELECT COUNT(*) AS n, SUM(is_correct) AS ok FROM attempts WHERE user_email=?",
        [user_email],
    ))
    n = row["n"] or 0
    ok = row["ok"] or 0
    pct = (ok / n * 100) if n else 0.0
    return {"attempts": n, "correct": ok, "pct": round(pct, 1)}


def stats_per_section(db: sqlite_utils.Database, questions: list[dict], user_email: str) -> dict[str, dict]:
    """Returns {section: {attempts, correct, pct}} pro daného uživatele."""
    qid_to_section = {q["id"]: q.get("section") or "unknown" for q in questions}
    out: dict[str, dict] = {}
    for row in db.query("SELECT question_id, is_correct FROM attempts WHERE user_email=?", [user_email]):
        sec = qid_to_section.get(row["question_id"], "unknown")
        bucket = out.setdefault(sec, {"attempts": 0, "correct": 0})
        bucket["attempts"] += 1
        bucket["correct"] += row["is_correct"]
    for sec, b in out.items():
        b["pct"] = round(b["correct"] / b["attempts"] * 100, 1) if b["attempts"] else 0.0
    return out


def top_mistakes(db: sqlite_utils.Database, user_email: str, limit: int = 20) -> list[dict]:
    sql = """
        SELECT question_id,
               COUNT(*) AS attempts,
               SUM(is_correct) AS correct,
               (COUNT(*) - SUM(is_correct)) AS wrong
        FROM attempts
        WHERE user_email=?
        GROUP BY question_id
        HAVING wrong > 0
        ORDER BY wrong DESC, attempts DESC
        LIMIT ?
    """
    return list(db.query(sql, [user_email, limit]))


def question_ids_with_mistakes(db: sqlite_utils.Database, user_email: str) -> list[str]:
    """Všechna qid, kde má uživatel aspoň jeden špatný pokus."""
    sql = """
        SELECT question_id, COUNT(*) - SUM(is_correct) AS wrong
        FROM attempts
        WHERE user_email=?
        GROUP BY question_id
        HAVING wrong > 0
        ORDER BY wrong DESC
    """
    return [r["question_id"] for r in db.query(sql, [user_email])]


# ---------- marathon ----------

def get_active_marathon(db: sqlite_utils.Database, user_email: str) -> dict | None:
    rows = list(db.query(
        "SELECT * FROM marathon_runs WHERE user_email=? AND finished_at IS NULL "
        "ORDER BY started_at DESC LIMIT 1",
        [user_email],
    ))
    return rows[0] if rows else None


def start_marathon(db: sqlite_utils.Database, user_email: str, total: int) -> int:
    pk = db["marathon_runs"].insert({
        "user_email": user_email,
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


def list_marathons(db: sqlite_utils.Database, user_email: str) -> list[dict]:
    return list(db.query(
        "SELECT * FROM marathon_runs WHERE user_email=? ORDER BY started_at DESC",
        [user_email],
    ))


# ---------- bookmarks ----------

def get_bookmark(db: sqlite_utils.Database, user_email: str, question_id: str) -> dict | None:
    rows = list(db.query(
        "SELECT * FROM bookmarks WHERE user_email=? AND question_id=?",
        [user_email, question_id],
    ))
    return rows[0] if rows else None


def set_bookmark(db: sqlite_utils.Database, user_email: str, question_id: str, *,
                 flagged: bool | None = None, note: str | None = None):
    cur = get_bookmark(db, user_email, question_id) or {
        "user_email": user_email, "question_id": question_id, "flagged": 0, "note": "",
    }
    if flagged is not None:
        cur["flagged"] = int(flagged)
    if note is not None:
        cur["note"] = note
    cur["updated_at"] = int(time.time())
    db["bookmarks"].insert(cur, pk=("user_email", "question_id"), replace=True)


def all_flagged(db: sqlite_utils.Database, user_email: str) -> list[str]:
    return [r["question_id"] for r in db.query(
        "SELECT question_id FROM bookmarks WHERE user_email=? AND flagged=1", [user_email]
    )]


# ---------- exam ----------

def record_exam(
    db: sqlite_utils.Database,
    *,
    user_email: str,
    level: str,
    score: int,
    total: int,
    duration_s: int,
):
    threshold = 26 if level == "standard" else 28
    db["exam_results"].insert({
        "user_email": user_email,
        "level": level,
        "score": score,
        "total": total,
        "passed": int(score >= threshold),
        "duration_s": duration_s,
        "ts": int(time.time()),
    })


def list_exams(db: sqlite_utils.Database, user_email: str) -> list[dict]:
    return list(db.query(
        "SELECT * FROM exam_results WHERE user_email=? ORDER BY ts DESC", [user_email]
    ))


# ---------- maintenance ----------

def reset_all(db: sqlite_utils.Database, user_email: str):
    """Smaže data JEN daného uživatele (attempts, marathon, bookmarks, exam, SRS)."""
    tables = ("attempts", "marathon_runs", "bookmarks", "exam_results", "srs_state")
    existing = set(db.table_names())
    for t in tables:
        if t in existing:
            db.conn.execute(f"DELETE FROM {t} WHERE user_email=?", [user_email])
    db.conn.commit()
