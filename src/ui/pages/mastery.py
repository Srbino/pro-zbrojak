"""Mastery podle oblasti — trenink dokud nezvladnes 90% na poslednich 30."""
from __future__ import annotations

from collections import defaultdict

from nicegui import ui

from src.db.questions import load_questions
from src.db.store import get_db, record_attempt
from src.ui.components import (
    SECTION_LABEL, QuizSession, progress_bar, query_str,
)
from src.ui.icons import I
from src.ui.layout import page_shell


@ui.page("/mastery")
def mastery_page():
    db = get_db()
    questions = load_questions()

    with page_shell("Mastery", active_path="/mastery"):
        ui.label("Mastery podle oblasti").classes("zp-display")
        ui.label(
            "Procvičuj oblast dokud nedosáhneš ≥ 90 % úspěšnosti na posledních 30 pokusech."
        ).classes("zp-body zp-prose zp-mb-lg")

        recent_per_sec: dict[str, list[int]] = defaultdict(list)
        qid_to_sec = {q["id"]: q.get("section") for q in questions}
        rows = list(db.query("SELECT question_id, is_correct FROM attempts ORDER BY ts DESC"))
        for r in rows:
            sec = qid_to_sec.get(r["question_id"])
            if sec and len(recent_per_sec[sec]) < 30:
                recent_per_sec[sec].append(r["is_correct"])

        with ui.element("div").classes("zp-grid-2"):
            for sec, label in SECTION_LABEL.items():
                pool_n = sum(1 for q in questions if q.get("section") == sec)
                if pool_n == 0:
                    continue
                recent = recent_per_sec.get(sec, [])
                if recent:
                    pct = round(sum(recent) / len(recent) * 100, 1)
                    mastered = pct >= 90 and len(recent) >= 30
                    sample_factor = min(len(recent) / 30.0, 1.0)
                    display_ratio = pct * sample_factor / 100.0
                else:
                    pct = 0
                    display_ratio = 0
                    mastered = False

                with ui.element("div").classes("zp-card"):
                    with ui.row().classes("zp-row-between zp-nowrap w-full"):
                        ui.label(label).classes("zp-h3")
                        if mastered:
                            ui.html('<span class="zp-badge success">zvládnuto</span>')
                        elif len(recent) >= 10 and pct >= 75:
                            ui.html('<span class="zp-badge warning">blízko</span>')
                    variant = "success" if mastered else ("primary" if pct >= 65 else "danger" if recent else "primary")
                    progress_bar(display_ratio, variant=variant)
                    with ui.row().classes("zp-row-between zp-nowrap w-full zp-mt-sm"):
                        if recent:
                            detail = f"{pool_n} otázek  ·  {pct} % na posledních {len(recent)}/30"
                        else:
                            detail = f"{pool_n} otázek  ·  zatím bez pokusu"
                        ui.label(detail).classes("zp-body-sm")
                        ui.button("Trénovat", icon=I["next"],
                                  on_click=lambda s=sec: ui.navigate.to(f"/mastery/run?section={s}")).props(
                            "flat dense color=primary"
                        )


@ui.page("/mastery/run")
def mastery_run_page():
    section = query_str("section", "pravo")
    pool = [q for q in load_questions() if q.get("section") == section]
    title = f"Mastery — {SECTION_LABEL.get(section, section)}"
    db = get_db()

    def _rec(qid, chosen, correct, ms):
        record_attempt(db, question_id=qid, chosen=chosen, correct=correct,
                       mode="mastery", time_ms=ms)

    with page_shell(title, active_path="/mastery"):
        QuizSession(
            pool=pool, mode="mastery",
            empty_icon="info", empty_heading="Prázdná oblast",
            empty_subtitle="V této oblasti nejsou otázky.",
            on_record=_rec,
        ).run()
