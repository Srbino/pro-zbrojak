"""Nastaveni — info, reset historie, disclaimer."""
from __future__ import annotations

from nicegui import ui

from src.auth import do_logout, require_login
from src.db.questions import load_questions
from src.db.store import get_db, reset_all
from src.paths import DB_PATH, EXPORT_DIR
from src.ui.components import confirm_button
from src.ui.icons import I
from src.ui.layout import page_shell


@ui.page("/settings")
def settings_page():
    from src.ui.pages.dashboard import VERSION
    user = require_login()
    if user is None:
        return
    db = get_db()
    with page_shell("Nastavení", active_path="/settings"):
        ui.label("Nastavení").classes("zp-display")

        with ui.element("div").classes("zp-card zp-mb-md"):
            ui.label("Přihlášený uživatel").classes("zp-h3")
            _kv("Jméno", user.name + ("  (admin)" if user.is_admin else ""))
            _kv("E-mail", user.email)

            with ui.row().classes("zp-row zp-gap-sm zp-mt-md").style("flex-wrap: wrap;"):
                ui.button("Odhlásit se", icon=I["logout"], on_click=do_logout).props(
                    "unelevated color=primary"
                )
                if user.is_admin:
                    ui.button("Admin přehled", icon=I["insights"],
                              on_click=lambda: ui.navigate.to("/admin")).props(
                        "outline color=primary"
                    )

        with ui.element("div").classes("zp-card zp-mb-md"):
            ui.label("Aplikace").classes("zp-h3")
            _kv("Verze", VERSION)
            _kv("DB", str(DB_PATH))
            _kv("Otázek v katalogu", str(len(load_questions())))
            _kv("Export adresář", str(EXPORT_DIR))

        with ui.element("div").classes("zp-card zp-accent-danger zp-mb-md"):
            ui.label("Reset historie").classes("zp-h3").style("color: var(--zp-danger);")
            ui.label(
                "Nevratně smaže TVÉ pokusy, marathony, simulace a bookmarky "
                "(ostatních uživatelů se netýká)."
            ).classes("zp-body-sm")

            def _do_reset():
                reset_all(db, user.email)
                ui.notify("Historie smazána", color="positive", position="top")

            confirm_button(
                "Reset historie",
                on_confirm=_do_reset,
                confirm_label="OPRAVDU SMAZAT VŠE",
            )

        with ui.element("div").classes("zp-card"):
            ui.label("O aplikaci").classes("zp-h3")
            ui.label("Pro Zbroják").classes("zp-body").style("font-weight: 600;")
            ui.label(
                "Český trenažér testových otázek pro zkoušku odborné způsobilosti (ZOZ) "
                "k vydání zbrojního průkazu."
            ).classes("zp-body-sm")
            ui.separator().classes("my-2")
            ui.label(
                "Studijní pomůcka založená na oficiálním PDF MV ČR „Soubor testových otázek "
                "pro teoretickou část ZOZ a komisionální zkoušku' (verze 15. 12. 2025). "
                "Není oficiálním zdrojem. Pro přípravu vždy konzultuj zákon č. 90/2024 Sb. "
                "a nařízení vlády č. 238/2025 Sb. v aktuálním znění (oba účinné od 1. 1. 2026)."
            ).classes("zp-body-sm")


def _kv(label: str, value: str):
    with ui.row().classes("zp-row w-full zp-kv-row").style(
        "align-items: baseline; padding: .3rem 0; gap: .75rem;"
    ):
        ui.label(label).classes("zp-caption").style("width: 160px; flex-shrink: 0;")
        ui.label(value).classes("zp-body-sm zp-mono").style(
            "flex: 1; min-width: 0; word-break: break-all;"
        )
