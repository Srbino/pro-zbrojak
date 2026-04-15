"""Simulace zkousky — setup, run s timerem, result screen."""
from __future__ import annotations

import random
import time
from collections import defaultdict

from nicegui import ui

from src.db.questions import load_questions
from src.db.store import get_db, record_attempt, record_exam, list_exams
from src.export.claude_md import export_questions
from src.ui.components import (
    SECTION_LABEL, SECTION_BADGE_VARIANT, hero_result, stat_card,
    back_home_button, section_badge,
    query_int, query_str,
)
from src.ui.icons import I, icon
from src.ui.layout import page_shell
from src.ui.quiz import QuizCard


@ui.page("/exam")
def exam_page():
    db = get_db()
    with page_shell("Simulace zkoušky", active_path="/exam"):
        ui.label("Simulace zkoušky").classes("zp-display")
        ui.label(
            "Podle NV č. 238/2025 Sb.: 30 otázek za 40 minut, bez okamžité zpětné vazby. "
            "Hranice úspěšnosti podle úrovně oprávnění."
        ).classes("zp-body zp-prose zp-mb-lg")

        with ui.element("div").classes("zp-card w-full zp-mb-md"):
            ui.label("Konfigurace").classes("zp-h3 zp-mb-sm")
            level = ui.select(
                {"standard": "Standardní zbrojní oprávnění (≥ 26/30)",
                 "extended": "Rozšířené zbrojní oprávnění (≥ 28/30)"},
                value="standard", label="Úroveň oprávnění",
            ).classes("w-full").props("outlined")
            with ui.row().classes("w-full zp-gap-md zp-mt-md zp-exam-inputs"):
                n_questions = ui.number("Počet otázek", value=30, min=5, max=100, step=1).props(
                    "outlined"
                ).classes("zp-flex-1")
                time_limit = ui.number("Časový limit (min)", value=40, min=5, max=120, step=1).props(
                    "outlined"
                ).classes("zp-flex-1")

            def start():
                ui.navigate.to(
                    f"/exam/run?level={level.value}&n={int(n_questions.value)}"
                    f"&t={int(time_limit.value)}"
                )

            ui.button("Spustit simulaci", icon=I["play"], on_click=start).props(
                "size=lg color=primary unelevated"
            ).classes("w-full zp-mt-md")

        history = list_exams(db)
        if history:
            ui.label("Historie simulací").classes("zp-h2 zp-mt-xl zp-mb-sm")
            _render_history(history)


@ui.page("/exam/run")
def exam_run_page():
    level = query_str("level", "standard")
    n = query_int("n", 30)
    t = query_int("t", 40)

    db = get_db()
    questions = load_questions()
    pool = random.sample(questions, k=min(n, len(questions)))
    answers: dict[str, str] = {}
    started_at = time.time()
    deadline = started_at + t * 60

    state = {"index": 0, "container": None, "timer_label": None, "finished": False}

    def time_left() -> int:
        return max(0, int(deadline - time.time()))

    def render():
        state["container"].clear()
        with state["container"]:
            if state["finished"]:
                return
            if state["index"] >= len(pool) or time_left() == 0:
                _finish()
                return
            q = pool[state["index"]]
            tl = time_left()
            timer_cls = "zp-timer"
            if tl < 60: timer_cls = "zp-timer danger"
            elif tl < 300: timer_cls = "zp-timer warning"
            with ui.row().classes("zp-row-between zp-nowrap w-full zp-mb-sm"):
                ui.label(f"Otázka {state['index']+1} / {len(pool)}").classes("zp-body-sm")
                state["timer_label"] = ui.html(
                    f'<div class="{timer_cls}">'
                    f'<span class="material-icons" style="font-size:14px;">{I["timer"]}</span> '
                    f'{_fmt(tl)}</div>'
                )

            card = QuizCard(
                q, instant_feedback=False,
                progress_label="",
                progress_ratio=state["index"] / len(pool),
                on_answer=lambda chosen, ms, q=q: _on_answer(q, chosen),
                on_next=_advance,
                show_next_button=False,
            )
            card.render()

            with ui.row().classes("w-full zp-gap-sm zp-mt-md"):
                ui.button("Přeskočit", icon=I["skip"], on_click=_advance).props("flat")
                ui.element("div").classes("zp-flex-1")
                ui.button("Ukončit simulaci", icon=I["stop"], on_click=_finish).props("flat color=negative")

    def _on_answer(q, chosen):
        answers[q["id"]] = chosen

    def _advance():
        state["index"] += 1
        render()

    def _finish():
        if state["finished"]:
            return
        state["finished"] = True
        score = sum(1 for q in pool if answers.get(q["id"]) == q["correct"])
        duration = int(time.time() - started_at)
        record_exam(db, level=level, score=score, total=len(pool), duration_s=duration)
        for q in pool:
            ch = answers.get(q["id"])
            if ch:
                record_attempt(db, question_id=q["id"], chosen=ch,
                               correct=q["correct"], mode="exam")
        _render_result(state["container"], pool, answers, level, score, duration)

    def _tick():
        if state["finished"] or state["timer_label"] is None:
            return
        tl = time_left()
        cls = "zp-timer"
        if tl < 60: cls = "zp-timer danger"
        elif tl < 300: cls = "zp-timer warning"
        state["timer_label"].content = (
            f'<div class="{cls}">'
            f'<span class="material-icons" style="font-size:14px;">{I["timer"]}</span> '
            f'{_fmt(tl)}</div>'
        )
        if tl == 0:
            _finish()

    with page_shell("Simulace probíhá", active_path="/exam"):
        state["container"] = ui.column().classes("w-full")
        render()
        ui.timer(1.0, _tick)


