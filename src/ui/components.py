"""Sdilene UI komponenty (DRY).

Kazda komponenta je cista funkce / trida: konzumuje parametry, vraci
vytvoreny element strom. Zadne stateful singletons.
"""
from __future__ import annotations

from typing import Callable

from nicegui import ui

from src.ui.icons import I, icon


SECTION_LABEL = {
    "pravo": "Právo",
    "provadeci_predpisy": "Prováděcí předpisy",
    "jine_predpisy": "Jiné předpisy",
    "nauka_o_zbranich": "Nauka o zbraních a střelivu",
    "zdravotni_minimum": "Zdravotnické minimum",
}

SECTION_BADGE_VARIANT = {
    "pravo": "",
    "provadeci_predpisy": "neutral",
    "jine_predpisy": "neutral",
    "nauka_o_zbranich": "warning",
    "zdravotni_minimum": "success",
}


# ============================================================================
# Layout primitives
# ============================================================================

def page_header(title: str, *, subtitle: str = "", icon_name: str | None = None, eyebrow: str = ""):
    """Jednotny nadpis stranky: (eyebrow) + H1 + optional podtitulek."""
    with ui.element("div").classes("zp-page-header w-full"):
        if eyebrow:
            with ui.element("div").classes("zp-eyebrow"):
                if icon_name:
                    icon(icon_name, size="xs")
                ui.label(eyebrow)
        ui.label(title).classes("zp-display")
        if subtitle:
            ui.label(subtitle).classes("zp-body zp-prose").style("margin-top: .25rem;")


def back_home_button(label: str = "Zpět"):
    """„Zpet na prehled" tlacitko, flat style."""
    return ui.button(label, icon=I["home"], on_click=lambda: ui.navigate.to("/")).props("flat")


def section_badge(section_key: str | None):
    """Barevne badge pro sekci otazky."""
    if not section_key:
        return
    variant = SECTION_BADGE_VARIANT.get(section_key, "neutral")
    label = SECTION_LABEL.get(section_key, section_key)
    cls = f"zp-badge {variant}".strip()
    ui.html(f'<span class="{cls}">{label}</span>')


def progress_bar(ratio: float, *, variant: str = "primary"):
    """Univerzalni progress bar. variant: primary | success | danger."""
    pct = max(0.0, min(1.0, ratio)) * 100
    # make sure a sliver is visible even at 0%
    display_pct = max(0.5, pct)
    cls = "zp-progress"
    if variant == "success":
        cls += " success"
    elif variant == "danger":
        cls += " danger"
    ui.html(f'<div class="{cls}"><div style="width:{display_pct}%;"></div></div>')


# ============================================================================
# Cards
# ============================================================================

def stat_card(label: str, value: str, *, sub: str = "", accent: str | None = None, icon_name: str | None = None):
    """Statisticka karta s velkym cislem. accent: success | danger | warning | primary."""
    accent_cls = f" zp-accent-{accent}" if accent in {"success", "danger", "warning", "primary"} else ""
    with ui.element("div").classes(f"zp-card{accent_cls}"):
        with ui.row().classes("zp-row-between zp-gap-sm"):
            ui.label(label).classes("zp-caption").style("text-transform: uppercase;")
            if icon_name:
                icon(icon_name, size="sm", color="var(--zp-text-soft)")
        ui.label(value).classes("zp-metric zp-mt-xs")
        if sub:
            ui.label(sub).classes("zp-body-sm zp-mt-xs")


def mode_tile(*, path: str, icon_name: str, title: str, description: str,
              badge: str | int | None = None, disabled: bool = False, highlight: bool = False,
              cta: str | None = None):
    """Dashboard tile. highlight=True -> primarni gradient.

    Sjednoceni _tile + _primary_tile z puvodniho app.py.
    """
    cls = "zp-tile primary" if highlight else "zp-tile"
    if disabled:
        cls += " zp-tile-disabled"

    on_click: Callable = (lambda: None) if disabled else (lambda p=path: ui.navigate.to(p))

    with ui.element("div").classes(cls).on("click", on_click):
        if badge is not None and not disabled:
            ui.html(f'<span class="zp-tile-badge">{badge}</span>')
        with ui.row().classes("zp-row zp-gap-md zp-nowrap w-full"):
            # Icon bubble
            bubble_bg = "rgba(255,255,255,0.15)" if highlight else "var(--zp-primary-soft)"
            bubble_color = "white" if highlight else "var(--zp-primary)"
            with ui.element("div").classes("tile-icon-bubble").style(
                f"width: 42px; height: 42px; flex-shrink: 0; "
                f"display: flex; align-items: center; justify-content: center; "
                f"border-radius: 12px; background: {bubble_bg};"
            ):
                icon(icon_name, size="md", color=bubble_color)
            # Text
            with ui.column().classes("zp-col zp-flex-1 zp-gap-xs"):
                ui.label(title).classes("zp-tile-title")
                ui.label(description).classes("zp-body-sm")
                if cta:
                    ui.label(cta).classes("zp-body-sm").style(
                        "color: var(--zp-accent); font-weight: 600; margin-top: .25rem;"
                    )
            if highlight:
                icon("next", size="md").style("color: white; opacity: .8;")


