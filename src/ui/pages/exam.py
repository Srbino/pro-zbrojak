"""Simulace zkousky — setup, run s timerem, result screen."""
from __future__ import annotations

import random
import time
from collections import defaultdict

from nicegui import ui

from src.auth import require_login
from src.db import law_refs, traps
from src.db.questions import load_questions
from src.db.store import get_db, list_exams, record_attempt, record_exam
from src.export.claude_md import export_questions
from src.learning.exam import threshold_for
from src.ui.components import (
    SECTION_LABEL,
    back_home_button,
    progress_bar,
    query_int,
    query_str,
    section_badge,
    stat_card,
)
from src.ui.icons import I
from src.ui.layout import page_shell
from src.ui.quiz import QuizCard


@ui.page("/exam")
def exam_page():
    user = require_login()
    if user is None:
        return
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
                {"standard": "Standardní zbrojní oprávnění (26 z 30)",
                 "extended": "Rozšířené zbrojní oprávnění (28 z 30)"},
                value="standard", label="Úroveň oprávnění",
            ).classes("w-full").props("outlined")
            with ui.row().classes("w-full zp-gap-md zp-mt-md zp-exam-inputs"):
                n_questions = ui.number("Počet otázek", value=30, min=5, max=100, step=1).props(
                    "outlined"
                ).classes("zp-flex-1")
                time_limit = ui.number("Časový limit (min)", value=40, min=5, max=120, step=1).props(
                    "outlined"
                ).classes("zp-flex-1")

            hint = ui.label("").classes("zp-body-sm zp-mt-sm")

            def _update_hint():
                try:
                    n = int(n_questions.value or 30)
                except (TypeError, ValueError):
                    n = 30
                need = threshold_for(level.value, n)
                hint.text = f"K úspěchu potřebuješ {need} správných z {n}."

            _update_hint()
            level.on_value_change(lambda _: _update_hint())
            n_questions.on_value_change(lambda _: _update_hint())

            def start():
                ui.navigate.to(
                    f"/exam/run?level={level.value}&n={int(n_questions.value)}"
                    f"&t={int(time_limit.value)}"
                )

            ui.button("Spustit simulaci", icon=I["play"], on_click=start).props(
                "size=lg color=primary unelevated"
            ).classes("w-full zp-mt-md")

        history = list_exams(db, user.email)
        if history:
            ui.label("Historie simulací").classes("zp-h2 zp-mt-xl zp-mb-sm")
            _render_history(history)


@ui.page("/exam/run")
def exam_run_page():
    user = require_login()
    if user is None:
        return
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
            if tl < 60:
                timer_cls = "zp-timer danger"
            elif tl < 300:
                timer_cls = "zp-timer warning"
            with ui.row().classes("zp-row-between zp-nowrap w-full zp-mb-sm"):
                ui.label(f"Otázka {state['index']+1} / {len(pool)}").classes("zp-body-sm")
                state["timer_label"] = ui.html(
                    f'<div class="{timer_cls}">'
                    f'<span class="material-icons" style="font-size:14px;">{I["timer"]}</span> '
                    f'{_fmt(tl)}</div>'
                )

            card = QuizCard(
                q, instant_feedback=False,
                exam_mode=True,
                user_email=user.email,
                progress_label="",
                progress_ratio=state["index"] / len(pool),
                on_answer=lambda chosen, ms, q=q: _on_answer(q, chosen),
                on_next=_advance,
                show_next_button=False,
            )
            card.render()

            with ui.row().classes("w-full zp-gap-md zp-mt-md").style(
                "justify-content: center; flex-wrap: wrap;"
            ):
                ui.button("Přeskočit", icon=I["skip"], on_click=_advance).props("flat")
                ui.button("Ukončit simulaci", icon=I["stop"], on_click=_finish).props(
                    "flat color=negative"
                )

            _progress_dots(pool, answers, state["index"])

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
        record_exam(db, user_email=user.email, level=level, score=score,
                    total=len(pool), duration_s=duration)
        for q in pool:
            ch = answers.get(q["id"])
            if ch:
                record_attempt(db, user_email=user.email, question_id=q["id"], chosen=ch,
                               correct=q["correct"], mode="exam")
        _render_result(state["container"], pool, answers, level, score, duration)

    def _tick():
        if state["finished"] or state["timer_label"] is None:
            return
        tl = time_left()
        cls = "zp-timer"
        if tl < 60:
            cls = "zp-timer danger"
        elif tl < 300:
            cls = "zp-timer warning"
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