# ----- helpers -----

def _fmt(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def _render_history(history):
    with ui.element("div").classes("zp-card"):
        try:
            import plotly.graph_objects as go
            xs = list(range(len(history) - 1, -1, -1))
            ys_std = [r["score"] if r["level"] == "standard" else None for r in history][::-1]
            ys_ext = [r["score"] if r["level"] == "extended" else None for r in history][::-1]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=xs[::-1], y=ys_std, mode="markers+lines", name="Standard",
                                     marker=dict(size=10, color="#1E40AF"), line=dict(color="#1E40AF")))
            fig.add_trace(go.Scatter(x=xs[::-1], y=ys_ext, mode="markers+lines", name="Rozšířené",
                                     marker=dict(size=10, color="#F59E0B"), line=dict(color="#F59E0B")))
            fig.add_hline(y=26, line_dash="dash", line_color="#1E40AF", opacity=0.4, annotation_text="26 std")
            fig.add_hline(y=28, line_dash="dash", line_color="#F59E0B", opacity=0.4, annotation_text="28 ext")
            fig.update_layout(
                height=220, margin=dict(l=30, r=10, t=20, b=30),
                yaxis=dict(range=[0, 30], title="skóre"),
                xaxis=dict(title="simulace (starší → novější)"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            ui.plotly(fig).classes("w-full").style("height: 220px;")
        except Exception:
            pass
        ui.separator().classes("my-2")
        for r in history[:10]:
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(r["ts"]))
            cls = "success" if r["passed"] else "danger"
            label = "prošel" if r["passed"] else "neprošel"
            lvl = "Standard" if r["level"] == "standard" else "Rozšířené"
            mm, ss = r["duration_s"] // 60, r["duration_s"] % 60
            with ui.row().classes("zp-row zp-nowrap w-full").style("padding: .4rem 0;"):
                ui.html(f'<span class="zp-badge {cls}">{label}</span>')
                ui.label(lvl).classes("zp-body-sm").style("width: 110px; margin-left: .75rem;")
                ui.label(f"{r['score']}/{r['total']}").classes("zp-body zp-mono").style(
                    "width: 60px; font-weight: 600;"
                )
                ui.label(f"{mm}:{ss:02d}").classes("zp-body-sm zp-mono").style("width: 60px;")
                ui.label(ts).classes("zp-caption zp-mono").style("flex: 1; text-align: right;")


def _render_result(container, pool, answers, level, score, duration):
    container.clear()
    threshold = 26 if level == "standard" else 28
    passed = score >= threshold
    wrongs = [q for q in pool if answers.get(q["id"]) != q["correct"]]
    by_sec: dict[str, list[dict]] = defaultdict(list)
    for q in wrongs:
        by_sec[q.get("section") or "unknown"].append(q)

    with container:
        hero_result(
            passed=passed,
            title="PROŠEL JSI" if passed else "NEPROŠEL JSI",
            subtitle=f"{score} / {len(pool)} správně   ·   {_fmt(duration)}   ·   hranice {threshold}",
            icon_name="trophy" if passed else "fitness",
        )

        with ui.element("div").classes("zp-grid-3 zp-mt-lg"):
            stat_card("Úspěšnost", f"{round(score/len(pool)*100, 1)} %", sub="z této simulace")
            stat_card("Hranice", f"{threshold}/30",
                      sub=("standardní" if level == "standard" else "rozšířené oprávnění"))
            stat_card("Čas", _fmt(duration), sub="trvání simulace")

        if wrongs:
            ui.label(f"Chyby ({len(wrongs)})").classes("zp-h2 zp-mt-xl zp-mb-sm")
            for sec, qs in by_sec.items():
                label = SECTION_LABEL.get(sec, sec)
                with ui.element("div").classes("zp-card zp-mb-sm"):
                    with ui.row().classes("zp-row zp-nowrap w-full zp-mb-sm"):
                        section_badge(sec)
                        ui.label(f"{len(qs)} chyb").classes("zp-caption").style("margin-left: .75rem;")
                    for q in qs[:10]:
                        ch = answers.get(q["id"])
                        msg = f"Q{q['pdf_number']}  ·  tvá volba: {ch or '—'}  ·  správně: {q['correct']}"
                        ui.label(msg).classes("zp-body-sm zp-mono").style("padding: .2rem 0;")
                    if len(qs) > 10:
                        ui.label(f"… a {len(qs) - 10} dalších").classes("zp-caption")

        with ui.row().classes("w-full zp-gap-sm zp-mt-lg").style("flex-wrap: wrap;"):
            ui.button("Nová simulace", icon=I["refresh"],
                      on_click=lambda: ui.navigate.to("/exam")).props("color=primary unelevated")
            back_home_button()
            if wrongs:
                def do_export():
                    path = export_questions(wrongs, my_answers=answers, filename_hint="exam_wrong")
                    ui.notify(f"Vyexportováno → {path.name}", position="top", timeout=3000)
                ui.button("Export chyb pro Claude Code", icon=I["upload"],
                          on_click=do_export).props("color=secondary")
