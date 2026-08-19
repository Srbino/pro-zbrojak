"""Dashboard (hlavni prehled)."""
from __future__ import annotations

import datetime as dt

from nicegui import ui

from src.auth import require_login
from src.db import traps
from src.db.questions import load_questions
from src.db.store import (
    all_flagged,
    get_active_marathon,
    get_db,
    question_ids_with_mistakes,
    stats_overall,
    stats_per_section,
)
from src.learning import srs as srs_mod
from src.learning.heatmap import daily_counts
from src.ui.components import (
    SECTION_LABEL,
    hero_primary,
    mode_tile,
    progress_bar,
    stat_card,
)
from src.ui.layout import nav_items_for_dashboard, page_shell
from src.version import VERSION

APP_NAME = "Pro Zbroják"


@ui.page("/")
def index_page():
    user = require_login()
    if user is None:
        return
    with page_shell("Přehled", active_path="/"):
        db = get_db()
        questions = load_questions()
        total = len(questions)
        ov = stats_overall(db, user.email)
        per_sec = stats_per_section(db, questions, user.email)
        active_run = get_active_marathon(db, user.email)
        n_due = len(srs_mod.due_today(db, user.email, limit=999))
        n_srs_total = srs_mod.total_cards(db, user.email)
        n_mistakes = len(question_ids_with_mistakes(db, user.email))
        n_flagged = len(all_flagged(db, user.email))

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

        n_traps = traps.count()
        badges = {
            "/srs":      str(n_due) if n_due > 0 else None,
            "/mistakes": str(n_mistakes) if n_mistakes else None,
            "/flagged":  str(n_flagged) if n_flagged else None,
            "/traps":    str(n_traps) if n_traps else None,
        }
        disabled = {
            "/mistakes": n_mistakes == 0,
            "/flagged":  n_flagged == 0,
            "/traps":    n_traps == 0,
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
        heatmap = daily_counts(db, user.email, days=90)
        if any(v > 0 for v in heatmap.values()):
            ui.label("Aktivita (90 dní)").classes("zp-h2 zp-mt-xl zp-mb-sm")
            with ui.element("div").classes("zp-card"):
                _render_heatmap(heatmap)

        # --- FOOTER ---
        ui.element("div").style("height: 3rem;")
        with ui.row().classes("zp-row zp-gap-xs w-full").style("justify-content: center;"):
            ui.label(f"{APP_NAME} v{VERSION}").classes("zp-caption")
            ui.label("·").classes("zp-caption")
            ui.label("studijní pomůcka — ZOZ podle zák. 90/2024 Sb. a NV 238/2025 Sb.").classes("zp-caption")


# ---------- helpers (private to this module) ----------

def _plural_otazky(n: int) -> str:
    """Česká shoda: 1 otázku, 2–4 otázky, 5+ otázek."""
    if n == 1:
        return "otázku"
    return "otázky" if 2 <= n <= 4 else "otázek"


def _render_hero(*, total: int, active_run, n_due: int, ov: dict):
    if n_due > 0:
        hero_primary(
            title=f"Dnes máš {n_due} {_plural_otazky(n_due)} k opakování",
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
            title=f"Vítej v Pro Zbrojáku! {total} otázek připraveno.",
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


MONTHS_CS = ["led", "úno", "bře", "dub", "kvě", "čvn",
             "čvc", "srp", "zář", "říj", "lis", "pro"]

# Rozměr jedné buňky a mezery — musí sedět s .zp-hm-body v theme.py,
# protože podle toho se počítá šířka popisků měsíců.
_HM_CELL = 11
_HM_GAP = 3


def _render_heatmap(daily: dict[str, int]):
    """Heatmapa aktivity — sloupec je týden, řádek den v týdnu.

    Buňky se vypisují PO SLOUPCÍCH, protože mřížka má `grid-auto-flow: column`.
    Dřív se plnily po řádcích do `repeat(n, 1fr)`, což je roztáhlo na pruhy
    přes celý týden a popisky měsíců spadly pod sebe.
    """
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
        if cnt == 0:
            return 0
        if max_count <= 1:
            return 4
        if cnt <= max_count * 0.25:
            return 1
        if cnt <= max_count * 0.50:
            return 2
        if cnt <= max_count * 0.75:
            return 3
        return 4

    # Popisky měsíců — každý zabere tolik, kolik má týdnů, aby seděl nad nimi.
    month_starts: list[tuple[int, str]] = []
    last_month = None
    for c in range(n_cols):
        d = start + dt.timedelta(days=c * 7)
        if d.month != last_month:
            month_starts.append((c, MONTHS_CS[d.month - 1]))
            last_month = d.month

    step = _HM_CELL + _HM_GAP
    day_labels = ["Po", "", "St", "", "Pá", "", "Ne"]

    parts = ['<div class="zp-hm">']

    # Sloupec s názvy dnů stojí mimo mřížku, takže mřížku nedeformuje.
    parts.append('<div class="zp-hm-days">')
    parts.extend(f"<span>{lbl}</span>" for lbl in day_labels)
    parts.append("</div>")

    parts.append('<div class="zp-hm-scroll">')
    parts.append('<div class="zp-hm-months">')
    for i, (col, name) in enumerate(month_starts):
        end = month_starts[i + 1][0] if i + 1 < len(month_starts) else n_cols
        width = (end - col) * step
        # Pod dva týdny se název měsíce nevejde a ořízl by se do nesmyslu.
        text = name if width >= 2 * step else ""
        parts.append(f'<span class="zp-hm-month" style="width:{width}px;">{text}</span>')
    parts.append("</div>")

    parts.append('<div class="zp-hm-body">')
    for col in range(n_cols):          # po sloupcích — grid-auto-flow: column
        for row in range(7):
            if (row, col) in cells:
                cnt, iso = cells[(row, col)]
                parts.append(
                    f'<div class="zp-hm-cell zp-hm-l{_level(cnt)}" '
                    f'title="{iso}: {cnt} odpovědí"></div>'
                )
            else:
                parts.append('<div class="zp-hm-cell zp-hm-l0"></div>')
    parts.append("</div></div></div>")

    parts.append(
        '<div class="zp-hm-legend"><span>Méně</span>'
        '<span class="zp-hm-cell zp-hm-l0"></span>'
        '<span class="zp-hm-cell zp-hm-l1"></span>'
        '<span class="zp-hm-cell zp-hm-l2"></span>'
        '<span class="zp-hm-cell zp-hm-l3"></span>'
        '<span class="zp-hm-cell zp-hm-l4"></span>'
        '<span>Více</span></div>'
    )
    ui.html("".join(parts)).classes("w-full")
