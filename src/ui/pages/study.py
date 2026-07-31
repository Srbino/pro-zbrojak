"""Studium — projdi otázky se správnými odpověďmi.

Výchozí režim je čtení: odpověď i ustanovení jsou vidět rovnou. Kdo se chce
zkoušet po paměti, zapne si režim kartičky.

Vlevo je stejný navigátor jako v marathonu — seznam otázek s hledáním
a filtry. Nahradil dřívější políčko „Skoč na č." a rozklikávací mřížku čísel:
obojí nutilo psát číslo otázky, kterou člověk hledá podle znění, ne podle čísla.
"""
from __future__ import annotations

import random

from nicegui import ui

from src.auth import require_login
from src.db.questions import load_questions
from src.db.store import all_flagged, get_db, set_studied, studied_counts, studied_map
from src.ui.components import (
    SECTION_LABEL,
    QuestionNavigator,
    law_reference,
    progress_bar,
    section_badge,
)
from src.ui.icons import I
from src.ui.layout import page_shell
from src.ui.shuffle import display_letter, option_order

# Stavy ve studiu se jmenují jinak než v kvízu, mechanika je stejná.
STUDY_FILTERS = (
    ("", "Vše"),
    ("correct", "Umím"),
    ("wrong", "Ještě ne"),
    ("flagged", "Označené"),
    ("trap", "Chytáky"),
)


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
        # Studium je čtení, ne zkoušení. Odpověď je vidět rovnou — mezikrok
        # „odhalit" u látky, kterou člověk teprve poznává, jen přidává klik.
        # Kdo si chce zkoušet paměť, zapne si režim kartičky.
        "flashcard": False, "only_correct": False,
        "pool": [], "index": 0, "revealed": False,
        "known": studied_map(db, user.email),
        "body": None, "counts": None,
    }

    def build_pool():
        qs = all_q if st["section"] == "all" else [q for q in all_q if q.get("section") == st["section"]]
        if st["order"] == "rand":
            qs = qs[:]
            random.Random(1).shuffle(qs)
        st["pool"] = qs
        st["index"] = 0
        st["revealed"] = False

    # ---------- navigátor ----------
    def _navigator() -> QuestionNavigator:
        """Seznam otázek vlevo, obarvený podle toho, co už umíš."""
        status = {}
        for q in st["pool"]:
            k = st["known"].get(q["id"])
            if k == 1:
                status[q["id"]] = "correct"   # umím
            elif k == 0:
                status[q["id"]] = "wrong"     # ještě ne
        return QuestionNavigator(
            st["pool"], current_index=st["index"], status=status, on_pick=goto,
            flagged=set(all_flagged(db, user.email)), filters=STUDY_FILTERS,
        )

    def render():
        """Překreslí navigátor i kartu — panel musí vědět, kde právě jsi."""
        st["body"].clear()
        with st["body"], ui.element("div").classes("zp-quiz-with-nav"):
            _navigator().render()
            with ui.element("div").classes("zp-quiz-main"):
                render_card()

    # ---------- karta ----------
    def render_card():
        with ui.element("div").classes("zp-quiz-wrap"):
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

            with ui.element("div").classes("zp-card"):
                if q.get("image"):
                    ui.html(
                        f'<div style="text-align:center;margin-bottom:1rem;">'
                        f'<img src="/{q["image"]}" style="max-height:300px;max-width:100%;object-fit:contain;">'
                        f'</div>'
                    )
                ui.label(q["question"]).classes("zp-question zp-mb-md")

                if not reveal_now:
                    ui.button("Odhalit odpověď", icon=I["reveal"], on_click=_reveal).props(
                        "color=primary unelevated size=md"
                    )
                    ui.label("(mezerník)").classes("zp-caption zp-mt-xs")
                else:
                    correct = q["correct"]
                    # Stejné promíchání jako v kvízu — jinak by studium naučilo
                    # právě tu polohu odpovědi, kterou se učit nemá.
                    order = option_order(q, user_email=user.email)
                    with ui.column().classes("w-full zp-gap-sm"):
                        if st["only_correct"]:
                            shown = display_letter(order.index(correct))
                            ui.html(f'<div class="zp-answer-correct"><b>{shown})</b> {_esc(q["options"][correct])}</div>')
                        else:
                            for position, canonical in enumerate(order):
                                shown = display_letter(position)
                                cls = "zp-answer-correct" if canonical == correct else "zp-answer-neutral"
                                ui.html(f'<div class="{cls}"><b>{shown})</b> {_esc(q["options"][canonical])}</div>')
                    # Když odkaz chybí, řekni to. Mlčení vypadá jako chyba
                    # aplikace, přitom ověřený odkaz má 231 z 837 otázek.
                    if not law_reference(q["pdf_number"]):
                        ui.label(
                            "K této otázce zatím nemáme ověřený odkaz do e-Sbírky."
                        ).classes("zp-caption zp-mt-md")

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
        render()

    def goto(i: int):
        st["index"] = max(0, min(i, len(st["pool"]) - 1))
        st["revealed"] = False
        render()

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
        if st["index"] < len(st["pool"]) - 1:
            goto(st["index"] + 1)
        else:
            render()

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

    # ---------- layout ----------
    with page_shell("Studium", active_path="/study"):
        ui.label("Studium").classes("zp-display")
        # Krátce — na mobilu úvod ukrajoval půl obrazovky, než se objevila otázka.
        ui.label(
            "Otázky rovnou se správnou odpovědí a s ustanovením. Režim kartičky "
            "odpověď schová, odhalíš ji mezerníkem."
        ).classes("zp-body zp-prose zp-mb-md")

        with ui.element("div").classes("zp-card w-full zp-mb-md"):
            with ui.row().classes("w-full zp-gap-md zp-study-controls").style(
                "flex-wrap:wrap;align-items:center;"
            ):
                sec = ui.select(
                    {"all": "Vše", **SECTION_LABEL}, value="all", label="Oblast",
                ).props("outlined dense").style("min-width:200px;")
                order = ui.select(
                    {"seq": "Po pořadí", "rand": "Náhodně"}, value="seq", label="Pořadí",
                ).props("outlined dense").style("min-width:150px;")
                sw_card = ui.switch("Režim kartičky")
                sw_only = ui.switch("Jen správná odpověď")
                # Na otázku se skáče ze seznamu vlevo, ne opisováním čísla.
                st["counts"] = ui.label("").classes("zp-body-sm zp-flex-1").style(
                    "text-align:right; min-width:200px;"
                )

        st["body"] = ui.column().classes("w-full")

        def _rebuild():
            build_pool()
            render()

        def _on_toggle():
            st["flashcard"] = sw_card.value
            st["only_correct"] = sw_only.value
            st["revealed"] = False
            render()

        sec.on_value_change(lambda: (st.update(section=sec.value), _rebuild()))
        order.on_value_change(lambda: (st.update(order=order.value), _rebuild()))
        sw_card.on_value_change(_on_toggle)
        sw_only.on_value_change(_on_toggle)

        _rebuild()
        ui.keyboard(on_key=_on_key)
