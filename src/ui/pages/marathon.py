"""Marathon — sekvencni pruchod vsech otazek s perzistenci pozice."""
from __future__ import annotations

import time

from nicegui import ui

from src.auth import require_login
from src.db.questions import load_questions
from src.db.store import (
    finish_marathon,
    get_active_marathon,
    get_db,
    last_answers,
    list_marathons,
    record_attempt,
    start_marathon,
    update_marathon,
)
from src.ui.components import (
    QuestionNavigator,
    back_home_button,
    hero_result,
    is_flagged,
    toggle_flagged,
)
from src.ui.icons import I
from src.ui.layout import page_shell
from src.ui.quiz import QuizCard


@ui.page("/marathon")
def marathon_page():
    user = require_login()
    if user is None:
        return
    db = get_db()
    questions = load_questions()
    sorted_q = sorted(questions, key=lambda q: q["pdf_number"])
    qmap = {q["id"]: q for q in sorted_q}

    # `review` drží pozici prohlížené otázky, nebo None = jsme na aktuální.
    # Listování zpátky nic nezapisuje, jen ukazuje, co jsi tehdy odpověděl.
    state = {"run": get_active_marathon(db, user.email), "container": None, "review": None}

    def render():
        state["container"].clear()
        with state["container"]:
            run = state["run"]
            if run is None:
                _marathon_intro(sorted_q, db, user.email, _start_new)
                return
            if state["review"] is not None:
                _render_review(run)
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
            with ui.element("div").classes("zp-quiz-with-nav"):
                _navigator(pos).render()
                with ui.element("div").classes("zp-quiz-main"):
                    QuizCard(
                        q,
                        user_email=user.email,
                        instant_feedback=True,
                        progress_label=(
                            f"Otázka {pos+1} / {run['total']}"
                            f"   ·   správně {run['correct']}"
                        ),
                        progress_ratio=pos / run["total"],
                        is_bookmarked=is_flagged(db, user.email, q["id"]),
                        on_answer=lambda chosen, ms, q=q: _on_answer(q, chosen, ms),
                        on_next=_advance,
                        on_bookmark_toggle=lambda q=q: toggle_flagged(db, user.email, q["id"]),
                    ).render()
                    if pos > 0:
                        with ui.row().classes("w-full zp-mt-md").style(
                            "justify-content: center;"
                        ):
                            ui.button(
                                "Zpět na předchozí", icon=I["back"],
                                on_click=lambda: _review(pos - 1),
                            ).props("flat").classes("zp-review-enter")

    def _navigator(current_pos: int) -> QuestionNavigator:
        """Seznam otázek vlevo. Obarvený podle toho, jak jsi odpovídal."""
        answered = last_answers(
            db, user.email, [q["id"] for q in sorted_q], mode="marathon"
        )
        status = {
            qid: ("correct" if chosen == qmap[qid]["correct"] else "wrong")
            for qid, chosen in answered.items()
            if qid in qmap
        }
        from src.db.store import all_flagged
        return QuestionNavigator(
            sorted_q, current_index=current_pos, status=status, on_pick=_jump,
            flagged=set(all_flagged(db, user.email)),
        )

    def _jump(index: int):
        """Skok na otázku ze seznamu.

        Dopředu se přeskakovat nedá — marathon je sekvenční průchod a přeskočené
        otázky by tiše zmizely z postupu. Na už zodpovězené se skáče do prohlížení.
        """
        run = state["run"]
        if index >= run["position"]:
            ui.notify(
                "Dopředu se v marathonu přeskakovat nedá — pokračuj po pořadí.",
                position="top", timeout=2500,
            )
            return
        _review(index)

    def _render_review(run):
        """Prohlížení už zodpovězené otázky — bez možnosti odpovídat znovu."""
        pos = state["review"]
        q = sorted_q[pos]
        answered = last_answers(db, user.email, [q["id"]], mode="marathon").get(q["id"])

        ui.label("Prohlížíš odpovězenou otázku — zpátky se nic nezapisuje.").classes(
            "zp-body-sm zp-mb-sm"
        ).style("text-align: center;")

        with ui.element("div").classes("zp-quiz-with-nav"):
            _navigator(pos).render()
            with ui.element("div").classes("zp-quiz-main"):
                if answered:
                    QuizCard(
                        q,
                        user_email=user.email,
                        preset_answer=answered,
                        progress_label=f"Otázka {pos+1} / {run['total']}",
                        progress_ratio=pos / run["total"],
                        is_bookmarked=is_flagged(db, user.email, q["id"]),
                        on_bookmark_toggle=lambda q=q: toggle_flagged(db, user.email, q["id"]),
                    ).render()
                else:
                    ui.label(
                        f"Otázku č. {q['pdf_number']} jsi v tomhle marathonu ještě nezodpověděl."
                    ).classes("zp-body zp-mb-md").style("text-align: center;")
                _review_controls(run, pos)

    def _review_controls(run, pos):
        with ui.row().classes("w-full zp-gap-sm zp-mt-md").style(
            "justify-content: center; flex-wrap: wrap;"
        ):
            ui.button(icon=I["back"], on_click=lambda: _review(pos - 1)).props(
                "flat round"
            ).classes("zp-review-prev").tooltip("Předchozí").set_enabled(pos > 0)
            ui.button("Zpět na aktuální", icon=I["next"], on_click=_leave_review).props(
                "color=primary unelevated"
            ).classes("zp-review-exit")
            ui.button(icon=I["next"], on_click=lambda: _review(pos + 1)).props(
                "flat round"
            ).classes("zp-review-next").tooltip("Další").set_enabled(pos + 1 < run["position"])

    def _review(pos: int):
        state["review"] = max(0, min(pos, state["run"]["position"] - 1))
        render()

    def _leave_review():
        state["review"] = None
        render()

    def _start_new():
        start_marathon(db, user.email, len(sorted_q))
        state["run"] = get_active_marathon(db, user.email)
        render()

    def _on_answer(q, chosen, ms):
        record_attempt(db, user_email=user.email, question_id=q["id"], chosen=chosen,
                       correct=q["correct"], mode="marathon", time_ms=ms)
        if chosen == q["correct"]:
            update_marathon(db, state["run"]["id"], position=state["run"]["position"], correct_inc=1)
            state["run"] = get_active_marathon(db, user.email)

    def _advance():
        new_pos = state["run"]["position"] + 1
        update_marathon(db, state["run"]["id"], position=new_pos)
        state["run"] = get_active_marathon(db, user.email)
        render()

    with page_shell("Marathon", active_path="/marathon"):
        state["container"] = ui.column().classes("w-full")
        render()


def _marathon_intro(sorted_q, db, user_email, start_cb):
    ui.label("Marathon").classes("zp-display")
    ui.label(
        f"Sekvenční průchod všech {len(sorted_q)} otázek po pořadí podle PDF. "
        "Pozici si aplikace zapamatuje — můžeš kdykoli zavřít a pokračovat."
    ).classes("zp-body zp-prose zp-mb-lg")

    history = list_marathons(db, user_email)
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
