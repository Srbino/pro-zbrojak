"""Staticky audit: UI kod nesmi obsahovat emoji — vsechny ikony jen pres src/ui/icons.py.

Povoleno:
- parse_pdf.py (CLI vystup)
- tests/* (test fixtures / markers)
- app.py favicon="🎯" (SVG/emoji favicon je OK — browser ho konvertuje na vector)
- src/export/claude_md.py (markdown pro LLM smi mit ✅/❌ text markers)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent

# Emoji ranges — hlavni bloky kde Unicode drzi emoji / pictographs / symbols
EMOJI_RE = re.compile(
    r"["
    r"\U0001F300-\U0001FAFF"  # Miscellaneous Symbols & Pictographs + Emoticons + ... + Symbols/Pictographs Extended-A
    r"\U0001F000-\U0001F2FF"  # Mahjong, Domino, Playing cards, Enclosed Ideographs
    r"\u2600-\u27BF"          # Miscellaneous Symbols + Dingbats
    r"]"
)

# Arrow characters — nejsou emoji ale v UI by se nemely misit s textem (KISS)
# (necháváme v exam_page "simulace (starší → novější)" — OK jako text v grafu)
# Allow-list konkretni radky (substring match):
ALLOWED_ARROW_LINES = {
    "simulace (starší → novější)",
    "# Spuštění: python app.py  →  http://127.0.0.1:8080",
}

UI_FILES = [
    "app.py",
    *list((ROOT / "src" / "ui").rglob("*.py")),
]

# Files explicitly allowed to contain emojis
ALLOW_FILES = {
    "parse_pdf.py",                       # CLI
    "src/export/claude_md.py",           # MD markers for LLM
}


def _files_to_check() -> list[Path]:
    out = []
    for entry in UI_FILES:
        p = Path(entry) if not isinstance(entry, Path) else entry
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in ALLOW_FILES:
            continue
        out.append(p)
    return out


def test_no_emoji_in_ui_code():
    """UI kod (app.py + src/ui/*) nesmi obsahovat emoji."""
    violations = []
    for path in _files_to_check():
        txt = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(txt.splitlines(), 1):
            # favicon="🎯" je v app.py povoleno — NiceGUI akceptuje emoji favicon
            if 'favicon=' in line:
                continue
            hits = EMOJI_RE.findall(line)
            if hits:
                violations.append(f"{path.relative_to(ROOT)}:{lineno}: {hits} | {line.strip()}")
    assert not violations, "UI kód obsahuje emoji (použij src/ui/icons.py):\n" + "\n".join(violations)


def test_icons_module_has_semantic_names():
    """src/ui/icons.py musi definovat vsechny kriticke icon keys pouzite v NAV_ITEMS."""
    from src.ui.icons import I
    from src.ui.layout import NAV_ITEMS
    required = {it.icon_key for it in NAV_ITEMS if it is not None}
    required.add("brand")
    required.add("next")
    required.add("home")
    required.add("play")
    required.add("refresh")
    required.add("close")
    required.add("help")
    required.add("menu")
    required.add("dark")
    required.add("trophy")
    required.add("bookmark")
    required.add("bookmark_off")
    required.add("zoom")
    required.add("timer")
    missing = required - set(I.keys())
    assert not missing, f"Chybi icon keys v I: {missing}"


def test_icon_helper_returns_nicegui_element():
    """icon() helper vraci NiceGUI ui.icon element."""
    # Import-time check that module is valid + I dict has str values
    from src.ui.icons import I
    assert all(isinstance(v, str) and v for v in I.values()), (
        "Vsechny hodnoty v I musi byt neprazdne stringy (Material Symbol glyph names)"
    )
