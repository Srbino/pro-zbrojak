"""Kombinovane 'praktikum' routy: random, mistakes, flagged.

Vsechny sdili QuizSession — DRY.
"""
from __future__ import annotations

from nicegui import ui

from src.db.questions import load_questions
from src.db.store import get_db, record_attempt, question_ids_with_mistakes, all_flagged
from src.ui.components import QuizSession
from src.ui.layout import page_shell


def _record(mode: str):
    db = get_db()
    def _rec(qid: str, chosen: str, correct: str, ms: int):
        record_attempt(db, question_id=qid, chosen=chosen, correct=correct,
                       mode=mode, time_ms=ms)
    return _rec


@ui.page("/random")
def random_page():
    with page_shell("Náhodné procvičování", active_path="/random"):
        QuizSession(
            pool=load_questions(),
            mode="random",
            on_record=_record("random"),
        ).run()


@ui.page("/mistakes")
def mistakes_page():
    db = get_db()
    bad_ids = set(question_ids_with_mistakes(db))
    pool = [q for q in load_questions() if q["id"] in bad_ids]
    with page_shell("Lekce z chyb", active_path="/mistakes"):
        QuizSession(
            pool=pool,
            mode="mistakes",
            empty_icon="success",
            empty_heading="Žádné chyby",
            empty_subtitle="Začni nějaký režim a když někde chybuješ, objeví se tady.",
            on_record=_record("mistakes"),
        ).run()


@ui.page("/flagged")
def flagged_page():
    db = get_db()
    flagged = set(all_flagged(db))
    pool = [q for q in load_questions() if q["id"] in flagged]
    with page_shell("Označené otázky", active_path="/flagged"):
        QuizSession(
            pool=pool,
            mode="flagged",
            empty_icon="flagged",
            empty_heading="Žádné označené otázky",
            empty_subtitle='Stiskni "F" nebo klikni na bookmark v quizu.',
            on_record=_record("flagged"),
        ).run()
