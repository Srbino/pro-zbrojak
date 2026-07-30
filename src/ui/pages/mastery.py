"""Mastery podle oblasti — trenink dokud nezvladnes 90% na poslednich 30."""
from __future__ import annotations

from collections import defaultdict

from nicegui import ui

from src.auth import require_login
from src.db.questions import load_questions
from src.db.store import get_db, record_attempt
from src.ui.components import (
    SECTION_LABEL,
    QuizSession,
    query_str,
)
from src.ui.icons import I
from src.ui.layout import page_shell

THRESHOLD_PCT = 90    # hranice zvládnutí oblasti
SAMPLE_TARGET = 30    # kolik posledních odpovědí se hodnotí


def _mastery_meter(pct: float, *, mastered: bool, sparse: bool, seen: bool) -> None:
    """Pruh úspěšnosti s ryskou na hranici zvládnutí."""
    classes = "zp-meter-fill"
    if mastered:
        classes += " ok"
    elif seen and pct < 65:
        classes += " low"
    if sparse:
        classes += " sparse"
    width = max(0.0, min(100.0, pct))
    ui.html(
        '<div class="zp-meter">'
        f'<div class="{classes}" style="width:{width}%;"></div>'
        f'<div class="zp-meter-mark" style="left:{THRESHOLD_PCT}%;" '
        f'data-label="{THRESHOLD_PCT} %"></div>'
        "</div>"
    )


@ui.page("/mastery")
def mastery_page():
    user = require_login()
    if user is None:
        return
    db = get_db()
    questions = load_questions()

    with page_shell("Mastery", active_path="/mastery"):
        ui.label("Mastery podle oblasti").classes("zp-display")
        ui.label(
            f"Oblast je zvládnutá při ≥ {THRESHOLD_PCT} % z posledních {SAMPLE_TARGET} odpovědí. "
            "Počítají se odpovědi ze všech režimů, ne jen odsud — co jsi zvládl "
            "v marathonu, se ti tu tedy započítá. Dokud odpovědí není "
            f"{SAMPLE_TARGET}, je pruh šrafovaný: číslo platí, ale stojí na malém vzorku."
        ).classes("zp-body zp-prose zp-mb-lg")

        recent_per_sec: dict[str, list[int]] = defaultdict(list)
        qid_to_sec = {q["id"]: q.get("section") for q in questions}
        rows = list(db.query(
            "SELECT question_id, is_correct FROM attempts WHERE user_email=? ORDER BY ts DESC",
            [user.email],
        ))
        for r in rows:
            sec = qid_to_sec.get(r["question_id"])
            if sec and len(recent_per_sec[sec]) < 30:
                recent_per_sec[sec].append(r["is_correct"])

        with ui.element("div").classes("zp-grid-2"):
            for sec, label in SECTION_LABEL.items():
                pool_n = sum(1 for q in questions if q.get("section") == sec)
                if pool_n == 0:
                    continue
                recent = recent_per_sec.get(sec, [])
                n = len(recent)
                # Skutečná úspěšnost. Dřív se násobila koeficientem n/30, takže
                # 80 % z pěti odpovědí se kreslilo jako 13 % a vypadalo to jako
                # chyba. Malý vzorek se teď přizná štítkem a šrafováním, ne tím,
                # že se číslo potichu stlačí dolů.
                pct = round(sum(recent) / n * 100, 1) if n else 0.0
                mastered = pct >= THRESHOLD_PCT and n >= SAMPLE_TARGET
                sparse = 0 < n < SAMPLE_TARGET

                with ui.element("div").classes("zp-card"):
                    with ui.row().classes("zp-row-between zp-nowrap w-full zp-gap-sm"):
                        ui.label(label).classes("zp-h3 zp-flex-1")
                        if mastered:
                            ui.html('<span class="zp-badge success">zvládnuto</span>')
                        elif sparse:
                            ui.html('<span class="zp-badge neutral">málo dat</span>')
                        elif n and pct >= 75:
                            ui.html('<span class="zp-badge warning">blízko</span>')

                    _mastery_meter(pct, mastered=mastered, sparse=sparse, seen=bool(n))

                    with ui.row().classes("zp-row-between w-full zp-mt-sm zp-gap-sm").style(
                        "flex-wrap: wrap;"
                    ):
                        if n:
                            detail = (
                                f"{pct} % z {n}/{SAMPLE_TARGET} posledních odpovědí"
                                "  ·  napříč režimy"
                            )
                        else:
                            detail = f"{pool_n} otázek  ·  zatím bez pokusu"
                        ui.label(detail).classes("zp-body-sm zp-flex-1")
                        ui.button("Trénovat" if n else "Začít", icon=I["next"],
                                  on_click=lambda s=sec: ui.navigate.to(f"/mastery/run?section={s}")).props(
                            "flat dense color=primary"
                        )


@ui.page("/mastery/run")
def mastery_run_page():
    user = require_login()
    if user is None:
        return
    section = query_str("section", "pravo")
    pool = [q for q in load_questions() if q.get("section") == section]
    title = f"Mastery — {SECTION_LABEL.get(section, section)}"
    db = get_db()

    def _rec(qid, chosen, correct, ms):
        record_attempt(db, user_email=user.email, question_id=qid, chosen=chosen,
                       correct=correct, mode="mastery", time_ms=ms)

    with page_shell(title, active_path="/mastery"):
        QuizSession(
            pool=pool, mode="mastery",
            user_email=user.email,
            empty_icon="info", empty_heading="Prázdná oblast",
            empty_subtitle="V této oblasti nejsou otázky.",
            on_record=_rec,
            show_navigator=True,
        ).run()
