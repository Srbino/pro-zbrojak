"""Marathon — sekvencni pruchod vsech otazek s perzistenci pozice."""
from __future__ import annotations

import time

from nicegui import ui

from src.db.questions import load_questions
from src.db.store import (
    get_db, record_attempt, get_active_marathon, start_marathon,
    update_marathon, finish_marathon, list_marathons,
)
from src.ui.components import (
    hero_result, back_home_button, is_flagged, toggle_flagged,
)
from src.ui.icons import I
from src.ui.layout import page_shell
from src.ui.quiz import QuizCard


@ui.page("/marathon")
def marathon_page():
    db = get_db()
    questions = load_questions()
    sorted_q = sorted(questions, key=lambda q: q["pdf_number"])

    state = {"run": get_active_marathon(db), "container": None}

    def render():
        state["container"].clear()
        with state["container"]:
            run = state["run"]
            if run is None:
                _marathon_intro(sorted_q, db, _start_new)
                return
            pos = run["position"]
            if pos >= run["total"]:
                finish_marathon(db, run["id"])
                pct = round(run["correct"] / run["total"] * 100, 1)
                hero_result(
                    passed=True,
                    title="Marathon dokončen!",
                    subtitle=f"Správně {run['correct']}/{run['total']} ({pct} %)",
                    icon_name="trophy",
                )
                with ui.row().classes("zp-row zp-gap-sm zp-mt-lg").style("justify-content: center;"):
                    ui.button("Začít znovu", icon=I["refresh"], on_click=_start_new).props(
                        "color=primary unelevated"
                    )
                    back_home_button()
                return
            q = sorted_q[pos]
            card = QuizCard(
                q,
                instant_feedback=True,
                progress_label=f"Otázka {pos+1} / {run['total']}   ·   správně {run['correct']}",
                progress_ratio=pos / run["total"],
                is_bookmarked=is_flagged(db, q["id"]),
                on_answer=lambda chosen, ms, q=q: _on_answer(q, chosen, ms),
                on_next=_advance,
                on_bookmark_toggle=lambda q=q: toggle_flagged(db, q["id"]),
            )
            card.render()

    def _start_new():
        start_marathon(db, len(sorted_q))
        state["run"] = get_active_marathon(db)
        render()

    def _on_answer(q, chosen, ms):
        record_attempt(db, question_id=q["id"], chosen=chosen, correct=q["correct"],
                       mode="marathon", time_ms=ms)
        if chosen == q["correct"]:
            update_marathon(db, state["run"]["id"], position=state["run"]["position"], correct_inc=1)
            state["run"] = get_active_marathon(db)

    def _advance():
        new_pos = state["run"]["position"] + 1
        update_marathon(db, state["run"]["id"], position=new_pos)
        state["run"] = get_active_marathon(db)
        render()

    with page_shell("Marathon", active_path="/marathon"):
        state["container"] = ui.column().classes("w-full")
        render()


def _marathon_intro(sorted_q, db, start_cb):
    ui.label("Marathon").classes("zp-display")
    ui.label(
        f"Sekvenční průchod všech {len(sorted_q)} otázek po pořadí podle PDF. "
        "Pozici si aplikace zapamatuje — můžeš kdykoli zavřít a pokračovat."
    ).classes("zp-body zp-prose zp-mb-lg")

    history = list_marathons(db)
    if history:
        with ui.element("div").classes("zp-card zp-mb-md"):
            ui.label("Předchozí běhy").classes("zp-h3 zp-mb-sm")
            for r in history[:5]:
                ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(r["started_at"]))
                end = "běží" if r["finished_at"] is None else "dokončen"
                pct = round(r["correct"] / max(1, r["position"]) * 100, 1) if r["position"] else 0
                with ui.row().classes("zp-row zp-nowrap w-full").style(
                    "padding: .35rem 0; border-bottom: 1px solid var(--zp-border);"
                ):
                    ui.label(ts).classes("zp-body-sm zp-mono").style("width: 160px;")
                    variant = "success" if end == "dokončen" else "warning"
                    ui.html(f'<span class="zp-badge {variant}">{end}</span>')
                    ui.label(f"{r['position']}/{r['total']}").classes("zp-body-sm").style(
                        "margin-left: 1rem; flex: 1;"
                    )
                    ui.label(f"{pct} %").classes("zp-body-sm zp-mono").style("font-weight: 600;")

    ui.button("Začít nový marathon", icon=I["play"], on_click=start_cb).props(
        "size=lg color=primary unelevated"
    )
