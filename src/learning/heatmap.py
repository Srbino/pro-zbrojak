"""Aktivitni heatmapa za poslednich 90 dni."""
from __future__ import annotations

import datetime as dt
import time
from collections import Counter

import sqlite_utils


def daily_counts(db: sqlite_utils.Database, days: int = 90) -> dict[str, int]:
    """Vrati {ISO date: pocet pokusu} za poslednich `days` dni."""
    cutoff = int(time.time()) - days * 86400
    rows = db.query("SELECT ts FROM attempts WHERE ts >= ?", [cutoff])
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
