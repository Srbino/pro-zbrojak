"""Sdilene UI komponenty (DRY).

Kazda komponenta je cista funkce / trida: konzumuje parametry, vraci
vytvoreny element strom. Zadne stateful singletons.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from src.db import law_refs, traps
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


def law_reference_chip(pdf_number: int, panel) -> bool:
    """Odkaz na ustanovení — do řádku k záložce pod otázkou.

    Tlačítko samo o sobě jen říká, které ustanovení odpověď zakládá. Znění se
    rozbalí AŽ NA KLIK do `panel` (ne při najetí myší) — nápověda má přijít,
    když si o ni člověk řekne, a má být čitelná, ne bublina pod kurzorem.
    """
    ref = law_refs.ref_for(pdf_number)
    if not ref:
        return False

    state = {"open": False}

    def toggle():
        state["open"] = not state["open"]
        panel.clear()
        chip.props(f"color={'primary' if state['open'] else 'grey-7'}")
        if not state["open"]:
            return
        with panel:
            with ui.element("div").classes("zp-law-ref"):
                if ref.get("quote"):
                    ui.label(f"„{ref['quote']}”").classes("zp-law-ref-quote")
                with ui.row().classes("zp-row zp-nowrap items-center zp-gap-sm zp-mt-sm"):
                    ui.link(
                        f"Otevřít {ref['ref']} v e-Sbírce", ref["url"], new_tab=True
                    ).classes("zp-law-ref-link")
                    icon("external", size="sm")

    chip = ui.button(ref["ref"], icon=I["law"], on_click=toggle)
    chip.props("flat dense no-caps color=grey-7").classes("zp-law-chip")
    return True


def trap_chip(pdf_number: int, panel) -> bool:
    """Tlačítko „Chyták" — rozbalí, čím přesně distraktor mění správnou odpověď.

    Ukazuje se až po odpovědi. Písmena možností se schválně neuvádějí: pořadí
    A/B/C se míchá (viz src/ui/shuffle.py), takže by nic neříkala — rozhoduje
    znění.
    """
    trap = traps.trap_for(pdf_number)
    if not trap:
        return False

    state = {"open": False}

    def toggle():
        state["open"] = not state["open"]
        panel.clear()
        chip.props(f"color={'warning' if state['open'] else 'grey-7'}")
        if not state["open"]:
            return
        with panel:
            with ui.element("div").classes("zp-trap-box"):
                ui.label("Co bylo nastražené").classes("zp-trap-title")

                for marker in trap.get("zadani", []):
                    with ui.row().classes("zp-row zp-gap-sm items-baseline zp-trap-item"):
                        ui.label(f"v zadání — {marker['typ']}:").classes("zp-trap-op")
                        ui.label(f"„{marker['slovo']}”").classes("zp-trap-stem")

                for past in trap.get("pasti", []):
                    with ui.element("div").classes("zp-trap-item"):
                        for change in past["zmeny"]:
                            _render_trap_change(change)

                if trap.get("dvojnici"):
                    others = ", ".join(f"č. {n}" for n in trap["dvojnici"])
                    with ui.element("div").classes("zp-trap-item"):
                        ui.label(
                            f"Skoro stejné zadání má i {others} — ale jinou správnou "
                            "odpověď. Nespleť si je."
                        ).classes("zp-trap-op")

    chip = ui.button("Chyták", icon=I["trap"], on_click=toggle)
    chip.props("flat dense no-caps color=grey-7").classes("zp-law-chip")
    return True


def _render_trap_change(change: dict) -> None:
    typ = change["typ"]
    with ui.row().classes("zp-row zp-gap-sm items-baseline").style("flex-wrap: wrap;"):
        if typ == "vsunuto":
            ui.label("navíc:").classes("zp-trap-op")
            ui.label(f"„{change['past']}”").classes("zp-trap-bad")
        elif typ == "vypuštěno":
            ui.label("chybí:").classes("zp-trap-op")
            ui.label(f"„{change['spravne']}”").classes("zp-trap-good")
        else:
            ui.label("místo").classes("zp-trap-op")
            ui.label(f"„{change['spravne']}”").classes("zp-trap-good")
            ui.label("bylo").classes("zp-trap-op")
            ui.label(f"„{change['past']}”").classes("zp-trap-bad")


def law_reference(pdf_number: int) -> bool:
    """Odkaz na ustanovení zákona v e-Sbírce MV ČR. Vrací False, když odkaz není.

    Vykresluje se až po odhalení odpovědi — je to vysvětlení („proč to tak je"),
    ne nápověda. Znění zákona nedržíme, klikne se přímo na oficiální text.
    """
    ref = law_refs.ref_for(pdf_number)
    if not ref:
        return False

    with ui.element("div").classes("zp-law-ref"):
        with ui.row().classes("zp-row zp-nowrap items-center zp-gap-sm"):
            icon("law", size="sm")
            ui.link(ref["ref"], ref["url"], new_tab=True).classes("zp-law-ref-link")
            icon("external", size="sm")
        if ref.get("quote"):
            ui.label(f"„{ref['quote']}”").classes("zp-law-ref-quote")
    return True


class QuestionNavigator:
    """Levý panel se seznamem otázek — hledání + proklik na libovolnou.

    Seznam se záměrně nevykresluje celý (837 řádků s textem je znát na rychlosti
    načtení). Ukazuje se okno kolem aktuální otázky a hledání ho nahradí shodami;
    na cokoli dál se dá skočit napsáním čísla.
    """

    WINDOW = 60  # kolik otázek kolem aktuální se ukáže bez hledání
    MAX_RESULTS = 80  # strop pro výsledky hledání

    # Filtry. Seznam 837 položek bez nich je jen k listování, ne k práci.
    FILTERS: tuple[tuple[str, str], ...] = (
        ("", "Vše"),
        ("wrong", "Chybné"),
        ("flagged", "Označené"),
        ("trap", "Chytáky"),
    )

    def __init__(
        self,
        questions: list[dict],
        *,
        current_index: int,
        status: dict[str, str] | None = None,
        on_pick: Callable[[int], None],
        flagged: set[str] | None = None,
        filters: tuple[tuple[str, str], ...] | None = None,
        notes: dict[str, str] | None = None,
    ):
        self.questions = questions
        self.current_index = current_index
        self.status = status or {}
        self.on_pick = on_pick
        self.flagged = flagged or set()
        # Studium má stejné stavy, ale jinak se jim říká — „Umím" místo
        # „Chybné". Popisky si proto smí režim přepsat.
        self.filters = filters or self.FILTERS
        # Krátký údaj u položky — třeba kolikrát na ní člověk chyboval.
        self.notes = notes or {}
        self._trap_numbers = traps.trap_numbers()
        self._list = None
        self._query = ""
        self._filter = ""
        self._info = None
        self._filter_buttons: dict[str, ui.button] = {}

    def render(self):
        # Na mobilu je panel vysunovací. Kdyby se kreslil rovnou, sežral by
        # celou první obrazovku a k zadání otázky by se člověk dostal až
        # po odscrollování seznamu.
        self._toggle = ui.button(
            f"Otázky ({len(self.questions)})", icon=I["menu"], on_click=self._open
        ).props("flat dense no-caps color=primary").classes("zp-qnav-toggle")

        self._backdrop = ui.element("div").classes("zp-qnav-backdrop")
        self._backdrop.on("click", self._close)

        self._panel = ui.element("div").classes("zp-qnav")
        with self._panel:
            with ui.row().classes("zp-row-between zp-nowrap w-full zp-mb-sm"):
                ui.label("Otázky").classes("zp-qnav-title")
                ui.label(f"{len(self.questions)}").classes("zp-caption zp-flex-1").style(
                    "text-align: right;"
                )
                ui.button(icon=I["close"], on_click=self._close).props(
                    "flat dense round size=sm"
                ).classes("zp-qnav-close").tooltip("Zavřít seznam")

            search = ui.input(placeholder="Hledat nebo číslo otázky…").props(
                "outlined dense clearable"
            ).classes("w-full zp-qnav-search")
            search.on("update:model-value", lambda e: self._on_search(e.args))

            with ui.row().classes("zp-qnav-filters"):
                for key, label in self.filters:
                    btn = ui.button(
                        label, on_click=lambda k=key: self._set_filter(k)
                    ).props("dense no-caps size=sm flat color=primary").classes("zp-qnav-filter")
                    self._filter_buttons[key] = btn

            self._info = ui.label("").classes("zp-caption zp-qnav-info")
            self._list = ui.element("div").classes("zp-qnav-list")
            self._sync_filter_buttons()
            self._fill()

    def _set_filter(self, key: str) -> None:
        self._filter = "" if key == self._filter else key
        self._sync_filter_buttons()
        self._fill()

    def _sync_filter_buttons(self) -> None:
        for key, btn in self._filter_buttons.items():
            btn.classes(
                add="active" if key == self._filter else "",
                remove="" if key == self._filter else "active",
            )

    def _passes_filter(self, q: dict) -> bool:
        if self._filter in ("wrong", "correct"):
            return self.status.get(q["id"]) == self._filter
        if self._filter == "flagged":
            return q["id"] in self.flagged
        if self._filter == "trap":
            return q["pdf_number"] in self._trap_numbers
        return True

    def _open(self) -> None:
        self._panel.classes(add="open")
        self._backdrop.classes(add="open")

    def _close(self) -> None:
        self._panel.classes(remove="open")
        self._backdrop.classes(remove="open")

    def _on_search(self, value) -> None:
        self._query = (value or "").strip() if isinstance(value, str) else ""
        self._fill()

    def _matches(self) -> tuple[list[tuple[int, dict]], str]:
        indexed = [(i, q) for i, q in enumerate(self.questions) if self._passes_filter(q)]
        query = self._query.lower()

        if not query:
            if self._filter:
                hits = indexed[: self.MAX_RESULTS]
                note = f"{len(indexed)} otázek v tomto filtru"
                if len(indexed) > self.MAX_RESULTS:
                    note += f", zobrazeno prvních {self.MAX_RESULTS}"
                return hits, note
            lo = max(0, self.current_index - self.WINDOW // 2)
            window = indexed[lo: lo + self.WINDOW]
            note = (
                f"okolí aktuální otázky ({lo + 1}–{lo + len(window)}) "
                "— hledej nebo napiš číslo"
                if len(self.questions) > self.WINDOW else ""
            )
            return window, note

        if query.isdigit():
            hits = [(i, q) for i, q in indexed if str(q["pdf_number"]).startswith(query)]
        else:
            hits = [
                (i, q) for i, q in indexed
                if query in q["question"].lower()
                or any(query in opt.lower() for opt in q["options"].values())
            ]

        note = f"nalezeno {len(hits)}"
        if len(hits) > self.MAX_RESULTS:
            note += f", zobrazeno prvních {self.MAX_RESULTS}"
        return hits[: self.MAX_RESULTS], note

    def _fill(self) -> None:
        rows, note = self._matches()
        self._info.text = note
        self._list.clear()
        with self._list:
            if not rows:
                ui.label("Nic nenalezeno.").classes("zp-caption")
                return
            for index, q in rows:
                self._row(index, q)

    def _row(self, index: int, q: dict) -> None:
        cls = "zp-qnav-item"
        state = self.status.get(q["id"])
        if state:
            cls += f" {state}"
        if index == self.current_index:
            cls += " current"

        item = ui.element("div").classes(cls)
        # Zavřít dřív, než se překreslí obsah — jinak by panel na mobilu
        # zůstal otevřený přes nově vybranou otázku.
        item.on("click", lambda e, i=index: (self._close(), self.on_pick(i)))
        with item:
            ui.label(str(q["pdf_number"])).classes("zp-qnav-num")
            ui.label(q["question"]).classes("zp-qnav-text")
            poznamka = self.notes.get(q["id"])
            if poznamka:
                ui.html(f'<span class="zp-qnav-note">{poznamka}</span>')


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

def format_interval(delta) -> str:
    """Lidsky citelny interval do dalsiho review."""
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 3600:
        return f"za {max(1, seconds // 60)} min"
    if seconds < 86400:
        return f"za {seconds // 3600} h"
    days = seconds // 86400
    if days < 31:
        return f"za {days} {'den' if days == 1 else 'dny' if days < 5 else 'dní'}"
    months = round(days / 30.4)
    if months < 12:
        return f"za {months} {'měsíc' if months == 1 else 'měsíce' if months < 5 else 'měsíců'}"
    years = round(days / 365)
    return f"za {years} {'rok' if years == 1 else 'roky' if years < 5 else 'let'}"


def rating_bar(on_rate: Callable[[str], None], *, intervals: dict[str, str] | None = None):
    """FSRS rating: Again / Hard / Good / Easy.

    `intervals` je {klic: text}, kdy se otazka vrati. Patri na tlacitko PREDEM
    — z hlasky po kliknuti uz se rozhodovat neda.
    """
    with ui.element("div").classes("zp-col w-full").style("align-items: center; gap: .25rem;"):
        ui.label("Ohodnoť obtížnost — automaticky jedeš dál").classes("zp-body-sm").style(
            "text-align: center; font-weight: 500;"
        )
        ui.label("Podle hodnocení se rozhodne, kdy otázku uvidíš znovu").classes("zp-caption")
    intervals = intervals or {}
    # Bez ikon. Šipky u hodnocení nic neříkaly a jen soupeřily o pozornost
    # s tím jediným, co je tu podstatné — za jak dlouho se otázka vrátí.
    buttons = [
        ("again",  "Znovu",   "1", intervals.get("again", "brzy")),
        ("hard",   "Těžké",   "2", intervals.get("hard", "za ~1 den")),
        ("good",   "Dobré",   "3", intervals.get("good", "za pár dní")),
        ("easy",   "Snadné",  "4", intervals.get("easy", "za týden+")),
    ]
    with ui.element("div").classes("zp-rate-bar zp-mt-sm"):
        for key, label, kbd, hint in buttons:
            btn = ui.button(on_click=lambda k=key: on_rate(k)).props(
                "flat no-caps padding=none"
            ).classes(f"zp-rate-btn {key}")
            with btn:
                ui.html(
                    f"<span class='zp-rate-key'>{kbd}</span>"
                    f"<span class='zp-rate-label'>{label}</span>"
                    f"<span class='zp-rate-hint'>{hint}</span>"
                )

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
                   dialog_message: str = "Tato akce je nevratná. Opravdu chceš pokračovat?",
                   icon_name: str = "delete",
                   color: str = "negative"):
    """Potvrzovaci dialog pro destruktivni akce.

    Klik na tlacitko → modalni dialog se 2 tlacitky (zrusit + potvrdit).
    """
    # Dialog — oddeleny CM pro kazdy level (vice spolehlive v NiceGUI)
    dialog = ui.dialog()

    def _confirm():
        try:
            on_confirm()
        except Exception as e:
            ui.notify(f"Chyba: {e}", color="negative", position="top")
            return
        dialog.close()

    with dialog:
        with ui.card().style("max-width: 420px; padding: 1.5rem;"):
            with ui.row().classes("zp-row zp-gap-sm zp-nowrap w-full zp-mb-sm"):
                icon("warning", size="md", color="var(--zp-danger)")
                ui.label("Potvrzení").classes("zp-h2").style("margin: 0;")
            ui.label(dialog_message).classes("zp-body").style("margin-bottom: 1rem;")
            with ui.row().classes("w-full zp-gap-sm").style("justify-content: flex-end;"):
                ui.button("Zrušit", on_click=dialog.close).props("flat")
                ui.button(confirm_label, icon=I[icon_name], on_click=_confirm).props(
                    f"color={color} unelevated"
                )

    btn = ui.button(label, icon=I[icon_name], on_click=dialog.open).props(f"color={color}")
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

def is_flagged(db, user_email: str, qid: str) -> bool:
    from src.db.store import get_bookmark
    bm = get_bookmark(db, user_email, qid)
    return bool(bm and bm.get("flagged"))


def toggle_flagged(db, user_email: str, qid: str) -> bool:
    """Prepne flag a vrati novy stav."""
    from src.db.store import set_bookmark
    new_state = not is_flagged(db, user_email, qid)
    set_bookmark(db, user_email, qid, flagged=new_state)
    return new_state


# ============================================================================
# QuizSession — genericky runner pro vsechny kviz rezimy
# ============================================================================

@dataclass
class QuizSession:
    """Generický runner pro vsechny kviz rezimy (random / mistakes / flagged / mastery).

    Marathon, SRS a Exam potrebuji specificke state navic (persistent position,
    rating bar, timer), tak si spoustenim vlastni loop s pouzitim QuizCard + helperu.
    """
    pool: list[dict]
    mode: str
    user_email: str = ""
    empty_icon: str = "info"
    empty_heading: str = "Prázdné"
    empty_subtitle: str = "Nic k zobrazení."
    on_record: Callable[[str, str, str, int], None] | None = None
    # (question_id, chosen, correct, time_ms) → void
    show_navigator: bool = False  # levý panel se seznamem otázek + hledáním
    # Míchat se hodí u volného procvičování. Když si pořadí určuje volající
    # (řazení podle počtu chyb), zamíchání by ho zahodilo.
    shuffle: bool = True
    notes: dict[str, str] | None = None   # popisek u položky v navigátoru

    def run(self):
        """Pusti kviz loop uvnitr aktualniho NiceGUI kontextu."""
        import random as _random

        from src.ui.quiz import QuizCard

        if not self.pool:
            empty_state(
                icon_name=self.empty_icon,
                heading=self.empty_heading,
                subtitle=self.empty_subtitle,
            )
            return

        queue = self.pool[:]
        if self.shuffle:
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

                # Obal musí mít vždy plnou šířku — rodičovský sloupec má
                # align-items: flex-start, takže bezešvý div by se scvrkl na
                # obsah a karta by skončila u levého okraje místo na středu.
                with ui.element("div").classes(
                    "zp-quiz-with-nav" if self.show_navigator else "w-full"
                ):
                    if self.show_navigator:
                        _render_navigator(db, queue, state["index"])
                    with ui.element("div").classes(
                        "zp-quiz-main" if self.show_navigator else "w-full"
                    ):
                        QuizCard(
                            q,
                            user_email=self.user_email,
                            instant_feedback=True,
                            progress_label=(
                                f"{state['index']+1} / {total}"
                                f"  ·  správně {state['correct']}"
                            ),
                            progress_ratio=state["index"] / total,
                            is_bookmarked=is_flagged(db, self.user_email, qid),
                            on_answer=lambda chosen, ms, q=q: _on_answer(q, chosen, ms),
                            on_next=_advance,
                            on_bookmark_toggle=lambda q=q: toggle_flagged(
                                db, self.user_email, q["id"]
                            ),
                        ).render()

        def _render_navigator(db, queue, current):
            """Seznam otázek kola. Na rozdíl od marathonu se tu smí skákat i dopředu —
            není to sekvenční průchod s uloženou pozicí, jen jedno kolo procvičování."""
            from src.db.store import last_answers

            answered = last_answers(db, self.user_email, [q["id"] for q in queue])
            status = {
                q["id"]: ("correct" if answered[q["id"]] == q["correct"] else "wrong")
                for q in queue
                if q["id"] in answered
            }
            from src.db.store import all_flagged
            QuestionNavigator(
                queue, current_index=current, status=status, on_pick=_goto,
                flagged=set(all_flagged(db, self.user_email)),
                notes=self.notes,
            ).render()

        def _goto(index: int):
            state["index"] = max(0, min(index, len(queue) - 1))
            render()

        def _on_answer(q, chosen, ms):
            if self.on_record:
                self.on_record(q["id"], chosen, q["correct"], ms)
            if chosen == q["correct"]:
                state["correct"] += 1

        def _advance():
            state["index"] += 1
            render()

        def _restart():
            if self.shuffle:
                _random.shuffle(queue)
            state["index"] = 0
            state["correct"] = 0
            render()

        state["container"] = ui.column().classes("w-full")
        render()
