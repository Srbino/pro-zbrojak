"""Quiz card — zobrazeni jedne otazky a sber odpovedi.

Pouziva `src.ui.icons` a `src.ui.components` — bez emoji, bez dupliciti.
"""
from __future__ import annotations

import re
import time
from collections.abc import Callable

from nicegui import ui

from src.db import traps
from src.ui.components import (
    law_reference_chip,
    progress_bar,
    section_badge,
    trap_chip,
)
from src.ui.icons import I
from src.ui.shuffle import display_letter, option_order, to_canonical, to_shown


class QuizCard:
    """
    Zobrazi otazku, posbira odpoved, zavola callback.

    Rezimy:
        instant_feedback=True   → po odpovedi zobrazi barvy + Dalsi button
        instant_feedback=False  → tise zapise odpoved, rovnou jede dal (exam)
    """

    def __init__(
        self,
        question: dict,
        *,
        instant_feedback: bool = True,
        on_answer: Callable[[str, int], None] | None = None,
        on_next: Callable[[], None] | None = None,
        on_bookmark_toggle: Callable[[], None] | None = None,
        is_bookmarked: bool = False,
        progress_label: str = "",
        show_next_button: bool = True,
        progress_ratio: float | None = None,
        exam_mode: bool = False,
        user_email: str = "",
        preset_answer: str | None = None,
    ):
        self.q = question
        self.instant_feedback = instant_feedback
        self.on_answer = on_answer
        self.on_next = on_next
        self.on_bookmark_toggle = on_bookmark_toggle
        self.is_bookmarked = is_bookmarked
        self.progress_label = progress_label
        self.show_next_button = show_next_button
        self.progress_ratio = progress_ratio
        # U ostré zkoušky se otázky nečíslují ani neoznačují — u komise to tak taky
        # není a nemá smysl si na to zvykat.
        self.exam_mode = exam_mode
        self.start_ts = time.monotonic()
        # Pořadí možností je promíchané (viz src/ui/shuffle.py). `selected`
        # i `answered` drží ZOBRAZENÉ písmeno; ven se hlásí kanonické.
        self.order = option_order(question, user_email=user_email)
        self.selected: str | None = None  # vybráno, ale ještě nepotvrzeno
        self.answered: str | None = None
        # Prohlížení už zodpovězené otázky (návrat zpátky v historii). Karta se
        # vykreslí rovnou vyhodnocená a nejde s ní hnout — hlavně se znovu
        # nezapíše pokus, takže listování v historii nezkresluje statistiky.
        self.preset_answer = preset_answer
        self.review_mode = preset_answer is not None
        self._opt_elements: dict[str, ui.html] = {}

    def render(self):
        # Wrap whole card v narrow centered container (max 720px)
        with ui.element("div").classes("zp-quiz-wrap"):
            if self.progress_ratio is not None:
                progress_bar(self.progress_ratio)

            # Meta-row: progress label + section badge + pdf number
            with ui.row().classes("zp-row zp-nowrap w-full zp-mt-sm zp-mb-sm"):
                if self.progress_label:
                    ui.label(self.progress_label).classes("zp-body-sm zp-flex-1").style(
                        "font-weight: 500;"
                    )
                else:
                    ui.element("div").classes("zp-flex-1")
                section_badge(self.q.get("section"))
                if not self.exam_mode:
                    ui.label(f"č. {self.q['pdf_number']}").classes("zp-caption").style(
                        "margin-left: .75rem;"
                    )

            # Main question card
            with ui.element("div").classes("zp-card"):
                if self.q.get("image"):
                    self._render_image()
                # Vlastní role, ne .zp-h2 — text otázky je nejdůležitější text
                # v aplikaci a nemá se sázet stejně jako nadpis sekce.
                self._question_el = ui.html(
                    _escape(self.q["question"])
                ).classes("zp-question zp-mb-md")

                with ui.column().classes("w-full zp-gap-sm"):
                    for position, _canonical in enumerate(self.order):
                        shown = display_letter(position)
                        el = ui.html(self._option_html(shown, "zp-opt")).classes("w-full")
                        el.on("click", lambda e, k=shown: self._select(k))
                        self._opt_elements[shown] = el

            # Footer — VYSTREDENY: bookmark + next button vedle sebe, centered
            with ui.row().classes("w-full zp-mt-md").style(
                "justify-content: center; align-items: center; gap: 1rem;"
            ):
                if not self.exam_mode:
                    bm_key = "bookmark" if self.is_bookmarked else "bookmark_off"
                    self._bookmark_btn = ui.button(
                        icon=I[bm_key],
                        on_click=self._toggle_bookmark,
                    ).props(
                        f"flat dense round {'color=amber' if self.is_bookmarked else 'color=grey-7'}"
                    ).tooltip("Označit otázku (F)")

                # Odkaz do zákona se doplní sem, až bude odpověď odhalená.
                self._law_slot = ui.element("div").style("display: contents;")

                # Odpověď se odesílá až tímhle tlačítkem. Klik na možnost jen
                # vybírá — jde ji libovolně překlikat, takže omylem (třeba při
                # označování textu myší) nejde nic vyhodnotit.
                # U zkoušky se nic nevyhodnocuje — odpověď se jen potvrdí a jede
                # se dál. Popisek musí říkat, co se stane.
                self._submit_btn = ui.button(
                    "Potvrdit a dál" if self.exam_mode else "Vyhodnotit",
                    icon=I["next"] if self.exam_mode else I["check"],
                    on_click=self._submit,
                ).props("color=primary unelevated size=md")
                self._submit_btn.disable()
                if self.review_mode:
                    self._submit_btn.visible = False

                if self.show_next_button and not self.review_mode:
                    self._next_btn = ui.button(
                        "Další", icon=I["next"], on_click=self._do_next
                    ).props("color=primary unelevated size=md")
                    self._next_btn.visible = False

            # Panel se zněním zákona — rozbalí se až klikem na odkaz.
            self._law_panel = ui.element("div").classes("w-full")

        if self.review_mode:
            self._render_review()
        else:
            self._kb = ui.keyboard(on_key=self._on_key)

    def _render_review(self):
        """Vykreslí otázku rovnou vyhodnocenou podle dřív uložené odpovědi."""
        chosen_shown = to_shown(self.order, self.preset_answer)
        correct_shown = to_shown(self.order, self.q["correct"])
        for k, el in self._opt_elements.items():
            classes = "zp-opt disabled"
            if k == correct_shown:
                classes += " correct"
            elif k == chosen_shown:
                classes += " wrong"
            el.set_content(self._option_html(k, classes))
        self.answered = chosen_shown  # ať klik do možnosti nic nedělá
        self._show_law_reference()

    def _option_html(self, shown: str, classes: str) -> str:
        """HTML jedné možnosti. `shown` je písmeno, které uživatel vidí — text se
        k němu dohledá přes promíchané pořadí."""
        text = _escape(self.q["options"][to_canonical(self.order, shown)])
        # Písmeno je vlastní sloupec (flex), ne první znak textu — jinak se
        # druhý řádek zalomí pod badge místo pod začátek věty.
        return (
            f'<button class="{classes}" data-key="{shown}" type="button">'
            f'<span class="opt-key">{shown}</span>'
            f'<span class="opt-text">{text}</span></button>'
        )

    def _show_law_reference(self):
        """Doplní k záložce odkaz na ustanovení, ze kterého odpověď plyne."""
        slot = getattr(self, "_law_slot", None)
        if slot is None or self.exam_mode:
            return
        self._highlight_stem_trap()
        with slot:
            trap_chip(self.q["pdf_number"], self._law_panel)
            law_reference_chip(self.q["pdf_number"], self._law_panel)

    def _highlight_stem_trap(self):
        """Vyznačí v zadání slovo, které obrací smysl otázky („nepatří", „nejméně").

        Až po vyhodnocení — před ním by to byla nápověda, a přesně tohle
        přehlédnutí je u zkoušky ta past.
        """
        el = getattr(self, "_question_el", None)
        if el is None:
            return
        markers = traps.stem_markers(self.q["pdf_number"])
        if not markers:
            return
        html = _escape(self.q["question"])
        for word in sorted(set(markers), key=len, reverse=True):
            pattern = re.compile(rf"(?<!\w)({re.escape(_escape(word))})(?!\w)", re.IGNORECASE)
            html = pattern.sub(r'<mark class="zp-stem-mark">\1</mark>', html, count=1)
        el.set_content(html)

    def _render_image(self):
        img_src = f"/{self.q['image']}"

        # Zoom dialog — plain img (ne q-img) aby roztahovani do full size fungovalo
        with ui.dialog() as zoom:
            with ui.card().style(
                "min-width: min(90vw, 900px); max-width: 95vw; "
                "padding: 1rem; background: var(--zp-surface);"
            ):
                ui.html(
                    f'<img src="{img_src}" '
                    f'style="width: 100%; max-height: 85vh; object-fit: contain; display: block;" '
                    f'alt="Detail obrázku otázky">'
                )
                with ui.row().classes("w-full justify-end zp-mt-sm"):
                    ui.button("Zavřít", icon=I["close"], on_click=zoom.close).props("flat")

        # Inline image (clickable → opens zoom) — plain <img> wrapped in clickable button
        # Use ui.button with flat + no-caps for reliable click handler, transparent bg.
        with ui.element("div").classes("w-full").style(
            "display: flex; justify-content: center; margin-bottom: 1rem;"
        ):
            btn = ui.button(on_click=lambda: zoom.open()).props(
                "flat no-caps padding=none"
            ).classes("zp-image-wrap")
            btn.style(
                "background: transparent !important; cursor: zoom-in; "
                "border: none; padding: .5rem !important;"
            )
            with btn:
                ui.html(
                    f'<img src="{img_src}" '
                    f'style="max-height: 320px; max-width: 100%; object-fit: contain; '
                    f'display: block; pointer-events: none;" '
                    f'alt="Obrázek otázky">'
                )
                ui.html(
                    f'<span class="zp-zoom-hint"><i class="material-icons" '
                    f'style="font-size: 18px; color: white;">{I["zoom"]}</i></span>'
                )

    # ------ event handlers ------

    def _on_key(self, e):
        if not e.action.keydown:
            return
        key_raw = str(e.key).lower() if e.key else ""
        if self.answered is None:
            # Klávesa odpověď jen VYBERE, neodešle — potvrzuje se Enterem
            # nebo tlačítkem, aby omyl šel opravit.
            if key_raw in ("1", "a"):
                self._select("A")
            elif key_raw in ("2", "b"):
                self._select("B")
            elif key_raw in ("3", "c"):
                self._select("C")
            elif key_raw in ("enter", " ", "spacebar"):
                self._submit()
        else:
            if key_raw in ("enter", " ", "spacebar"):
                self._do_next()
        if key_raw == "f" and not self.exam_mode:
            self._toggle_bookmark()

    def _select(self, key: str):
        """Vybere možnost. Nic neodesílá — jde překlikávat, dokud se nepotvrdí."""
        if self.answered is not None:
            return
        self.selected = key
        for k, el in self._opt_elements.items():
            el.set_content(self._option_html(k, "zp-opt selected" if k == key else "zp-opt"))
        self._submit_btn.enable()

    def _submit(self):
        """Potvrdí vybranou odpověď."""
        if self.answered is not None or self.selected is None:
            return
        self._handle_click(self.selected)

    def _handle_click(self, key: str):
        if self.answered is not None:
            return
        self.answered = key
        self._submit_btn.visible = False
        elapsed_ms = int((time.monotonic() - self.start_ts) * 1000)
        if self.on_answer:
            # Ven vždycky kanonické písmeno z katalogu — statistiky, SRS
            # i vyhodnocení zkoušky nesmí vědět o promíchaném pořadí.
            self.on_answer(to_canonical(self.order, key), elapsed_ms)

        if self.instant_feedback:
            correct_shown = to_shown(self.order, self.q["correct"])
            for k, el in self._opt_elements.items():
                # Nezvolené možnosti se záměrně NETLUMÍ — po vyhodnocení má být
                # celá otázka pořád čitelná (člověk si ji chce přečíst znovu).
                # Zvýrazňuje se jen správná, případně chybná volba.
                classes = "zp-opt disabled"
                if k == correct_shown:
                    classes += " correct"
                elif k == key:
                    classes += " wrong"
                el.set_content(self._option_html(k, classes))
            self._show_law_reference()
            if hasattr(self, "_next_btn"):
                self._next_btn.visible = True
                self._next_btn.update()
        else:
            # Zkouška: zvýrazní se jen zvolená možnost, nikdy ne správnost.
            # `k` je ZOBRAZENÉ písmeno — text se k němu musí dohledat přes
            # promíchané pořadí, jinak se po odpovědi přepíší texty možností.
            for k, el in self._opt_elements.items():
                classes = "zp-opt disabled" + (" selected" if k == key else "")
                el.set_content(self._option_html(k, classes))
            ui.timer(0.25, self._do_next, once=True)

    def _do_next(self):
        if self.on_next:
            self.on_next()

    def _toggle_bookmark(self):
        if self.exam_mode:  # u zkoušky se otázky neoznačují
            return
        self.is_bookmarked = not self.is_bookmarked
        if self.on_bookmark_toggle:
            self.on_bookmark_toggle()
        bm_key = "bookmark" if self.is_bookmarked else "bookmark_off"
        color = "amber" if self.is_bookmarked else "grey-7"
        self._bookmark_btn.props(f"flat dense round color={color} icon={I[bm_key]}")
        ui.notify(
            "Otázka označena" if self.is_bookmarked else "Označení zrušeno",
            position="top", timeout=1500,
        )


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )
