"""Denni review — Spaced Repetition System (FSRS)."""
from __future__ import annotations

from fsrs import Rating
from nicegui import ui

from src.db.questions import by_id
from src.db.store import get_db, record_attempt
from src.learning import srs as srs_mod
from src.ui.components import (
    empty_state, hero_result, back_home_button, rating_bar,
    is_flagged, toggle_flagged,
)
from src.ui.icons import I
from src.ui.layout import page_shell
from src.ui.quiz import QuizCard


RATING_MAP = {
    "again": Rating.Again,
    "hard":  Rating.Hard,
    "good":  Rating.Good,
    "easy":  Rating.Easy,
}


@ui.page("/srs")
def srs_page():
    db = get_db()
    qmap = by_id()
    all_qids = list(qmap.keys())

    state = {"queue": [], "index": 0, "container": None}

    def _build_queue():
        due = srs_mod.due_today(db, limit=30)
        if len(due) < 20:
            due = due + srs_mod.queue_for_unseen(db, all_qids, limit=20 - len(due))
        state["queue"] = [qid for qid in due if qid in qmap]
        state["index"] = 0

    def render():
        state["container"].clear()
        with state["container"]:
            if not state["queue"]:
                empty_state(
                    icon_name="srs",
                    heading="Prázdná review fronta",
                    subtitle=(
                        "Zatím nemáš nic v SRS systému. Začni nějaký režim — "
                        "otázky se zaznamenají automaticky."
                    ),
                    cta_label="Začít Marathon",
                    cta_target="/marathon",
                )
                return
            total = len(state["queue"])
            if state["index"] >= total:
                hero_result(
                    passed=True,
                    title="Hotovo s dnešním review!",
                    subtitle=f"Zopakováno {total} otázek",
                    icon_name="trophy",
                )
                with ui.row().classes("zp-row zp-gap-sm zp-mt-lg").style("justify-content: center;"):
                    ui.button("Načíst další várku", icon=I["refresh"],
                              on_click=lambda: (_build_queue(), render())).props(
                        "color=primary unelevated"
                    )
                    back_home_button()
                return

            qid = state["queue"][state["index"]]
            q = qmap[qid]
            card = QuizCard(
                q,
                instant_feedback=True,
                progress_label=f"SRS  {state['index']+1} / {total}",
                progress_ratio=state["index"] / total,
                is_bookmarked=is_flagged(db, qid),
                on_answer=lambda chosen, ms, q=q: _on_answer(q, chosen, ms),
                on_next=lambda: None,
                on_bookmark_toggle=lambda q=q: toggle_flagged(db, q["id"]),
                show_next_button=False,
            )
            card.render()

            rating_bar(lambda key, q=q: _rate(q, RATING_MAP[key]))

    def _on_answer(q, chosen, ms):
        record_attempt(db, question_id=q["id"], chosen=chosen,
                       correct=q["correct"], mode="srs", time_ms=ms)

    def _rate(q, rating):
        card = srs_mod.review(db, q["id"], rating)
        # Feedback toast with next review interval
        import datetime as _dt
        now = _dt.datetime.now(_dt.timezone.utc)
        delta = card.due - now
        if delta.total_seconds() < 3600:
            when = f"{int(delta.total_seconds() // 60)} min"
        elif delta.total_seconds() < 86400:
            when = f"{int(delta.total_seconds() // 3600)} h"
        else:
            when = f"{delta.days} dní"
        label_map = {
            Rating.Again: "Znovu",
            Rating.Hard:  "Těžké",
            Rating.Good:  "Dobré",
            Rating.Easy:  "Snadné",
        }
        ui.notify(
            f"{label_map.get(rating, '')} — otázka se vrátí za {when}",
            position="top", timeout=1800, color="positive",
        )
        state["index"] += 1
        render()

    with page_shell("Denní review (SRS)", active_path="/srs"):
        state["container"] = ui.column().classes("w-full")
        _build_queue()
        render()
