"""Dashboard (hlavni prehled)."""
from __future__ import annotations

import datetime as dt

from nicegui import ui

from src.db.questions import load_questions
from src.db.store import (
    get_db, stats_overall, stats_per_section, get_active_marathon,
    question_ids_with_mistakes, all_flagged,
)
from src.learning import srs as srs_mod
from src.learning.heatmap import daily_counts
from src.ui.components import (
    SECTION_LABEL, hero_primary, stat_card, mode_tile, progress_bar,
)
from src.ui.icons import I, icon
from src.ui.layout import NAV_ITEMS, nav_items_for_dashboard, page_shell


VERSION = "0.3.0"


@ui.page("/")
def index_page():
    with page_shell("Přehled", active_path="/"):
        db = get_db()
        questions = load_questions()
        total = len(questions)
        ov = stats_overall(db)
        per_sec = stats_per_section(db, questions)
        active_run = get_active_marathon(db)
        n_due = len(srs_mod.due_today(db, limit=999))
        n_srs_total = srs_mod.total_cards(db)
        n_mistakes = len(question_ids_with_mistakes(db))
        n_flagged = len(all_flagged(db))

        # --- HERO ---
        _render_hero(total=total, active_run=active_run, n_due=n_due, ov=ov)

        # --- STATS GRID ---
        ui.label("Statistika").classes("zp-h2 zp-mt-xl zp-mb-sm")
        with ui.element("div").classes("zp-grid-4"):
            stat_card("Pokusů celkem", str(ov["attempts"]),
                      sub="všech odpovědí v historii",
                      icon_name="insights")
            ok_color = "success" if ov["pct"] >= 85 else ("warning" if ov["pct"] >= 65 else "danger")
            stat_card("Úspěšnost", f"{ov['pct']} %",
                      sub=f"{ov['correct']} správně / {ov['attempts']}",
                      accent=ok_color if ov["attempts"] else None,
                      icon_name="success" if ov["pct"] >= 85 else "warning")
            stat_card("V SRS systému", str(n_srs_total),
                      sub=f"{n_due} dnes k opakování",
                      accent="primary" if n_due > 0 else None,
                      icon_name="srs")
            stat_card("Chybných otázek", str(n_mistakes),
                      sub=("k zopakování v režimu Lekce z chyb" if n_mistakes else "zatím bez chyb"),
                      accent="danger" if n_mistakes > 10 else None,
                      icon_name="mistakes")

        # --- PRIMARY TILE (Marathon) ---
        ui.label("Režimy učení").classes("zp-h2 zp-mt-xl zp-mb-sm")
        marathon_cta = (
            f"Pokračovat od otázky {active_run['position']+1}"
            if active_run else "Začít nový běh"
        )
        mode_tile(
            path="/marathon", icon_name="marathon",
            title="Marathon",
            description=f"Projdi celý katalog — {total} otázek po pořadí",
            cta=marathon_cta, highlight=True,
        )

        # --- SECONDARY TILES ---
        # Vytvari tiles ze zdroje pravdy (NAV_ITEMS), takze se nemusi rucne
        # duplikovat ikony a popisy. Vynecha dashboard + marathon (jiz rendered).
        tiles = [it for it in nav_items_for_dashboard() if it.path not in ("/marathon", "/settings")]

        badges = {
            "/srs":      str(n_due) if n_due > 0 else None,
            "/mistakes": str(n_mistakes) if n_mistakes else None,
            "/flagged":  str(n_flagged) if n_flagged else None,
        }
        disabled = {
            "/mistakes": n_mistakes == 0,
            "/flagged":  n_flagged == 0,
        }

        with ui.element("div").classes("zp-grid-3 zp-mt-sm"):
            for it in tiles:
                mode_tile(
                    path=it.path,
                    icon_name=it.icon_key,
                    title=it.label,
                    description=it.description,
                    badge=badges.get(it.path),
                    disabled=disabled.get(it.path, False),
                )

        # --- SECTION SUCCESS ---
        if per_sec:
            ui.label("Úspěšnost podle oblasti").classes("zp-h2 zp-mt-xl zp-mb-sm")
            with ui.element("div").classes("zp-grid-2"):
                for sec_key, label in SECTION_LABEL.items():
                    if sec_key not in per_sec:
                        continue
                    b = per_sec[sec_key]
                    _section_row(label, b["correct"], b["attempts"], b["pct"])

        # --- HEATMAP ---
        heatmap = daily_counts(db, days=90)
        if any(v > 0 for v in heatmap.values()):
            ui.label("Aktivita (90 dní)").classes("zp-h2 zp-mt-xl zp-mb-sm")
            with ui.element("div").classes("zp-card"):
                _render_heatmap(heatmap)

        # --- FOOTER ---
        ui.element("div").style("height: 3rem;")
        with ui.row().classes("zp-row zp-gap-xs w-full").style("justify-content: center;"):
            ui.label(f"v{VERSION}").classes("zp-caption")
            ui.label("·").classes("zp-caption")
            ui.label("studijní pomůcka").classes("zp-caption")


# ---------- helpers (private to this module) ----------

