"""Admin přehled — statistiky všech uživatelů. Jen pro adminy."""
from __future__ import annotations

import time

from nicegui import ui

from src.auth import require_login
from src.db.store import get_db, list_exams, list_users, stats_overall
from src.learning import srs as srs_mod
from src.ui.components import back_home_button, stat_card
from src.ui.layout import page_shell


@ui.page("/admin")
def admin_page():
    user = require_login()
    if user is None:
        return
    if not user.is_admin:
        with page_shell("Přístup odepřen", active_path="/settings"):
            ui.label("Přístup odepřen").classes("zp-display")
            ui.label("Tahle stránka je jen pro administrátory.").classes("zp-body zp-mb-lg")
            back_home_button()
        return

    db = get_db()
    users = list_users(db)

    with page_shell("Admin — uživatelé", active_path="/settings"):
        ui.label("Admin — uživatelé").classes("zp-display")
        ui.label(
            f"Přehled všech {len(users)} uživatelů a jejich aktivity. "
            "Každý má vlastní izolovaný progres."
        ).classes("zp-body zp-prose zp-mb-lg")

        # Souhrn
        total_attempts = sum(stats_overall(db, u["email"])["attempts"] for u in users)
        with ui.element("div").classes("zp-grid-3 zp-mb-lg"):
            stat_card("Uživatelů", str(len(users)), sub="registrovaných")
            stat_card("Pokusů celkem", str(total_attempts), sub="napříč všemi")
            stat_card("Adminů", str(sum(1 for u in users if u["is_admin"])), sub="s právy")

        with ui.element("div").classes("zp-card").style("padding: 0;"):
            # Hlavička
            with ui.row().classes("zp-row zp-nowrap w-full").style(
                "padding: .6rem 1rem; border-bottom: 1px solid var(--zp-border); font-weight: 600;"
            ):
                ui.label("Uživatel").classes("zp-body-sm").style("flex: 2;")
                ui.label("Pokusů").classes("zp-body-sm").style("width: 80px; text-align: right;")
                ui.label("Úspěšnost").classes("zp-body-sm").style("width: 90px; text-align: right;")
                ui.label("Zkoušky ✓").classes("zp-body-sm").style("width: 90px; text-align: right;")
                ui.label("SRS").classes("zp-body-sm").style("width: 60px; text-align: right;")
                ui.label("Naposledy").classes("zp-body-sm").style("width: 130px; text-align: right;")

            for u in users:
                ov = stats_overall(db, u["email"])
                exams = list_exams(db, u["email"])
                passed = sum(1 for e in exams if e["passed"])
                srs_n = srs_mod.total_cards(db, u["email"])
                last = time.strftime("%Y-%m-%d %H:%M", time.localtime(u["last_seen"])) if u.get("last_seen") else "—"
                with ui.row().classes("zp-row zp-nowrap w-full").style(
                    "padding: .6rem 1rem; border-top: 1px solid var(--zp-border);"
                ):
                    with ui.column().classes("zp-col").style("flex: 2; gap: 0; min-width: 0;"):
                        badge = '  <span class="zp-badge success" style="min-width:auto;">admin</span>' if u["is_admin"] else ""
                        ui.html(f'<span style="font-weight:600;">{u["name"]}</span>{badge}')
                        ui.label(u["email"]).classes("zp-caption zp-mono").style("word-break: break-all;")
                    ui.label(str(ov["attempts"])).classes("zp-body-sm zp-mono").style("width: 80px; text-align: right;")
                    ui.label(f'{ov["pct"]} %').classes("zp-body-sm zp-mono").style("width: 90px; text-align: right;")
                    ui.label(f'{passed}/{len(exams)}').classes("zp-body-sm zp-mono").style("width: 90px; text-align: right;")
                    ui.label(str(srs_n)).classes("zp-body-sm zp-mono").style("width: 60px; text-align: right;")
                    ui.label(last).classes("zp-caption zp-mono").style("width: 130px; text-align: right;")

        ui.element("div").style("height: 1.5rem;")
        back_home_button()
