"""Nastaveni — info, reset historie, disclaimer."""
from __future__ import annotations

from pathlib import Path

from nicegui import ui

from src.db.questions import load_questions
from src.db.store import get_db, reset_all
from src.ui.components import confirm_button
from src.ui.layout import page_shell


ROOT = Path(__file__).resolve().parent.parent.parent.parent


@ui.page("/settings")
def settings_page():
    from src.ui.pages.dashboard import VERSION
    db = get_db()
    with page_shell("Nastavení", active_path="/settings"):
        ui.label("Nastavení").classes("zp-display")

        with ui.element("div").classes("zp-card zp-mb-md"):
            ui.label("Aplikace").classes("zp-h3")
            _kv("Verze", VERSION)
            _kv("DB", str(ROOT / "data" / "stats.db"))
            _kv("Otázek v katalogu", str(len(load_questions())))
            _kv("Export adresář", str(ROOT / "exports"))

        with ui.element("div").classes("zp-card zp-accent-danger zp-mb-md"):
            ui.label("Reset historie").classes("zp-h3").style("color: var(--zp-danger);")
            ui.label(
                "Nevratně smaže všechny pokusy, marathony, simulace a bookmarky."
            ).classes("zp-body-sm")
            confirm_button(
                "Reset historie",
                on_confirm=lambda: (reset_all(db), ui.notify("Historie smazána", color="positive", position="top")),
                confirm_label="OPRAVDU SMAZAT VŠE",
            )

        with ui.element("div").classes("zp-card"):
            ui.label("Disclaimer").classes("zp-h3")
            ui.label(
                "Tato aplikace je studijní pomůcka založená na otázkách MV ČR "
                "(zdroj PDF z 15. 12. 2025). Není oficiálním zdrojem. Pro přípravu vždy konzultuj "
                "zákon č. 90/2024 Sb. a NV č. 238/2025 Sb. v aktuálním znění."
            ).classes("zp-body-sm")


def _kv(label: str, value: str):
    with ui.row().classes("zp-row w-full zp-kv-row").style(
        "align-items: baseline; padding: .3rem 0; gap: .75rem;"
    ):
        ui.label(label).classes("zp-caption").style("width: 160px; flex-shrink: 0;")
        ui.label(value).classes("zp-body-sm zp-mono").style(
            "flex: 1; min-width: 0; word-break: break-all;"
        )
