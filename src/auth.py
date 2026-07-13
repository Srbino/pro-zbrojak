"""Identita uživatele + přihlášení.

Dvě cesty:
  1) **Cloudflare Access** (vzdálený přístup) — Cloudflare vloží ověřenou hlavičku
     `Cf-Access-Authenticated-User-Email`. Té věříme (jediná veřejná cesta vede přes
     Access), takže přihlášení je automatické, bez druhého loginu.
  2) **Fallback login** (LAN, kde hlavička není) — jednoduchá volba jména,
     volitelně chráněná sdíleným kódem `PRO_ZBROJAK_LOGIN_CODE`.

Admini se určují přes `PRO_ZBROJAK_ADMINS` (čárkami oddělené e-maily).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from nicegui import app, context, ui

ACCESS_EMAIL_HEADER = "cf-access-authenticated-user-email"

ADMIN_EMAILS = {
    e.strip().lower()
    for e in os.environ.get("PRO_ZBROJAK_ADMINS", "srba@unify.cz").split(",")
    if e.strip()
}

# Přátelská jména pro známé e-maily (jinak se použije část před @).
DISPLAY_NAMES = {
    "srba@unify.cz": "Pavel",
    "bena.matej@email.cz": "Matěj",
    "ondrej.harant17@gmail.com": "Ondra",
}

# Volitelný sdílený kód pro LAN login. Prázdný = LAN login bez kódu (důvěryhodná síť).
LOGIN_CODE = os.environ.get("PRO_ZBROJAK_LOGIN_CODE", "").strip()


@dataclass(frozen=True)
class User:
    email: str
    name: str
    is_admin: bool


def display_name(email: str) -> str:
    return DISPLAY_NAMES.get(email.lower(), email.split("@")[0] or email)


def is_admin(email: str) -> bool:
    return email.lower() in ADMIN_EMAILS


def _header_email() -> str | None:
    try:
        req = context.client.request
        if req is None:
            return None
        val = req.headers.get(ACCESS_EMAIL_HEADER)
    except Exception:
        return None
    return val.strip().lower() if val else None


def _session_email() -> str | None:
    try:
        val = app.storage.user.get("email")
    except Exception:
        return None
    return (val or "").strip().lower() or None


def current_user() -> User | None:
    """Aktuální uživatel: Cloudflare Access hlavička má přednost, jinak session (LAN)."""
    header_email = _header_email()
    email = header_email or _session_email()
    if not email:
        return None
    # Cache do session + zajisti řádek v DB (auto-provisioning — Access už ověřil).
    try:
        app.storage.user["email"] = email
        app.storage.user["via_access"] = bool(header_email)
    except Exception:
        pass
    from src.db.store import ensure_user, get_db
    ensure_user(get_db(), email, display_name(email), is_admin(email))
    return User(email=email, name=display_name(email), is_admin=is_admin(email))


def login_local(email: str) -> None:
    app.storage.user["email"] = email.strip().lower()
    app.storage.user["via_access"] = False


def logout() -> None:
    try:
        app.storage.user.pop("email", None)
        app.storage.user.pop("via_access", None)
    except Exception:
        pass


def do_logout() -> None:
    """Chytré odhlášení: za Cloudflare Access odhlásí i z Accessu, jinak zpět na login."""
    via_access = False
    try:
        via_access = bool(app.storage.user.get("via_access"))
    except Exception:
        pass
    logout()
    if via_access:
        # Cloudflare zruší CF_Authorization cookie a ukáže odhlašovací stránku.
        ui.navigate.to("/cdn-cgi/access/logout")
    else:
        ui.navigate.to("/")


def require_login() -> User | None:
    """Vrátí přihlášeného uživatele, nebo vykreslí login a vrátí None.

    Vzor v každé @ui.page:
        user = require_login()
        if user is None:
            return
    """
    user = current_user()
    if user is not None:
        return user
    _render_login()
    return None


def _render_login(next_path: str = "/") -> None:
    from src.ui.icons import icon
    from src.ui.theme import apply_theme

    apply_theme()
    with ui.column().classes("w-full").style(
        "min-height: 90vh; align-items: center; justify-content: center; gap: 1rem;"
    ):
        with ui.element("div").classes("zp-card").style("max-width: 420px; width: 100%; padding: 2rem;"):
            with ui.row().classes("zp-row zp-gap-sm").style("align-items: center; margin-bottom: .5rem;"):
                icon("brand", size="md", color="var(--zp-primary)")
                ui.label("Pro Zbroják").classes("zp-h1")
            ui.label("Přihlas se, ať máš vlastní progres.").classes("zp-body-sm zp-mb-md")

            email_in = ui.input("E-mail").props("outlined dense").classes("w-full")

            # Rychlá volba známých lidí.
            if DISPLAY_NAMES:
                ui.label("Rychlá volba").classes("zp-caption zp-mt-sm")
                with ui.row().classes("zp-row zp-gap-sm").style("flex-wrap: wrap;"):
                    for em, nm in DISPLAY_NAMES.items():
                        ui.button(nm, on_click=lambda e=em: email_in.set_value(e)).props(
                            "flat dense color=primary"
                        )

            code_in = None
            if LOGIN_CODE:
                code_in = ui.input("Přístupový kód", password=True).props(
                    "outlined dense"
                ).classes("w-full zp-mt-sm")

            def _do_login():
                email = (email_in.value or "").strip().lower()
                if "@" not in email:
                    ui.notify("Zadej platný e-mail", color="warning", position="top")
                    return
                if LOGIN_CODE and (code_in.value or "").strip() != LOGIN_CODE:
                    ui.notify("Špatný přístupový kód", color="negative", position="top")
                    return
                login_local(email)
                ui.navigate.to(next_path)

            email_in.on("keydown.enter", lambda: _do_login())
            if code_in is not None:
                code_in.on("keydown.enter", lambda: _do_login())

            ui.button("Vstoupit", on_click=_do_login).props(
                "unelevated color=primary size=md"
            ).classes("w-full zp-mt-md")
