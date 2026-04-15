"""Export chybnych otazek do Markdownu pro Claude Code."""
from __future__ import annotations

from nicegui import ui

from src.db.questions import by_id
from src.db.store import (
    get_db, top_mistakes, question_ids_with_mistakes, all_flagged,
)
from src.export.claude_md import export_questions, export_single
from src.ui.components import SECTION_LABEL, SECTION_BADGE_VARIANT, section_badge
from src.ui.icons import I
from src.ui.layout import page_shell


@ui.page("/export")
def export_page():
    db = get_db()
    qmap = by_id()
    bad_ids = question_ids_with_mistakes(db)
    flagged_ids = all_flagged(db)

    with page_shell("Export pro Claude Code", active_path="/export"):
        ui.label("Export pro Claude Code").classes("zp-display")
        ui.label(
            "Vygeneruje Markdown s otázkami, tvou odpovědí, správnou odpovědí a hotovým promptem. "
            "Otevři výsledný soubor v Claude Code a nech si vysvětlit obtížné otázky s citacemi z aktuální legislativy."
        ).classes("zp-body zp-prose zp-mb-lg")

        with ui.element("div").classes("zp-card w-full zp-mb-md"):
            ui.label("Co exportovat").classes("zp-h3 zp-mb-sm")
            opt_mistakes = ui.checkbox(f"Otázky s chybami ({len(bad_ids)})", value=True)
            opt_flagged = ui.checkbox(f"Označené otázky ({len(flagged_ids)})", value=False)
            limit = ui.number("Maximum otázek (0 = vše)", value=20, min=0, max=500).props(
                "outlined"
            ).classes("w-48 zp-mt-sm")

            def do_export():
                qids: list[str] = []
                if opt_mistakes.value:
                    qids += bad_ids
                if opt_flagged.value:
                    qids += [q for q in flagged_ids if q not in qids]
                if not qids:
                    ui.notify("Žádné otázky k exportu", color="warning", position="top")
                    return
                if limit.value > 0:
                    qids = qids[:int(limit.value)]
                qs = [qmap[qid] for qid in qids if qid in qmap]
                path = export_questions(qs, filename_hint="explain")
                ui.notify(f"Uloženo: {path.name}", position="top", timeout=4000)
                try:
                    import pyperclip
                    pyperclip.copy(str(path))
                except Exception:
                    pass

            ui.button("Vygenerovat Markdown", icon=I["download"], on_click=do_export).props(
                "color=primary unelevated size=md"
            ).classes("zp-mt-md")

        if bad_ids:
            ui.label("Top chybované otázky").classes("zp-h2 zp-mt-xl zp-mb-sm")
            with ui.element("div").classes("zp-card").style("padding: 0;"):
                for i, row in enumerate(top_mistakes(db, 20)):
                    q = qmap.get(row["question_id"])
                    if not q:
                        continue
                    sec = q.get("section") or "unknown"
                    border = "border-top: 1px solid var(--zp-border);" if i > 0 else ""
                    with ui.row().classes("zp-row zp-nowrap w-full").style(
                        f"padding: .75rem 1rem; {border}"
                    ):
                        ui.html(
                            f'<span class="zp-badge danger" style="min-width:auto;">{row["wrong"]}×</span>'
                        )
                        ui.label(f"Q{q['pdf_number']}").classes("zp-body-sm zp-mono").style(
                            "width: 60px; margin-left: .75rem;"
                        )
                        section_badge(sec)
                        ui.label(q["question"][:110]).classes("zp-body-sm").style(
                            "margin-left: .75rem; flex: 1;"
                        )

                        def make_export(qq):
                            def _ex():
                                path = export_single(qq)
                                ui.notify(f"Uloženo → {path.name}", position="top")
                            return _ex
                        ui.button(icon=I["upload"], on_click=make_export(q)).props(
                            "flat dense round"
                        ).tooltip("Export jen této otázky")