# ============================================================================
# Hero banners
# ============================================================================

def hero_primary(*, title: str, subtitle: str, cta_label: str, cta_target: str, icon_name: str | None = None):
    """Dashboard top-of-page CTA."""
    with ui.element("div").classes("zp-hero zp-hero-primary"):
        with ui.row().classes("zp-row-between zp-nowrap zp-gap-md w-full"):
            with ui.column().classes("zp-col zp-gap-xs zp-flex-1"):
                ui.label(title).classes("zp-h1").style("color: white; margin: 0;")
                ui.label(subtitle).classes("zp-body").style(
                    "color: rgba(255,255,255,0.88); margin: 0;"
                )
            ui.button(cta_label, icon=I["next"],
                      on_click=lambda: ui.navigate.to(cta_target)).props(
                "size=lg color=amber unelevated"
            ).style("color: #111827; font-weight: 700;")


def hero_result(*, passed: bool, title: str, subtitle: str, icon_name: str):
    """Zeleny/cerveny banner pass/fail (exam, marathon done)."""
    cls = "zp-hero zp-hero-success" if passed else "zp-hero zp-hero-danger"
    with ui.element("div").classes(cls):
        with ui.column().classes("zp-col").style("align-items: center; gap: .35rem;"):
            icon(icon_name, size="2xl", color="white")
            ui.label(title).classes("zp-hero-title").style("margin: 0;")
            ui.label(subtitle).classes("zp-hero-sub").style("margin: 0;")


# ============================================================================
# Empty state
# ============================================================================

def empty_state(*, icon_name: str, heading: str, subtitle: str,
                cta_label: str = "Zpět na přehled", cta_target: str = "/"):
    """Konzistentni prazdny stav."""
    with ui.element("div").classes("zp-empty-container"):
        with ui.element("div").classes("zp-empty-icon-wrap"):
            icon(icon_name, size="lg")
        ui.label(heading).classes("zp-h1 zp-mb-sm")
        ui.label(subtitle).classes("zp-body zp-prose").style("margin: 0 auto;")
        ui.button(cta_label, icon=I["home"],
                  on_click=lambda: ui.navigate.to(cta_target)).props("flat").style("margin-top: 1rem;")


# ============================================================================
# Rating bar (SRS)
# ============================================================================

def rating_bar(on_rate: Callable[[str], None]):
    """FSRS rating: Again / Hard / Good / Easy.

    Kazdy rating = current answer + kdy ukaz otazku priste + next question.
    Buttony maji vestavene obtiznostni hint (=kdy se vrati) pro jasnost.
    """
    with ui.element("div").classes("zp-col w-full").style("align-items: center; gap: .25rem;"):
        ui.label("Ohodnoť obtížnost — automaticky jedeš dál").classes("zp-body-sm").style(
            "text-align: center; font-weight: 500;"
        )
        ui.label("Algoritmus rozhodne, kdy ti otázku ukáže znovu").classes("zp-caption")
    buttons = [
        ("again",  "Znovu",   I["rate_again"],  "1", "za < 10 min"),
        ("hard",   "Těžké",   I["rate_hard"],   "2", "za ~1 den"),
        ("good",   "Dobré",   I["rate_good"],   "3", "za pár dní"),
        ("easy",   "Snadné",  I["rate_easy"],   "4", "za týden+"),
    ]
    with ui.element("div").classes("zp-rate-bar zp-mt-sm"):
        for key, label, glyph, kbd, hint in buttons:
            btn = ui.button(on_click=lambda k=key: on_rate(k)).props(
                "flat no-caps padding=none"
            ).classes(f"zp-rate-btn {key}")
            with btn:
                ui.icon(glyph).classes("text-lg")
                ui.html(f"<span class='zp-rate-label'>{label}</span>")
                ui.html(f"<span class='zp-rate-hint'>{hint}</span>")
                ui.html(f"<span class='zp-kbd' style='font-size:.65rem;'>{kbd}</span>")

    # Keyboard shortcuts
    def _on_key(e):
        if not e.action.keydown:
            return
        k = str(e.key).lower() if e.key else ""
        mapping = {"4": "easy", "3": "good", "2": "hard", "1": "again"}
        if k in mapping:
            on_rate(mapping[k])

    ui.keyboard(on_key=_on_key)


# ============================================================================
# Confirm button (double-click)
# ============================================================================