def _render_hero(*, total: int, active_run, n_due: int, ov: dict):
    if n_due > 0:
        hero_primary(
            title=f"Dnes máš {n_due} otázek k opakování",
            subtitle="Spaced repetition drží znalosti dlouhodobě. Zabere to ~5–10 min.",
            cta_label="Začít review", cta_target="/srs",
        )
    elif active_run is not None:
        pos = active_run["position"]
        correct = active_run["correct"]
        pct = round(correct / max(1, pos) * 100, 1) if pos > 0 else 0
        hero_primary(
            title=f"Pokračovat v maratonu: {pos+1} / {active_run['total']}",
            subtitle=f"Zatím správně {correct}/{pos} ({pct} %). Jeden krok blíž ke zvládnutí celého katalogu.",
            cta_label="Pokračovat", cta_target="/marathon",
        )
    elif ov["attempts"] == 0:
        hero_primary(
            title=f"Vítej! {total} otázek připraveno.",
            subtitle="Doporučujeme začít Marathonem — projdeš celý katalog po pořadí a objevíš, kde jsi slabý.",
            cta_label="Začít Marathon", cta_target="/marathon",
        )
    else:
        hero_primary(
            title="Co dnes?",
            subtitle="Nejlepší je krátké SRS nebo lekce z chyb. Před zkouškou spusť simulaci.",
            cta_label="Simulace zkoušky", cta_target="/exam",
        )


def _section_row(label: str, correct: int, attempts: int, pct: float):
    variant = "success" if pct >= 85 else ("primary" if pct >= 65 else "danger")
    with ui.element("div").classes("zp-card"):
        with ui.row().classes("zp-row-between w-full").style("align-items: baseline;"):
            ui.label(label).classes("zp-h3")
            ui.label(f"{pct} %").classes("zp-metric-sm")
        progress_bar(pct / 100.0, variant=variant)
        ui.label(f"{correct} / {attempts} správně").classes("zp-caption zp-mt-xs")


def _render_heatmap(daily: dict[str, int]):
    """GitHub-style heatmap jako CSS grid — plne responzivni, bez knihovny."""
    items = sorted(daily.items())
    if not items:
        return
    first_date = dt.date.fromisoformat(items[0][0])
    monday_offset = first_date.weekday()
    start = first_date - dt.timedelta(days=monday_offset)

    cells: dict[tuple[int, int], tuple[int, str]] = {}
    for iso, cnt in items:
        d = dt.date.fromisoformat(iso)
        delta = (d - start).days
        col, row = delta // 7, delta % 7
        cells[(row, col)] = (cnt, iso)

    n_cols = max((c for (_, c) in cells.keys()), default=0) + 1

    # Determine max for binning
    max_count = max((v[0] for v in cells.values()), default=0)

    def _level(cnt: int) -> int:
        if cnt == 0: return 0
        if max_count <= 1: return 4
        if cnt <= max_count * 0.25: return 1
        if cnt <= max_count * 0.50: return 2
        if cnt <= max_count * 0.75: return 3
        return 4

    # Build month labels (first week of each month)
    month_cols: list[tuple[int, str]] = []
    last_month = None
    for c in range(n_cols):
        d = start + dt.timedelta(days=c * 7)
        m = d.strftime("%b")
        if m != last_month:
            month_cols.append((c, m))
            last_month = m

    # Build HTML
    day_labels = ["Po", "", "St", "", "Pá", "", "Ne"]
    html_parts = ['<div class="zp-hm">']
    # Months row
    html_parts.append('<div class="zp-hm-months">')
    prev_col = 0
    for col, m in month_cols:
        if col > prev_col:
            # spacer
            html_parts.append(f'<span style="grid-column: span {col - prev_col};"></span>')
        html_parts.append(f'<span class="zp-hm-month" style="grid-column: span 1;">{m}</span>')
        prev_col = col + 1
    html_parts.append('</div>')
    # Days grid (rows × cols)
    html_parts.append(f'<div class="zp-hm-body" style="grid-template-columns: 20px repeat({n_cols}, 1fr);">')
    for row in range(7):
        # Day label
        html_parts.append(f'<div class="zp-hm-day">{day_labels[row]}</div>')
        for col in range(n_cols):
            if (row, col) in cells:
                cnt, iso = cells[(row, col)]
                lvl = _level(cnt)
                html_parts.append(
                    f'<div class="zp-hm-cell zp-hm-l{lvl}" title="{iso}: {cnt} odpovědí"></div>'
                )
            else:
                html_parts.append('<div class="zp-hm-cell"></div>')
    html_parts.append('</div>')
    html_parts.append('</div>')

    # Legend
    html_parts.append(
        '<div class="zp-hm-legend">'
        '<span>Méně</span>'
        '<span class="zp-hm-cell zp-hm-l0"></span>'
        '<span class="zp-hm-cell zp-hm-l1"></span>'
        '<span class="zp-hm-cell zp-hm-l2"></span>'
        '<span class="zp-hm-cell zp-hm-l3"></span>'
        '<span class="zp-hm-cell zp-hm-l4"></span>'
        '<span>Více</span>'
        '</div>'
    )
    ui.html("".join(html_parts)).classes("w-full").style("width: 100%; display: block;")
