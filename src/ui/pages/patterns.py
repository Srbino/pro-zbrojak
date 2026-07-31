"""Vzorce — strukturní pravidla testu a trénink na jejich výjimky.

Myšlenka režimu: naučit se pár pravidel plynoucích z toho, jak je test psaný,
a k nim jmenovitě otázky, kde pravidlo NEPLATÍ. Čtyři pravidla se dotýkají
332 otázek a výjimek je dohromady padesát — to je výrazně méně učení než
těch 332 otázek zvlášť.

Součástí je i seznam pravidel, která NEFUNGUJÍ. Bez něj by si každý stejně
zkusil „nejdelší odpověď bývá správná" a přišel by na to sám, jen dráž.
"""
from __future__ import annotations

from nicegui import ui

from src.auth import require_login
from src.db import patterns as pat
from src.db.questions import load_questions
from src.db.store import get_db, record_attempt
from src.ui.components import QuizSession, empty_state, query_str
from src.ui.icons import I, icon
from src.ui.layout import page_shell


@ui.page("/patterns")
def patterns_page():
    user = require_login()
    if user is None:
        return

    pravidla = pat.rules()
    with page_shell("Vzorce", active_path="/patterns"):
        ui.label("Vzorce v testu").classes("zp-display")
        ui.label(
            "Pravidla, která plynou z toho, jak je test napsaný — ne z práva. "
            "Použij je, když si nejsi jistý; nenahradí znalost, ale zúží výběr. "
            "U každého je změřeno, jak často platí, a jmenovitě otázky, kde ne."
        ).classes("zp-body zp-prose zp-mb-lg")

        if not pravidla:
            empty_state(
                icon_name="pattern",
                heading="Vzorce nejsou vygenerované",
                subtitle="Spusť `make patterns` — počítají se z katalogu otázek.",
            )
            return

        for p in pravidla:
            _rule_card(p)

        _not_working()


def _rule_card(p: dict) -> None:
    spolehlivost = p.get("spolehlivost", 0) * 100
    zaklad = p.get("zaklad", 0) * 100
    vyjimky = p.get("vyjimky", [])
    typ_popis = (
        "zúží ze tří možností na dvě" if p.get("typ") == "zuz"
        else "škrtne jednu možnost"
    )

    with ui.element("div").classes("zp-card zp-mb-md"):
        with ui.row().classes("zp-row zp-gap-sm zp-nowrap w-full zp-mb-sm"):
            icon("pattern", size="sm", color="var(--zp-primary)")
            ui.label(p.get("nazev", "—")).classes("zp-h3 zp-flex-1")
            ui.html(f'<span class="zp-badge">{typ_popis}</span>')

        ui.label(p.get("pravidlo", "")).classes("zp-body zp-mb-sm")

        # Spolehlivost proti tomu, co by dala náhoda bez pravidla.
        ui.html(
            '<div class="zp-meter">'
            f'<div class="zp-meter-fill{" ok" if spolehlivost >= 85 else ""}" '
            f'style="width:{min(100.0, spolehlivost):.1f}%;"></div>'
            f'<div class="zp-meter-mark" style="left:{min(100.0, zaklad):.1f}%;" '
            f'data-label="naslepo {zaklad:.0f} %"></div>'
            "</div>"
        )
        ui.label(
            f"Platí v {spolehlivost:.0f} % — uplatní se u {p.get('pouzito', 0)} otázek "
            f"z 837, výjimek je {len(vyjimky)}."
        ).classes("zp-body-sm zp-mt-sm")

        if p.get("proc"):
            with ui.element("div").classes("zp-law-ref zp-mt-md"):
                ui.label("Proč to funguje").classes("zp-trap-title")
                ui.label(p["proc"]).classes("zp-body-sm")

        if p.get("pozor"):
            with ui.element("div").classes("zp-trap-box"):
                ui.label("Kde si dát pozor").classes("zp-trap-title")
                ui.label(p["pozor"]).classes("zp-body-sm")

        if vyjimky:
            with ui.row().classes("w-full zp-gap-sm zp-mt-md").style("flex-wrap: wrap;"):
                ui.button(
                    f"Procvičit {len(vyjimky)} výjimek", icon=I["next"],
                    on_click=lambda pid=p["id"]: ui.navigate.to(f"/patterns/run?pravidlo={pid}"),
                ).props("color=primary unelevated")
                ui.label(
                    "č. " + ", ".join(str(n) for n in vyjimky[:14])
                    + (" …" if len(vyjimky) > 14 else "")
                ).classes("zp-caption zp-mono zp-flex-1")


def _not_working() -> None:
    nefunguje = pat.not_working()
    if not nefunguje:
        return
    ui.label("Co naopak nefunguje").classes("zp-h2 zp-mt-xl zp-mb-sm")
    ui.label(
        "Změřeno na stejných datech. Náhodné tipnutí trefí 33 %, takže tohle "
        "jsou pověry — vyplatí se je znát, ať se jimi nezdržuješ."
    ).classes("zp-body-sm zp-prose zp-mb-sm")
    with ui.element("div").classes("zp-card"):
        for item in nefunguje:
            with ui.row().classes("zp-row-between w-full zp-gap-sm").style(
                "padding: .4rem 0; flex-wrap: wrap;"
            ):
                with ui.column().classes("zp-col zp-flex-1").style("gap: .1rem; min-width: 200px;"):
                    ui.label(item["nazev"]).classes("zp-body-sm").style("font-weight: 600;")
                    ui.label(item["pozn"]).classes("zp-caption")
                pct = item["uspesnost"] * 100
                cls = "danger" if pct < 33.3 else "neutral"
                ui.html(f'<span class="zp-badge {cls}">{pct:.0f} %</span>')


@ui.page("/patterns/run")
def patterns_run_page():
    """Trénink na výjimky — otázky, kde vybrané pravidlo neplatí."""
    user = require_login()
    if user is None:
        return
    rule_id = query_str("pravidlo", "")
    p = pat.rule(rule_id)
    cisla = pat.exception_numbers(rule_id) if p else pat.exception_numbers()
    pool = [q for q in load_questions() if q["pdf_number"] in cisla]
    nazev = p["nazev"] if p else "Všechny výjimky"

    db = get_db()

    def _rec(qid, chosen, correct, ms):
        record_attempt(db, user_email=user.email, question_id=qid, chosen=chosen,
                       correct=correct, mode="patterns", time_ms=ms)

    with page_shell(f"Výjimky — {nazev}", active_path="/patterns"):
        ui.label(f"Výjimky: {nazev}").classes("zp-display")
        if p:
            ui.label(
                f"Tady pravidlo „{p['pravidlo'].rstrip('.')}“ NEPLATÍ. "
                "Právě tyhle otázky se vyplatí znát jmenovitě — bez nich je "
                "pravidlo past."
            ).classes("zp-body zp-prose zp-mb-md")

        QuizSession(
            pool=pool, mode="patterns", user_email=user.email,
            empty_icon="pattern",
            empty_heading="Žádné výjimky",
            empty_subtitle="Tohle pravidlo platí bez výjimky.",
            on_record=_rec,
            show_navigator=True,
        ).run()
