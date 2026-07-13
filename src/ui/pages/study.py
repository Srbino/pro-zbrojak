"""Studium — projdi otázky se správnými odpověďmi.

Výchozí režim je kartička (otázka → mezerníkem odhal správnou = lehké vybavování).
Přepínače: „Rovnou ukázat" (čtení) a „Jen správná" (skryje distraktory).
Navigátor: seznam čísel otázek — klikni a skoč na libovolnou.
"""
from __future__ import annotations

import random

from nicegui import ui

from src.auth import require_login
from src.db.questions import load_questions
from src.db.store import get_db, set_studied, studied_counts, studied_map
from src.ui.components import SECTION_LABEL, progress_bar, section_badge
from src.ui.icons import I
from src.ui.layout import page_shell


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


@ui.page("/study")
def study_page():
    user = require_login()
    if user is None:
        return
    db = get_db()
    all_q = sorted(load_questions(), key=lambda x: x["pdf_number"])

    st = {
        "section": "all", "order": "seq",
        "flashcard": True, "only_correct": False,
        "pool": [], "index": 0, "revealed": False,
        "known": studied_map(db, user.email),
        "chips": {},          # qid -> ui element
        "card": None, "grid": None, "counts": None,
    }

    def build_pool():
        qs = all_q if st["section"] == "all" else [q for q in all_q if q.get("section") == st["section"]]
        if st["order"] == "rand":
            qs = qs[:]
            random.Random(1).shuffle(qs)
        st["pool"] = qs
        st["index"] = 0
        st["revealed"] = False

    # ---------- navigátor (seznam čísel) ----------
    def chip_cls(qid: str, cur: bool) -> str:
        cls = "zp-chip"
        k = st["known"].get(qid)
        if k == 1:
            cls += " known"
        elif k == 0:
            cls += " seen"
        if cur:
            cls += " cur"
        return cls

    def render_grid():
        st["grid"].clear()
        st["chips"] = {}
        with st["grid"]:
            for i, q in enumerate(st["pool"]):
                lbl = ui.label(str(q["pdf_number"])).classes(chip_cls(q["id"], i == st["index"]))
                lbl.on("click", lambda e, i=i: goto(i))
                st["chips"][q["id"]] = lbl

    def restyle_chip(idx: int):
        if 0 <= idx < len(st["pool"]):
            q = st["pool"][idx]
            ch = st["chips"].get(q["id"])
            if ch is not None:
                ch.classes(replace=chip_cls(q["id"], idx == st["index"]))

    # ---------- karta ----------
    def render_card():
        st["card"].clear()
        with st["card"]:
            total = len(st["pool"])
            if total == 0:
                ui.label("V této oblasti nejsou otázky.").classes("zp-body")
                return
            q = st["pool"][st["index"]]
            reveal_now = (not st["flashcard"]) or st["revealed"]

            progress_bar((st["index"] + 1) / total)
            with ui.row().classes("zp-row zp-nowrap w-full zp-mt-sm zp-mb-sm").style("align-items:center;"):
                ui.label(f"{st['index']+1} / {total}").classes("zp-body-sm zp-flex-1").style("font-weight:500;")
                section_badge(q.get("section"))
                ui.label(f"č. {q['pdf_number']}").classes("zp-caption").style("margin-left:.75rem;")
                if st["known"].get(q["id"]) == 1:
                    ui.html('<span class="zp-badge success" style="margin-left:.5rem;">umím</span>')

            with ui.element("div").classes("zp-card").style("padding:1.5rem;"):
                if q.get("image"):
                    ui.html(
                        f'<div style="text-align:center;margin-bottom:1rem;">'
                        f'<img src="/{q["image"]}" style="max-height:300px;max-width:100%;object-fit:contain;">'
                        f'</div>'
                    )
                ui.label(q["question"]).classes("zp-h2 zp-mb-md")

                if not reveal_now:
                    ui.button("Odhalit odpověď", icon=I["reveal"], on_click=_reveal).props(
                        "color=primary unelevated size=md"
                    )
                    ui.label("(mezerník)").classes("zp-caption zp-mt-xs")
                else:
                    correct = q["correct"]
                    with ui.column().classes("w-full zp-gap-sm"):
                        if st["only_correct"]:
                            ui.html(f'<div class="zp-answer-correct"><b>{correct})</b> {_esc(q["options"][correct])}</div>')
                        else:
                            for k in ("A", "B", "C"):
                                cls = "zp-answer-correct" if k == correct else "zp-answer-neutral"
                                ui.html(f'<div class="{cls}"><b>{k})</b> {_esc(q["options"][k])}</div>')

            # ovládání
            with ui.row().classes("w-full zp-gap-sm zp-mt-md").style("flex-wrap:wrap;align-items:center;justify-content:center;"):
                ui.button(icon=I["back"], on_click=_prev).props("flat round").tooltip("Předchozí (←)")
                ui.button("Ještě ne", on_click=lambda: _mark(False)).props("outline color=grey-7")
                ui.button("Umím", icon=I["check"], on_click=lambda: _mark(True)).props("unelevated color=positive")
                ui.button(icon=I["next"], on_click=_next).props("flat round color=primary").tooltip("Další (→ / mezerník)")

            c = studied_counts(db, user.email)
            st["counts"].text = f"Umím: {c['known']}   ·   Prošel jsi: {c['seen']} / {len(all_q)}"

    # ---------- akce ----------
    def _reveal():
        st["revealed"] = True
        render_card()

    def goto(i: int):
        old = st["index"]
        st["index"] = max(0, min(i, len(st["pool"]) - 1))
        st["revealed"] = False
        restyle_chip(old)
        restyle_chip(st["index"])
        render_card()

    def _next():
        if st["index"] < len(st["pool"]) - 1:
            goto(st["index"] + 1)

    def _prev():
        if st["index"] > 0:
            goto(st["index"] - 1)

    def _mark(known: bool):
        q = st["pool"][st["index"]]
        set_studied(db, user.email, q["id"], known)
        st["known"][q["id"]] = int(known)
        restyle_chip(st["index"])
        if st["index"] < len(st["pool"]) - 1:
            goto(st["index"] + 1)
        else:
            render_card()

    def _on_key(e):
        if not e.action.keydown:
            return
        k = (str(e.key).lower() if e.key else "")
        if k in ("enter", " ", "spacebar"):
            if st["flashcard"] and not st["revealed"]:
                _reveal()
            else:
                _next()
        elif k in ("arrowright",):
            _next()
        elif k in ("arrowleft",):
            _prev()
        elif k == "u":
            _mark(True)

    def _jump():
        try:
            n = int(jump.value)
        except (TypeError, ValueError):
            return
        for i, q in enumerate(st["pool"]):
            if q["pdf_number"] == n:
                goto(i)
                return
        ui.notify(f"Otázka č. {n} není v aktuálním filtru", color="warning", position="top")

    # ---------- layout ----------
    with page_shell("Studium", active_path="/study"):
        ui.label("Studium").classes("zp-display")
        ui.label(
            "Projdi si otázky a rovnou správné odpovědi. Ve výchozím režimu je to kartička — "
            "zkus si odpověď vybavit a mezerníkem ji odhal (drží se to v paměti líp)."
        ).classes("zp-body zp-prose zp-mb-md")

        with ui.element("div").classes("zp-card w-full zp-mb-md"):
            with ui.row().classes("w-full zp-gap-md").style("flex-wrap:wrap;align-items:center;"):
                sec = ui.select(
                    {"all": "Vše", **SECTION_LABEL}, value="all", label="Oblast",
                ).props("outlined dense").style("min-width:200px;")
                order = ui.select(
                    {"seq": "Po pořadí", "rand": "Náhodně"}, value="seq", label="Pořadí",
                ).props("outlined dense").style("min-width:150px;")
                sw_read = ui.switch("Rovnou ukázat správnou")
                sw_only = ui.switch("Jen správná odpověď")

            with ui.row().classes("w-full zp-gap-sm zp-mt-sm").style("align-items:center;"):
                jump = ui.number("Skoč na č.", min=1, max=len(all_q)).props("outlined dense").style("width:130px;")
                ui.button("Skoč", on_click=lambda: _jump()).props("flat color=primary")
                st["counts"] = ui.label("").classes("zp-body-sm zp-flex-1").style("text-align:right;")

            with ui.expansion("Seznam otázek — klikni a skoč na libovolnou", icon=I["study"]).classes("w-full zp-mt-sm"):
                st["grid"] = ui.element("div").classes("zp-study-grid")

        st["card"] = ui.column().classes("w-full")

        def _rebuild():
            build_pool()
            render_grid()
            render_card()

        def _on_toggle():
            st["flashcard"] = not sw_read.value
            st["only_correct"] = sw_only.value
            st["revealed"] = False
            render_card()

        sec.on_value_change(lambda: (st.update(section=sec.value), _rebuild()))
        order.on_value_change(lambda: (st.update(order=order.value), _rebuild()))
        sw_read.on_value_change(_on_toggle)
        sw_only.on_value_change(_on_toggle)

        _rebuild()
        ui.keyboard(on_key=_on_key)
