"""Kombinovane 'praktikum' routy: random, mistakes, flagged.

Vsechny sdili QuizSession — DRY.
"""
from __future__ import annotations

from nicegui import ui

from src.auth import require_login
from src.db import traps as traps_db
from src.db.questions import load_questions
from src.db.store import all_flagged, get_db, mistake_stats
from src.db.traps import trap_numbers
from src.ui.components import SECTION_LABEL, QuizSession, query_str
from src.ui.layout import page_shell


def _record(mode: str, user_email: str):
    db = get_db()
    def _rec(qid: str, chosen: str, correct: str, ms: int):
        from src.db.store import record_attempt
        record_attempt(db, user_email=user_email, question_id=qid, chosen=chosen,
                       correct=correct, mode=mode, time_ms=ms)
    return _rec


@ui.page("/random")
def random_page():
    user = require_login()
    if user is None:
        return
    with page_shell("Náhodné procvičování", active_path="/random"):
        QuizSession(
            pool=load_questions(),
            mode="random",
            user_email=user.email,
            on_record=_record("random", user.email),
        ).run()


@ui.page("/traps")
def traps_page():
    """Chytáky — jen otázky, kde se distraktor liší od správné odpovědi o kousek.

    Přesně na tyhle se u zkoušky padá: člověk látku zná, ale přehlédne jedno
    slovo. Po odpovědi jde rozbalit, co bylo nastražené.
    """
    user = require_login()
    if user is None:
        return
    kind = query_str("druh", "")
    if kind not in traps_db.KINDS:
        kind = ""
    numbers = trap_numbers(kind or None)
    pool = [q for q in load_questions() if q["pdf_number"] in numbers]

    with page_shell("Chytáky", active_path="/traps"):
        with ui.element("div").classes("zp-quiz-head zp-mb-md"):
            ui.label(
                "Otázky, na kterých se dá snadno šlápnout vedle. Po vyhodnocení se "
                "v zadání vyznačí slovo, které obrací smysl, a pod otázkou si rozbalíš "
                "rozbor — co přesně bylo nastražené."
            ).classes("zp-body")
            with ui.row().classes("w-full zp-gap-sm").style("flex-wrap: wrap;"):
                _kind_chip("", "Vše", kind)
                for key, (label, _field) in traps_db.KINDS.items():
                    _kind_chip(key, label, kind)

        QuizSession(
            pool=pool,
            mode="traps",
            user_email=user.email,
            empty_icon="info",
            empty_heading="Žádné chytáky",
            empty_subtitle="Spusť `make traps` — seznam se generuje z katalogu.",
            on_record=_record("traps", user.email),
        ).run()


def _kind_chip(key: str, label: str, active: str) -> None:
    """Přepínač druhu pasti. Počet je součástí popisku — bez něj se nedá odhadnout,
    do čeho člověk jde."""
    n = traps_db.count(key or None)
    props = "unelevated color=primary" if key == active else "outline color=primary"
    ui.button(
        f"{label} ({n})",
        on_click=lambda k=key: ui.navigate.to(f"/traps?druh={k}" if k else "/traps"),
    ).props(f"{props} no-caps dense size=md")


# Pořadí, ve kterém má smysl chyby procházet. Dřív se fronta zamíchala,
# takže se skákalo mezi oblastmi a nedalo se poznat, co člověk plete nejvíc.
RAZENI = {
    "nejvic": ("Nejvíc chyb", lambda q, s: (-s["chyb"], -s["podil"], q["pdf_number"])),
    "podil":  ("Nejhorší poměr", lambda q, s: (-s["podil"], -s["chyb"], q["pdf_number"])),
    "cerstve": ("Nejčerstvější chyba", lambda q, s: (-s["posledni_chyba"], q["pdf_number"])),
    "cislo":  ("Po pořadí", lambda q, s: (q["pdf_number"],)),
}


@ui.page("/mistakes")
def mistakes_page():
    user = require_login()
    if user is None:
        return
    db = get_db()
    staty = mistake_stats(db, user.email)
    vsechny = [q for q in load_questions() if q["id"] in staty]

    sekce = query_str("oblast", "")
    razeni = query_str("razeni", "nejvic")
    if razeni not in RAZENI:
        razeni = "nejvic"

    pool = [q for q in vsechny if not sekce or q.get("section") == sekce]
    pool.sort(key=lambda q: RAZENI[razeni][1](q, staty[q["id"]]))

    with page_shell("Lekce z chyb", active_path="/mistakes"):
        with ui.element("div").classes("zp-quiz-head zp-mb-md"):
            ui.label(
                f"Otázky, kde jsi chyboval — celkem {len(vsechny)}. "
                "Pořadí i oblast si vyber, ať se neskáče mezi tématy."
            ).classes("zp-body")

            with ui.row().classes("w-full zp-gap-sm").style("flex-wrap: wrap;"):
                _chip("Vše", not sekce, f"/mistakes?razeni={razeni}",
                      len(vsechny))
                for klic, nazev in SECTION_LABEL.items():
                    n = sum(1 for q in vsechny if q.get("section") == klic)
                    if n:
                        _chip(nazev, sekce == klic,
                              f"/mistakes?oblast={klic}&razeni={razeni}", n)

            with ui.row().classes("w-full zp-gap-sm").style("flex-wrap: wrap;"):
                ui.label("Řadit:").classes("zp-caption").style("align-self: center;")
                for klic, (nazev, _) in RAZENI.items():
                    _chip(nazev, razeni == klic,
                          f"/mistakes?oblast={sekce}&razeni={klic}")

        # Kolikrát na které otázce člověk chyboval — přímo u položky v seznamu.
        poznamky = {
            q["id"]: f"{staty[q['id']]['chyb']}×" for q in pool
            if staty[q["id"]]["chyb"] > 1
        }

        QuizSession(
            pool=pool,
            mode="mistakes",
            user_email=user.email,
            empty_icon="success",
            empty_heading="Žádné chyby",
            empty_subtitle=(
                "V téhle oblasti nemáš chybu." if sekce
                else "Začni nějaký režim a když někde chybuješ, objeví se tady."
            ),
            on_record=_record("mistakes", user.email),
            show_navigator=True,
            shuffle=False,          # pořadí si určuje uživatel výše
            notes=poznamky,
        ).run()


def _chip(nazev: str, aktivni: bool, cil: str, pocet: int | None = None) -> None:
    popis = f"{nazev} ({pocet})" if pocet is not None else nazev
    props = "unelevated color=primary" if aktivni else "outline color=primary"
    ui.button(popis, on_click=lambda c=cil: ui.navigate.to(c)).props(
        f"{props} no-caps dense size=md"
    )


@ui.page("/flagged")
def flagged_page():
    user = require_login()
    if user is None:
        return
    db = get_db()
    flagged = set(all_flagged(db, user.email))
    pool = [q for q in load_questions() if q["id"] in flagged]
    with page_shell("Označené otázky", active_path="/flagged"):
        QuizSession(
            pool=pool,
            mode="flagged",
            user_email=user.email,
            empty_icon="flagged",
            empty_heading="Žádné označené otázky",
            empty_subtitle='Stiskni "F" nebo klikni na bookmark v quizu.',
            on_record=_record("flagged", user.email),
        ).run()
