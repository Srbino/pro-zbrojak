"""Spolecny layout (header + sidebar). Material Symbols namisto emoji."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from nicegui import ui

from src.ui.theme import apply_theme
from src.ui.icons import I, icon


@dataclass(frozen=True)
class NavItem:
    path: str
    icon_key: str
    label: str
    description: str = ""


# Jediny zdroj pravdy pro navigaci. Dashboard tiles si take ctou z nej.
NAV_ITEMS: tuple[NavItem | None, ...] = (
    NavItem("/",         "dashboard", "Přehled",           "Statistiky a doporučení"),
    None,  # separator
    NavItem("/marathon", "marathon",  "Marathon",          "Všechny otázky po pořadí"),
    NavItem("/srs",      "srs",       "Denní review",      "Spaced repetition (FSRS)"),
    NavItem("/random",   "random",    "Náhodně",           "Volné procvičování"),
    NavItem("/mistakes", "mistakes",  "Lekce z chyb",      "Jen otázky, kde jsi chyboval"),
    NavItem("/mastery",  "mastery",   "Mastery",           "90% na oblasti"),
    NavItem("/exam",     "exam",      "Simulace zkoušky",  "30 otázek, 40 minut"),
    None,
    NavItem("/flagged",  "flagged",   "Označené",          "Otázky k zamyšlení"),
    NavItem("/export",   "export",    "Export pro AI",     "Markdown pro Claude Code"),
    NavItem("/settings", "settings",  "Nastavení",         ""),
)


def nav_items_for_dashboard() -> tuple[NavItem, ...]:
    """Vraci neprazdne nav polozky krome dashboardu (pro dashboard tiles)."""
    return tuple(it for it in NAV_ITEMS if it and it.path != "/")


@contextmanager
def page_shell(title: str = "ZP Trenažér", active_path: str | None = None):
    """Stranka: header + left_drawer + container pro obsah.

    Usage:
        with page_shell("Marathon", active_path="/marathon"):
            ui.label(...)
    """
    apply_theme()

    # Header — bile pozadi, tmavy text; dark mode ridi theme.py
    with ui.header(elevated=False).style(
        "background: var(--zp-surface); color: var(--zp-text);"
        "border-bottom: 1px solid var(--zp-border);"
    ):
        with ui.row().classes("zp-row-between zp-nowrap w-full").style(
            "padding: .35rem .75rem; min-height: 56px;"
        ):
            with ui.row().classes("zp-row zp-gap-sm zp-nowrap"):
                ui.button(icon=I["menu"], on_click=lambda: drawer.toggle()).props(
                    "flat dense round color=primary size=md"
                ).tooltip("Menu").classes("zp-hamburger")
                with ui.element("div").classes("zp-brand").style(
                    "display: flex; align-items: center; gap: .5rem;"
                ):
                    icon("brand", size="md", color="var(--zp-primary)")
                    with ui.column().classes("zp-col").style("gap: 0; min-width: 0;"):
                        ui.label(title).classes("zp-header-title")
                        ui.label("Trenažér zbrojního průkazu").classes("zp-header-sub")
            with ui.row().classes("zp-row zp-gap-xs zp-nowrap"):
                ui.button(icon=I["help"], on_click=_show_help_dialog).props(
                    "flat round dense color=primary size=md"
                ).tooltip("Klávesové zkratky (?)")
                ui.button(icon=I["dark"], on_click=lambda: ui.dark_mode().toggle()).props(
                    "flat round dense color=primary size=md"
                ).tooltip("Přepnout tmavý / světlý režim")

    # Left drawer
    with ui.left_drawer(value=False, fixed=False).style(
        "background: var(--zp-surface); "
        "border-right: 1px solid var(--zp-border); padding: 1rem .75rem;"
    ) as drawer:
        ui.label("MENU").classes("zp-caption").style(
            "margin: .5rem .5rem 1rem; letter-spacing: .1em; font-weight: 600;"
        )
        for item in NAV_ITEMS:
            if item is None:
                ui.separator().classes("my-2")
                continue
            cls = "zp-nav-link active" if item.path == active_path else "zp-nav-link"
            with ui.link(target=item.path).classes(cls):
                icon(item.icon_key, size="sm", cls="zp-nav-icon")
                ui.label(item.label)
        ui.separator().classes("my-3")
        ui.label(
            "Studijní pomůcka, nenahrazuje oficiální zdroje MV ČR a platnou legislativu."
        ).classes("zp-caption").style("padding: 0 .5rem;")

    # Main content wrapper
    with ui.column().classes("zp-container"):
        yield


def _show_help_dialog():
    with ui.dialog() as d, ui.card().style("max-width: 520px; padding: 1.5rem;"):
        ui.label("Klávesové zkratky").classes("zp-h1 zp-mb-md")
        rows = [
            ("1 / A", "Odpověď A"),
            ("2 / B", "Odpověď B"),
            ("3 / C", "Odpověď C"),
            ("Enter / mezera", "Další otázka"),
            ("F", "Přepnout bookmark"),
            ("Esc", "Zavřít dialog"),
        ]
        with ui.column().classes("zp-col zp-gap-sm w-full"):
            for key, desc in rows:
                with ui.row().classes("zp-row-between w-full"):
                    ui.label(desc).classes("zp-body")
                    ui.html(f"<span class='zp-kbd' style='font-size: .85rem;'>{key}</span>")
        ui.button("Zavřít", icon=I["close"], on_click=d.close).props(
            "color=primary unelevated"
        ).classes("zp-mt-md w-full")
    d.open()
