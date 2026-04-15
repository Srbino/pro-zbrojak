"""Icon registry — semantic name -> Material Symbols.

Jeden zdroj pravdy pro vsechny ikony v UI. NiceGUI dostane Material Symbols
z Quasar frameworku zdarma — `ui.icon("dashboard")` staci.

Pouziti:
    from src.ui.icons import I, icon
    ui.icon(I["marathon"])          # primo
    icon("marathon", size="lg")     # helper s velikostmi
"""
from __future__ import annotations

from nicegui import ui


# Sémantické jméno → Material Symbols glyph (https://fonts.google.com/icons)
I: dict[str, str] = {
    # Navigace
    "dashboard":    "dashboard",
    "marathon":     "directions_run",
    "srs":          "psychology",
    "random":       "shuffle",
    "mistakes":     "track_changes",
    "mastery":      "school",
    "exam":         "edit_note",
    "flagged":      "bookmarks",
    "export":       "ios_share",
    "settings":     "settings",
    "help":         "help_outline",
    "menu":         "menu",
    "dark":         "dark_mode",
    "light":        "light_mode",
    "brand":        "adjust",
    # Akce
    "next":         "arrow_forward",
    "back":         "arrow_back",
    "home":         "home",
    "play":         "play_arrow",
    "refresh":      "refresh",
    "close":        "close",
    "check":        "check",
    "skip":         "skip_next",
    "stop":         "stop",
    "download":     "download",
    "upload":       "upload",
    "copy":         "content_copy",
    "zoom":         "zoom_in",
    "delete":       "delete_forever",
    # Status / výsledky
    "success":      "check_circle",
    "error":        "cancel",
    "warning":      "warning",
    "info":         "info",
    "timer":        "timer",
    "trophy":       "emoji_events",
    "fitness":      "fitness_center",
    "insights":     "insights",
    "image":        "image",
    "schedule":     "schedule",
    # Bookmark states
    "bookmark":     "bookmark",
    "bookmark_off": "bookmark_border",
    # Rating (SRS)
    "rate_again":   "undo",
    "rate_hard":    "trending_down",
    "rate_good":    "trending_flat",
    "rate_easy":    "trending_up",
}


_SIZE_CLASS = {
    "xs": "text-sm",
    "sm": "text-base",
    "md": "text-xl",
    "lg": "text-3xl",
    "xl": "text-5xl",
    "2xl": "text-6xl",
}


def icon(name: str, *, size: str = "sm", color: str | None = None, cls: str = ""):
    """DRY helper pro ui.icon(I[name]) s velikosti a barvou.

    Args:
        name: semantic key from I dict
        size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
        color: CSS color value (hex, var, or Quasar color)
        cls: extra css classes
    """
    glyph = I.get(name, name)  # fallback: allow raw material symbol name
    el = ui.icon(glyph)
    el.classes(_SIZE_CLASS.get(size, _SIZE_CLASS["sm"]) + (" " + cls if cls else ""))
    if color:
        el.style(f"color: {color};")
    return el
