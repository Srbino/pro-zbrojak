"""Quiz card — zobrazeni jedne otazky a sber odpovedi.

Pouziva `src.ui.icons` a `src.ui.components` — bez emoji, bez dupliciti.
"""
from __future__ import annotations

import time
from typing import Callable

from nicegui import ui

from src.ui.icons import I, icon
from src.ui.components import (
    SECTION_LABEL, SECTION_BADGE_VARIANT, section_badge, progress_bar,
)


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
        self.start_ts = time.monotonic()
        self.answered: str | None = None
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
                ui.label(f"č. {self.q['pdf_number']}").classes("zp-caption").style(
                    "margin-left: .75rem;"
                )

            # Main question card
            with ui.element("div").classes("zp-card").style("padding: 1.5rem;"):
                if self.q.get("image"):
                    self._render_image()
                ui.label(self.q["question"]).classes("zp-h2 zp-mb-md")

                with ui.column().classes("w-full zp-gap-sm"):
                    for key in ("A", "B", "C"):
                        text = _escape(self.q["options"][key])
                        html = (
                            f'<button class="zp-opt" data-key="{key}">'
                            f'<span class="opt-key">{key.lower()}</span>{text}</button>'
                        )
                        el = ui.html(html).classes("w-full")
                        el.on("click", lambda e, k=key: self._handle_click(k))
                        self._opt_elements[key] = el

            # Footer — VYSTREDENY: bookmark + next button vedle sebe, centered
            with ui.row().classes("w-full zp-mt-md").style(
                "justify-content: center; align-items: center; gap: 1rem;"
            ):
                bm_key = "bookmark" if self.is_bookmarked else "bookmark_off"
                self._bookmark_btn = ui.button(
                    icon=I[bm_key],
                    on_click=self._toggle_bookmark,
                ).props(
                    f"flat dense round {'color=amber' if self.is_bookmarked else 'color=grey-7'}"
                ).tooltip("Označit otázku (F)")

                if self.show_next_button:
                    self._next_btn = ui.button(
                        "Další", icon=I["next"], on_click=self._do_next
                    ).props("color=primary unelevated size=md")
                    self._next_btn.visible = False

        self._kb = ui.keyboard(on_key=self._on_key)

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
            if key_raw in ("1", "a"):
                self._handle_click("A")
            elif key_raw in ("2", "b"):
                self._handle_click("B")
            elif key_raw in ("3", "c"):
                self._handle_click("C")
        else:
            if key_raw in ("enter", " ", "spacebar"):
                self._do_next()
        if key_raw == "f":
            self._toggle_bookmark()

    def _handle_click(self, key: str):
        if self.answered is not None:
            return
        self.answered = key
        elapsed_ms = int((time.monotonic() - self.start_ts) * 1000)
        if self.on_answer:
            self.on_answer(key, elapsed_ms)

        if self.instant_feedback:
            correct = self.q["correct"]
            for k, el in self._opt_elements.items():
                text = _escape(self.q["options"][k])
                classes = "zp-opt disabled"
                if k == correct:
                    classes += " correct"
                elif k == key:
                    classes += " wrong"
                else:
                    classes += " dimmed"
                html = (
                    f'<button class="{classes}" data-key="{k}">'
                    f'<span class="opt-key">{k.lower()}</span>{text}</button>'
                )
                el.set_content(html)
            if hasattr(self, "_next_btn"):
                self._next_btn.visible = True
                self._next_btn.update()
        else:
            # Exam mode: highlight only selected (no correctness)
            for k, el in self._opt_elements.items():
                text = _escape(self.q["options"][k])
                selected = (
                    " style=\"border-color: var(--zp-primary); background: var(--zp-primary-soft);\""
                    if k == key else ""
                )
                html = (
                    f'<button class="zp-opt disabled" data-key="{k}"{selected}>'
                    f'<span class="opt-key">{k.lower()}</span>{text}</button>'
                )
                el.set_content(html)
            ui.timer(0.25, self._do_next, once=True)

    def _do_next(self):
        if self.on_next:
            self.on_next()

    def _toggle_bookmark(self):
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
