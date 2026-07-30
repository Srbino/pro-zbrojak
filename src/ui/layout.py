"""Spolecny layout (header + drawer + spodni lista). Material Symbols namisto emoji."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from nicegui import app, ui

from src.ui.icons import I, icon
from src.ui.theme import apply_theme


@dataclass(frozen=True)
class NavItem:
    path: str
    icon_key: str
    label: str
    description: str = ""


# Navigace ve třech skupinách. Dřív to byl jeden seznam jedenácti položek,
# ve kterém vypadal Export stejně důležitě jako Marathon.
NAV_GROUPS: tuple[tuple[str, tuple[NavItem, ...]], ...] = (
    ("", (
        NavItem("/",         "dashboard", "Přehled",          "Statistiky a doporučení"),
    )),
    ("Učení", (
        NavItem("/marathon", "marathon",  "Marathon",         "Všechny otázky po pořadí"),
        NavItem("/srs",      "srs",       "Denní review",     "Spaced repetition (FSRS)"),
        NavItem("/study",    "study",     "Studium",          "Projdi otázky + správné odpovědi"),
        NavItem("/random",   "random",    "Náhodně",          "Volné procvičování"),
        NavItem("/traps",    "trap",      "Chytáky",          "Odpovědi lišící se o jedno slovo"),
    )),
    ("Ověření", (
        NavItem("/mistakes", "mistakes",  "Lekce z chyb",     "Jen otázky, kde jsi chyboval"),
        NavItem("/mastery",  "mastery",   "Mastery",          "90% na oblasti"),
        NavItem("/exam",     "exam",      "Simulace zkoušky", "30 otázek, 40 minut"),
    )),
    ("Ostatní", (
        NavItem("/flagged",  "flagged",   "Označené",         "Otázky k zamyšlení"),
        NavItem("/export",   "export",    "Export pro AI",    "Markdown pro Claude Code"),
        NavItem("/settings", "settings",  "Nastavení",        ""),
    )),
)

# Plochý seznam kvůli zpětné kompatibilitě (dashboard tiles, testy).
NAV_ITEMS: tuple[NavItem, ...] = tuple(
    item for _, items in NAV_GROUPS for item in items
)

# Čtyři cíle pro palec. Poslední otevírá plné menu — na mobilu proto mizí
# hamburger, dva vstupy do stejné navigace by si jen konkurovaly.
TABBAR: tuple[tuple[str, str, str], ...] = (
    ("/marathon", "marathon", "Učit"),
    ("/srs",      "srs",      "Review"),
    ("/exam",     "exam",     "Zkouška"),
)


def nav_items_for_dashboard() -> tuple[NavItem, ...]:
    """Vraci neprazdne nav polozky krome dashboardu (pro dashboard tiles)."""
    return tuple(it for it in NAV_ITEMS if it.path != "/")


def _daily_status(user_email: str) -> tuple[int, int]:
    """(kolik otázek čeká na review, kolik dní v řadě). Nikdy nespadne — je to
    ozdoba hlavičky, ne důvod, proč by neměla jít otevřít stránka."""
    try:
        from src.db.store import get_db
        from src.learning import heatmap as hm
        from src.learning import srs as srs_mod
        db = get_db()
        return len(srs_mod.due_today(db, user_email, limit=999)), hm.current_streak(db, user_email)
    except Exception:
        return 0, 0


@contextmanager
def page_shell(title: str = "Pro Zbroják", active_path: str | None = None):
    """Stranka: header + drawer + spodni lista + container pro obsah.

    Usage:
        with page_shell("Marathon", active_path="/marathon"):
            ui.label(...)
    """
    apply_theme()

    from src.auth import current_user, do_logout
    user = current_user()
    n_due, streak = _daily_status(user.email) if user is not None else (0, 0)

    with ui.header(elevated=False):
        with ui.row().classes("zp-row-between zp-nowrap w-full").style(
            "padding: .35rem .75rem; min-height: 56px;"
        ):
            with ui.row().classes("zp-row zp-gap-sm zp-nowrap"):
                ui.button(icon=I["menu"], on_click=lambda: drawer.toggle()).props(
                    "flat dense round color=primary size=md"
                ).tooltip("Menu").classes("zp-hamburger")
                with ui.element("div").classes("zp-brand").style(
                    "display: flex; align-items: center; gap: .5rem; min-width: 0;"
                ):
                    icon("brand", size="md", color="var(--zp-primary)")
                    with ui.column().classes("zp-col").style("gap: 0; min-width: 0;"):
                        ui.label(title).classes("zp-header-title")
                        ui.label("Pro Zbroják — trenažér ZOZ").classes("zp-header-sub")

            with ui.row().classes("zp-row zp-gap-xs zp-nowrap").style("align-items: center;"):
                if user is not None:
                    # Kvůli čemu se sem člověk vrací. Dřív se to muselo hledat
                    # na Přehledu.
                    _status_chip(n_due, streak)
                    ui.label(user.name).classes("zp-user-name zp-body-sm").style(
                        "font-weight: 600;"
                    )
                    ui.button(
                        icon=I["person"], on_click=lambda: ui.navigate.to("/settings"),
                    ).props("flat round dense size=md").classes("zp-icon-btn").tooltip(
                        user.email + (" · admin" if user.is_admin else "")
                    )
                    ui.button(icon=I["logout"], on_click=do_logout).props(
                        "flat round dense size=md"
                    ).classes("zp-icon-btn").tooltip("Odhlásit se")
                # Stabilní třída, ne pořadí v hlavičce — počet tlačítek se mění
                # podle toho, jestli je někdo přihlášený.
                ui.button(icon=I["help"], on_click=_show_help_dialog).props(
                    "flat round dense size=md"
                ).classes("zp-icon-btn zp-help-btn").tooltip("Klávesové zkratky (?)")
                _theme_toggle()

    with ui.left_drawer(value=False, fixed=False).style("padding: .5rem .75rem;") as drawer:
        for group_label, items in NAV_GROUPS:
            if group_label:
                ui.label(group_label).classes("zp-nav-group")
            for item in items:
                cls = "zp-nav-link active" if item.path == active_path else "zp-nav-link"
                with ui.link(target=item.path).classes(cls):
                    icon(item.icon_key, size="sm", cls="zp-nav-icon")
                    ui.label(item.label)
                    if item.path == "/srs" and n_due:
                        ui.html(f'<span class="zp-nav-count">{n_due}</span>')
        ui.separator().classes("my-3")
        ui.label(
            "Studijní pomůcka, nenahrazuje oficiální zdroje MV ČR a platnou legislativu."
        ).classes("zp-caption").style("padding: 0 .5rem;")

    with ui.column().classes("zp-container"):
        yield

    # Spodní lišta se vykresluje až po obsahu, ať je v DOM pod ním.
    with ui.footer(fixed=True).classes("zp-only-mobile").props("bordered=false"):
        with ui.element("nav").classes("zp-tabbar w-full"):
            for path, icon_key, label in TABBAR:
                cls = "zp-tabbar-item active" if path == active_path else "zp-tabbar-item"
                with ui.link(target=path).classes(cls):
                    icon(icon_key, size="sm")
                    ui.label(label)
                    if path == "/srs" and n_due:
                        ui.html(f'<span class="zp-tabbar-dot">{n_due}</span>')
            menu_item = ui.element("div").classes("zp-tabbar-item")
            menu_item.on("click", lambda: drawer.toggle())
            with menu_item:
                icon("menu", size="sm")
                ui.label("Menu")


def _theme_toggle() -> None:
    """Přepínač světlý / tmavý režim.

    Instance `ui.dark_mode` musí být JEDNA na stránku a musí se držet ve
    volbě uživatele. Dřív se vyráběla až uvnitř obsluhy kliknutí, takže
    každý klik vytvořil nový prvek s prázdnou hodnotou — první klik zapnul
    tmu, druhý už neudělal nic a přechod na jinou stránku volbu zahodil.
    """
    dark = ui.dark_mode()
    try:
        stored = app.storage.user.get("dark_mode")
    except Exception:      # bez storage_secret (např. v testech) jedeme podle systému
        stored = None
    dark.value = stored  # None = řídí se nastavením systému

    def _apply(value: bool) -> None:
        dark.value = value
        try:
            app.storage.user["dark_mode"] = value
        except Exception:
            pass
        btn.props(f'icon={I["light"] if value else I["dark"]}')

    def _toggle() -> None:
        # Z „podle systému" se přepíná na opak toho, co je zrovna vidět.
        _apply(not bool(dark.value))

    btn = ui.button(
        icon=I["light"] if stored else I["dark"], on_click=_toggle
    ).props("flat round dense size=md").classes("zp-icon-btn")
    btn.tooltip("Přepnout tmavý / světlý režim")


def _status_chip(n_due: int, streak: int) -> None:
    """Kolik zbývá dnes + jak dlouhá je série."""
    bits = []
    if n_due:
        bits.append(f"{n_due} k review")
    if streak:
        bits.append(f"{streak} {'den' if streak == 1 else 'dny' if streak < 5 else 'dní'} v řadě")
    if not bits:
        return
    cls = "zp-streak due" if n_due else "zp-streak"
    ui.html(f'<span class="{cls}">{" · ".join(bits)}</span>')


def _show_help_dialog():
    with ui.dialog() as d, ui.card().style("max-width: 520px; padding: 1.5rem;"):
        ui.label("Klávesové zkratky").classes("zp-h1 zp-mb-md")
        rows = [
            ("1 / A", "Vybrat odpověď A"),
            ("2 / B", "Vybrat odpověď B"),
            ("3 / C", "Vybrat odpověď C"),
            ("Enter / mezera", "Vyhodnotit výběr, pak další otázka"),
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
