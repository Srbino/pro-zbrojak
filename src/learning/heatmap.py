"""Aktivitni heatmapa za poslednich 90 dni."""
from __future__ import annotations

import datetime as dt
import time
from collections import Counter

import sqlite_utils


def daily_counts(db: sqlite_utils.Database, user_email: str, days: int = 90) -> dict[str, int]:
    """Vrati {ISO date: pocet pokusu} za poslednich `days` dni pro daného uživatele."""
    cutoff = int(time.time()) - days * 86400
    rows = db.query("SELECT ts FROM attempts WHERE user_email=? AND ts >= ?", [user_email, cutoff])
    c: Counter = Counter()
    for r in rows:
        d = dt.date.fromtimestamp(r["ts"]).isoformat()
        c[d] += 1
    # Fill empty days
    out: dict[str, int] = {}
    today = dt.date.today()
    for i in range(days):
        d = (today - dt.timedelta(days=days - 1 - i)).isoformat()
        out[d] = c.get(d, 0)
    return out


def current_streak(db: sqlite_utils.Database, user_email: str) -> int:
    """Kolik dní v řadě se odpovídalo, včetně dneška.

    Dnešek se nezapočítává jako přetržení — série drží až do konce dne, jinak
    by ráno každý den ukazovala nulu.
    """
    counts = daily_counts(db, user_email, days=400)
    today = dt.date.today()
    streak = 0
    for i in range(len(counts)):
        day = (today - dt.timedelta(days=i)).isoformat()
        if counts.get(day, 0) > 0:
            streak += 1
        elif i > 0:  # včerejšek a starší už sérii přetrhne
            break
    return streak