def _progress_dots(pool: list[dict], answers: dict[str, str], index: int) -> None:
    """Stav průběhu tečkami — jediný způsob, jak poznat přeskočenou otázku.

    Tečky záměrně nenesou čísla otázek: u komise se otázky taky nečíslují
    a nemá smysl si na to zvykat.
    """
    dots = []
    for i, q in enumerate(pool):
        if i == index:
            cls = "cur"
        elif q["id"] in answers:
            cls = "done"
        elif i < index:
            cls = "skipped"
        else:
            cls = ""
        dots.append(f'<span class="zp-dot {cls}"></span>')
    n_answered = len(answers)
    n_skipped = sum(1 for i, q in enumerate(pool) if i < index and q["id"] not in answers)
    ui.html(
        f'<div class="zp-dots">{"".join(dots)}</div>'
        f'<div class="zp-dots-legend">{n_answered} odpovězeno'
        f'{f" · {n_skipped} přeskočeno" if n_skipped else ""}'
        f' · {len(pool) - index} zbývá</div>'
    ).classes("w-full")


def _render_history(history):
    with ui.element("div").classes("zp-card"):
        try:
            import plotly.graph_objects as go
            xs = list(range(len(history) - 1, -1, -1))
            # Procenta, ne absolutní skóre — simulace mají různý počet otázek,
            # takže 24 bodů z 30 a z 6 nejsou srovnatelné hodnoty.
            def _pct(r):
                return round(r["score"] / max(1, r["total"]) * 100, 1)
            ys_std = [_pct(r) if r["level"] == "standard" else None for r in history][::-1]
            ys_ext = [_pct(r) if r["level"] == "extended" else None for r in history][::-1]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=xs[::-1], y=ys_std, mode="markers+lines", name="Standard",
                                     marker=dict(size=10, color="#10627A"), line=dict(color="#10627A")))
            fig.add_trace(go.Scatter(x=xs[::-1], y=ys_ext, mode="markers+lines", name="Rozšířené",
                                     marker=dict(size=10, color="#F59E0B"), line=dict(color="#F59E0B")))
            fig.add_hline(y=86.7, line_dash="dash", line_color="#10627A", opacity=0.4,
                          annotation_text="hranice std")
            fig.add_hline(y=93.3, line_dash="dash", line_color="#F59E0B", opacity=0.4,
                          annotation_text="hranice ext")
            fig.update_layout(
                height=220, margin=dict(l=30, r=10, t=20, b=30),
                yaxis=dict(range=[0, 100], title="úspěšnost %"),
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
    threshold = threshold_for(level, len(pool))
    passed = score >= threshold
    wrongs = [q for q in pool if answers.get(q["id"]) != q["correct"]]
    by_sec: dict[str, list[dict]] = defaultdict(list)
    for q in wrongs:
        by_sec[q.get("section") or "unknown"].append(q)

    with container:
        ui.html(
            f'<div class="zp-verdict {"pass" if passed else "fail"}">'
            f'<span class="zp-verdict-label">{"Prošel jsi" if passed else "Neprošel jsi"}</span>'
            f'<span class="zp-verdict-score">{score} / {len(pool)}</span>'
            f'<span class="zp-verdict-sub">hranice {threshold} z {len(pool)} · '
            f'{"standardní" if level == "standard" else "rozšířené"} oprávnění · '
            f'{_fmt(duration)}</span></div>'
        ).classes("w-full")

        with ui.element("div").classes("zp-grid-3 zp-mt-lg"):
            stat_card("Úspěšnost", f"{round(score/len(pool)*100, 1)} %", sub="z této simulace")
            stat_card("Chybělo" if not passed else "Rezerva",
                      f"{abs(score - threshold)}",
                      sub="otázek k hranici" if not passed else "otázek nad hranicí")
            stat_card("Čas", _fmt(duration), sub=f"z {len(pool)} otázek")

        if wrongs:
            # Kde se ztrácelo — bez toho člověk neví, co se má doučit.
            ui.label("Kde jsi ztrácel").classes("zp-h2 zp-mt-xl zp-mb-sm")
            with ui.element("div").classes("zp-card"):
                for sec, qs in sorted(by_sec.items(), key=lambda kv: -len(kv[1])):
                    total_sec = sum(1 for q in pool if (q.get("section") or "unknown") == sec)
                    with ui.row().classes("zp-row w-full zp-gap-md zp-mb-sm").style(
                        "flex-wrap: wrap;"
                    ):
                        ui.label(SECTION_LABEL.get(sec, sec)).classes("zp-body-sm").style(
                            "min-width: 160px;"
                        )
                        with ui.element("div").classes("zp-flex-1").style("min-width: 120px;"):
                            progress_bar(1 - len(qs) / max(1, total_sec), variant="danger")
                        ui.label(
                            f"{len(qs)} chyb z {total_sec}"
                        ).classes("zp-caption zp-mono")

            ui.label(f"Chyby ({len(wrongs)})").classes("zp-h2 zp-mt-xl zp-mb-sm")
            for sec, qs in by_sec.items():
                with ui.element("div").classes("zp-card zp-mb-sm"):
                    with ui.row().classes("zp-row zp-nowrap w-full zp-mb-sm"):
                        section_badge(sec)
                        ui.label(f"{len(qs)} chyb").classes("zp-caption").style("margin-left: .75rem;")
                    for q in qs[:10]:
                        _wrong_row(q, answers.get(q["id"]))
                    if len(qs) > 10:
                        ui.label(f"… a {len(qs) - 10} dalších").classes("zp-caption")

        with ui.row().classes("w-full zp-gap-sm zp-mt-lg").style("flex-wrap: wrap;"):
            if wrongs:
                # Z výsledku rovnou do procvičení. Dřív se musely chyby hledat
                # ručně v Lekci z chyb.
                ui.button(f"Procvičit těchto {len(wrongs)}", icon=I["next"],
                          on_click=lambda: ui.navigate.to("/mistakes")).props(
                    "color=primary unelevated"
                )
            ui.button("Nová simulace", icon=I["refresh"],
                      on_click=lambda: ui.navigate.to("/exam")).props(
                "outline color=primary" if wrongs else "color=primary unelevated"
            )
            back_home_button()
            if wrongs:
                def do_export():
                    path = export_questions(wrongs, my_answers=answers, filename_hint="exam_wrong")
                    ui.notify(f"Vyexportováno → {path.name}", position="top", timeout=3000)
                ui.button("Export chyb pro AI", icon=I["upload"],
                          on_click=do_export).props("flat color=primary")


def _wrong_row(q: dict, chosen: str | None) -> None:
    """Jedna chyba: co jsi zvolil, co je správně, kde to v zákoně stojí.

    Bez písmen — možnosti se zobrazují promíchané, takže „správně: B" by
    neodpovídalo tomu, co člověk u zkoušky viděl.
    """
    ref = law_refs.ref_for(q["pdf_number"])
    is_trap = bool(traps.trap_for(q["pdf_number"]))
    with ui.column().classes("w-full").style("padding: .5rem 0; gap: .2rem;"):
        ui.label(q["question"]).classes("zp-body-sm").style("font-weight: 600;")
        if chosen:
            ui.label(f"tvá volba: {q['options'].get(chosen, '—')}").classes("zp-caption")
        else:
            ui.label("neodpovězeno").classes("zp-caption")
        ui.label(f"správně: {q['options'][q['correct']]}").classes("zp-caption").style(
            "font-weight: 600; opacity: .95;"
        )
        if ref or is_trap:
            with ui.row().classes("zp-row zp-gap-sm zp-mt-xs").style("flex-wrap: wrap;"):
                if ref:
                    ui.link(f"{ref['ref']} ↗", ref["url"], new_tab=True).classes(
                        "zp-law-ref-link"
                    )
                if is_trap:
                    ui.html('<span class="zp-badge warning">chyták</span>')
