"""Performance audit — merime startup, route latence, DB dotazy, DOM size, bundle size."""
from __future__ import annotations

import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_ui_e2e import server, browser  # noqa: F401, E402


# Performance budgets
BUDGETS = {
    "route_latency_ms": 2000,       # HTTP 200 response per route
    "dom_nodes": 3000,               # DOM complexity
    "page_load_wall_s": 4.0,         # Full page network-idle load
    "db_query_ms": 50,               # Single DB query
    "image_load_ms": 500,            # Single image fetch
}

PAGES = ["/", "/marathon", "/random", "/mistakes", "/flagged",
         "/exam", "/export", "/settings", "/srs", "/mastery"]


def test_startup_time():
    """Aplikace musi byt importable + connected k DB do 2s."""
    t0 = time.perf_counter()
    from src.db.questions import load_questions
    from src.db.store import get_db, stats_overall
    qs = load_questions()
    db = get_db()
    stats_overall(db)
    dt = time.perf_counter() - t0
    print(f"\nstartup (imports + load_questions + DB open): {dt*1000:.0f} ms")
    assert dt < 2.0, f"Startup {dt:.2f}s > 2s"
    assert len(qs) == 837


def test_every_route_responds_fast(server):
    """Kazda routa HTTP 200 do <2000 ms."""
    url_base = server
    slow = []
    for p in PAGES:
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(url_base + p, timeout=5) as resp:
                resp.read()
                status = resp.status
        except Exception as e:
            slow.append((p, f"error: {e}"))
            continue
        dt_ms = (time.perf_counter() - t0) * 1000
        print(f"  {p:20s} {status} {dt_ms:.0f} ms")
        if dt_ms > BUDGETS["route_latency_ms"]:
            slow.append((p, f"{dt_ms:.0f}ms > {BUDGETS['route_latency_ms']}ms"))
    assert not slow, f"Pomale routy: {slow}"


def test_dom_size_per_page(server, browser):
    """Kazda stranka pod <3000 DOM uzlu."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    oversized = []
    for p in PAGES:
        page.goto(server + p, wait_until="networkidle")
        page.wait_for_timeout(400)
        n = page.evaluate("() => document.querySelectorAll('*').length")
        print(f"  {p:20s} {n} DOM nodes")
        if n > BUDGETS["dom_nodes"]:
            oversized.append((p, n))
    ctx.close()
    assert not oversized, f"Stranky s prebytek DOM uzlu: {oversized}"


def test_page_load_wall_clock(server, browser):
    """Full page load (vcetne JS) pod 4s na kazde rute."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    slow = []
    for p in PAGES:
        t0 = time.perf_counter()
        page.goto(server + p, wait_until="networkidle")
        dt = time.perf_counter() - t0
        print(f"  {p:20s} {dt:.2f} s")
        if dt > BUDGETS["page_load_wall_s"]:
            slow.append((p, f"{dt:.2f}s"))
    ctx.close()
    assert not slow, f"Pomale page loads: {slow}"


def test_db_query_benchmarks(tmp_path, monkeypatch):
    """Kazdy klicovy DB dotaz pod 50ms i s realistickou historii (1000 pokusu)."""
    import src.db.store as store
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "perf.db")
    db = store.get_db()

    # Naplň: 1000 attempts v 100 ruznych otazkach
    import random as _r
    rng = _r.Random(42)
    for i in range(1000):
        store.record_attempt(
            db,
            question_id=f"q{rng.randint(0, 99)}",
            chosen=rng.choice(["A", "B", "C"]),
            correct="A",
            mode="random",
        )

    # Benchmark klicove dotazy
    results: dict[str, float] = {}

    t0 = time.perf_counter()
    store.stats_overall(db)
    results["stats_overall"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    store.question_ids_with_mistakes(db)
    results["question_ids_with_mistakes"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    store.top_mistakes(db, 20)
    results["top_mistakes"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    store.get_active_marathon(db)
    results["get_active_marathon"] = (time.perf_counter() - t0) * 1000

    print("\nDB queries (s 1000 attempts):")
    slow = []
    for name, ms in sorted(results.items()):
        print(f"  {name:30s} {ms:6.2f} ms")
        if ms > BUDGETS["db_query_ms"]:
            slow.append((name, f"{ms:.1f}ms"))
    assert not slow, f"Pomale DB dotazy: {slow}"


def test_image_load_time(server):
    """Obrazek se musi nacist < 500ms pres HTTP."""
    import json
    qs = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    img_qs = [q for q in qs if q.get("image")][:5]
    slow = []
    for q in img_qs:
        t0 = time.perf_counter()
        with urllib.request.urlopen(f"{server}/{q['image']}", timeout=5) as resp:
            resp.read()
        dt_ms = (time.perf_counter() - t0) * 1000
        print(f"  q{q['pdf_number']:3d}.png {dt_ms:6.1f} ms")
        if dt_ms > BUDGETS["image_load_ms"]:
            slow.append((q["pdf_number"], f"{dt_ms:.0f}ms"))
    assert not slow, f"Pomale image loads: {slow}"


def test_static_asset_sizes():
    """Zkontroluj ze bundled assets nejsou brutalne velke."""
    sizes: dict[str, int] = {}
    for p in (ROOT / "data" / "questions.json",):
        sizes[p.relative_to(ROOT).as_posix()] = p.stat().st_size
    images_dir = ROOT / "images"
    sizes["images/ (71 files)"] = sum(f.stat().st_size for f in images_dir.glob("*.png"))
    print("\nBundled asset sizes:")
    for name, s in sorted(sizes.items()):
        print(f"  {name:40s} {s / 1024:8.1f} KB")
    # Hard limits
    assert sizes["data/questions.json"] < 2_000_000, "questions.json > 2 MB"
    assert sizes["images/ (71 files)"] < 25_000_000, "images total > 25 MB"


def test_cold_cache_lru_cache_speeds_up():
    """load_questions @lru_cache pro opakovana volani neparsuje znovu."""
    from src.db.questions import load_questions
    # Force re-import for clean cache
    load_questions.cache_clear()
    t0 = time.perf_counter()
    load_questions()
    cold_ms = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    for _ in range(100):
        load_questions()
    warm_avg_ms = (time.perf_counter() - t0) * 1000 / 100
    print(f"\nload_questions — cold: {cold_ms:.1f}ms, warm avg (100×): {warm_avg_ms:.3f}ms")
    assert warm_avg_ms < cold_ms, "lru_cache neurychluje opakovana volani"
    assert warm_avg_ms < 0.1, f"warm call {warm_avg_ms:.3f}ms > 0.1ms — lru_cache broken"