def confirm_button(label: str, *, on_confirm: Callable[[], None],
                   confirm_label: str = "OPRAVDU SMAZAT VŠE",
                   icon_name: str = "delete",
                   color: str = "negative"):
    """Dvojklikove potvrzeni destruktivni akce."""
    state = {"armed": False}

    def _click():
        if not state["armed"]:
            state["armed"] = True
            btn.text = confirm_label
            btn.update()
            ui.notify("Klikni ještě jednou pro potvrzení",
                      color="warning", position="top", timeout=3000)
            ui.timer(3.0, lambda: _disarm(), once=True)
        else:
            on_confirm()
            _disarm()

    def _disarm():
        state["armed"] = False
        btn.text = label
        btn.update()

    btn = ui.button(label, icon=I[icon_name], on_click=_click).props(f"color={color}")
    return btn


# ============================================================================
# Query params helper
# ============================================================================

def get_query_params() -> dict:
    """Bezpecne cte query parametry aktualniho requestu."""
    try:
        from nicegui import context
        req = context.client.request
        return dict(req.query_params) if req else {}
    except Exception:
        return {}


def query_int(name: str, default: int) -> int:
    try:
        return int(get_query_params().get(name, default))
    except (ValueError, TypeError):
        return default


def query_str(name: str, default: str) -> str:
    return get_query_params().get(name, default)


# ============================================================================
# Bookmark helper
# ============================================================================

def is_flagged(db, qid: str) -> bool:
    from src.db.store import get_bookmark
    bm = get_bookmark(db, qid)
    return bool(bm and bm.get("flagged"))


def toggle_flagged(db, qid: str) -> bool:
    """Prepne flag a vrati novy stav."""
    from src.db.store import set_bookmark
    new_state = not is_flagged(db, qid)
    set_bookmark(db, qid, flagged=new_state)
    return new_state


# ============================================================================
# QuizSession — genericky runner pro vsechny kviz rezimy
# ============================================================================

from dataclasses import dataclass, field


@dataclass
class QuizSession:
    """Generický runner pro vsechny kviz rezimy (random / mistakes / flagged / mastery).

    Marathon, SRS a Exam potrebuji specificke state navic (persistent position,
    rating bar, timer), tak si spoustenim vlastni loop s pouzitim QuizCard + helperu.
    """
    pool: list[dict]
    mode: str
    empty_icon: str = "info"
    empty_heading: str = "Prázdné"
    empty_subtitle: str = "Nic k zobrazení."
    on_record: Callable[[str, str, str, int], None] | None = None
    # (question_id, chosen, correct, time_ms) → void

    def run(self):
        """Pusti kviz loop uvnitr aktualniho NiceGUI kontextu."""
        from src.ui.quiz import QuizCard
        import random as _random

        if not self.pool:
            empty_state(
                icon_name=self.empty_icon,
                heading=self.empty_heading,
                subtitle=self.empty_subtitle,
            )
            return

        queue = self.pool[:]
        _random.shuffle(queue)
        state = {"index": 0, "correct": 0, "container": None}

        def render():
            state["container"].clear()
            with state["container"]:
                total = len(queue)
                if state["index"] >= total:
                    pct = round(state["correct"] / total * 100, 1)
                    hero_result(
                        passed=pct >= 85,
                        title=f"Hotovo — {pct} %",
                        subtitle=f"{state['correct']} / {total} správně",
                        icon_name="trophy" if pct >= 85 else "insights",
                    )
                    with ui.row().classes("zp-row zp-gap-sm zp-mt-lg").style("justify-content: center;"):
                        ui.button("Nové kolo", icon=I["refresh"], on_click=_restart).props(
                            "color=primary unelevated"
                        )
                        back_home_button()
                    return
                q = queue[state["index"]]
                qid = q["id"]
                from src.db.store import get_db
                db = get_db()
                card = QuizCard(
                    q,
                    instant_feedback=True,
                    progress_label=f"{state['index']+1} / {total}  ·  správně {state['correct']}",
                    progress_ratio=state["index"] / total,
                    is_bookmarked=is_flagged(db, qid),
                    on_answer=lambda chosen, ms, q=q: _on_answer(q, chosen, ms),
                    on_next=_advance,
                    on_bookmark_toggle=lambda q=q: toggle_flagged(db, q["id"]),
                )
                card.render()

        def _on_answer(q, chosen, ms):
            if self.on_record:
                self.on_record(q["id"], chosen, q["correct"], ms)
            if chosen == q["correct"]:
                state["correct"] += 1

        def _advance():
            state["index"] += 1
            render()

        def _restart():
            _random.shuffle(queue)
            state["index"] = 0
            state["correct"] = 0
            render()

        state["container"] = ui.column().classes("w-full")
        render()
