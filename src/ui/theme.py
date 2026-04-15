"""Design system — globalni CSS, colors, typography.

Pridava se do kazde stranky pres `apply_theme()`.
"""
from __future__ import annotations

from nicegui import ui


# --- Color palette ---
# Primary: tmavsi modra (zbrojni / srs / trust)
# Accent: zlutooranzova (akce, highlight)
# Semantic: success / danger / warning / info
COLORS = {
    "primary": "#1E40AF",       # indigo-800
    "primary_soft": "#DBEAFE",  # indigo-100
    "accent": "#F59E0B",        # amber-500
    "success": "#16A34A",       # green-600
    "danger": "#DC2626",        # red-600
    "warning": "#F59E0B",
    "info": "#0EA5E9",          # sky-500
    "neutral_50": "#F9FAFB",
    "neutral_100": "#F3F4F6",
    "neutral_200": "#E5E7EB",
    "neutral_300": "#D1D5DB",
    "neutral_500": "#6B7280",
    "neutral_700": "#374151",
    "neutral_900": "#111827",
}

# Globalni CSS vkladany jednou do <head>
GLOBAL_CSS = """
:root {
  --zp-primary: #1E40AF;
  --zp-primary-soft: #DBEAFE;
  --zp-accent: #F59E0B;
  --zp-success: #16A34A;
  --zp-danger: #DC2626;
  --zp-text: #111827;
  --zp-text-soft: #6B7280;
  --zp-surface: #FFFFFF;
  --zp-bg: #F9FAFB;
  --zp-border: #E5E7EB;
  --zp-radius: 12px;
  --zp-radius-sm: 8px;
  --zp-shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --zp-shadow: 0 4px 14px rgba(0,0,0,0.06);
  --zp-shadow-lg: 0 20px 40px rgba(0,0,0,0.1);
}

body.body--dark, body.dark, html.dark, .dark {
  --zp-text: #F9FAFB;
  --zp-text-soft: #9CA3AF;
  --zp-surface: #1F2937;
  --zp-bg: #111827;
  --zp-border: #374151;
}

body { background: var(--zp-bg) !important; color: var(--zp-text); }

/* Typography scale */
.zp-display { font-size: 2.25rem; font-weight: 700; line-height: 1.1; letter-spacing: -0.02em; color: var(--zp-text); }
.zp-h1      { font-size: 1.75rem; font-weight: 700; line-height: 1.2; letter-spacing: -0.015em; color: var(--zp-text); }
.zp-h2      { font-size: 1.25rem; font-weight: 600; line-height: 1.3; color: var(--zp-text); }
.zp-h3      { font-size: 1.05rem; font-weight: 600; line-height: 1.4; color: var(--zp-text); }
.zp-body    { font-size: 1rem; line-height: 1.55; color: var(--zp-text); }
.zp-body-sm { font-size: 0.875rem; line-height: 1.5; color: var(--zp-text-soft); }
.zp-caption { font-size: 0.75rem; line-height: 1.4; color: var(--zp-text-soft); letter-spacing: 0.02em; }
.zp-metric  { font-size: 2rem; font-weight: 700; line-height: 1; letter-spacing: -0.02em; color: var(--zp-text); font-variant-numeric: tabular-nums; }
.zp-metric-sm { font-size: 1.25rem; font-weight: 600; font-variant-numeric: tabular-nums; color: var(--zp-text); }
.zp-mono    { font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace; font-variant-numeric: tabular-nums; }

/* Cards */
.zp-card {
  background: var(--zp-surface);
  border: 1px solid var(--zp-border);
  border-radius: var(--zp-radius);
  box-shadow: var(--zp-shadow-sm);
  padding: 1.25rem;
  transition: box-shadow .2s ease, transform .15s ease, border-color .2s ease;
}
.zp-card.clickable { cursor: pointer; }
.zp-card.clickable:hover { box-shadow: var(--zp-shadow); transform: translateY(-2px); border-color: var(--zp-primary); }

/* Tiles */
.zp-tile {
  background: var(--zp-surface);
  border: 1px solid var(--zp-border);
  border-radius: var(--zp-radius);
  padding: 1.25rem;
  cursor: pointer;
  transition: all .18s ease;
  position: relative;
  overflow: hidden;
  display: flex; flex-direction: column; gap: .35rem;
  min-height: 120px;
}
.zp-tile:hover { transform: translateY(-2px); box-shadow: var(--zp-shadow); border-color: var(--zp-primary); }
.zp-tile.primary { background: linear-gradient(135deg, var(--zp-primary) 0%, #312E81 100%); color: white; border-color: transparent; }
.zp-tile.primary .zp-body-sm, .zp-tile.primary .zp-caption { color: rgba(255,255,255,0.85); }
.zp-tile .tile-icon { font-size: 1.5rem; margin-bottom: .25rem; }
.zp-tile-title { font-size: 1.05rem; font-weight: 600; }
.zp-tile-badge {
  position: absolute; top: .75rem; right: .75rem;
  background: var(--zp-accent); color: #111827;
  font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 999px;
}
.zp-tile.primary .zp-tile-badge { background: var(--zp-accent); color: #111827; }

/* Stat card */
.zp-stat {
  display: flex; flex-direction: column; gap: .125rem;
  padding: .5rem 1rem;
  border-right: 1px solid var(--zp-border);
}
.zp-stat:last-child { border-right: 0; }

/* Quiz option buttons */
.zp-opt {
  display: block !important;
  width: 100%;
  text-align: left !important;
  background: var(--zp-surface) !important;
  color: var(--zp-text) !important;
  border: 1.5px solid var(--zp-border) !important;
  border-radius: var(--zp-radius-sm) !important;
  padding: .85rem 1rem !important;
  margin: 0 !important;
  font-size: 0.97rem !important;
  line-height: 1.45 !important;
  transition: all .15s ease;
  text-transform: none !important;
  letter-spacing: normal !important;
  font-weight: 400 !important;
}
.zp-opt:hover { border-color: var(--zp-primary) !important; background: var(--zp-primary-soft) !important; }
.zp-opt .opt-key {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border-radius: 8px;
  background: var(--zp-neutral-100, #F3F4F6);
  color: var(--zp-text-soft);
  font-weight: 600; font-size: .85rem;
  margin-right: .75rem;
  vertical-align: middle;
  flex-shrink: 0;
}
body.body--dark .zp-opt .opt-key, body.dark .zp-opt .opt-key, .dark .zp-opt .opt-key { background: #374151; color: #E5E7EB; }
.zp-opt.correct { border-color: var(--zp-success) !important; background: #ECFDF5 !important; color: #14532D !important; }
.zp-opt.correct .opt-key { background: var(--zp-success); color: white; }
.zp-opt.wrong { border-color: var(--zp-danger) !important; background: #FEF2F2 !important; color: #7F1D1D !important; }
.zp-opt.wrong .opt-key { background: var(--zp-danger); color: white; }
.zp-opt.dimmed { opacity: .55; }
.zp-opt.disabled { pointer-events: none; }
body.body--dark .zp-opt, body.dark .zp-opt, .dark .zp-opt { background: #1F2937 !important; color: #E5E7EB !important; }
body.body--dark .zp-opt:hover, body.dark .zp-opt:hover, .dark .zp-opt:hover { background: #1E3A8A !important; }
body.body--dark .zp-opt.correct, body.dark .zp-opt.correct, .dark .zp-opt.correct { background: #064E3B !important; color: #A7F3D0 !important; }
body.body--dark .zp-opt.wrong, body.dark .zp-opt.wrong, .dark .zp-opt.wrong { background: #7F1D1D !important; color: #FECACA !important; }

/* Section badges */
.zp-badge {
  display: inline-flex; align-items: center; gap: .25rem;
  padding: 3px 10px; border-radius: 999px;
  font-size: .72rem; font-weight: 600; letter-spacing: .02em;
  background: var(--zp-primary-soft);
  color: var(--zp-primary);
}
.zp-badge.success { background: #D1FAE5; color: #065F46; }
.zp-badge.danger  { background: #FEE2E2; color: #991B1B; }
.zp-badge.warning { background: #FEF3C7; color: #92400E; }
.zp-badge.neutral { background: #F3F4F6; color: #374151; }

/* Progress bar */
.zp-progress {
  width: 100%; height: 8px;
  background: var(--zp-border);
  border-radius: 999px; overflow: hidden;
}
.zp-progress > div {
  height: 100%;
  background: linear-gradient(90deg, var(--zp-primary), #6366F1);
  transition: width .4s ease;
}
.zp-progress.success > div { background: linear-gradient(90deg, var(--zp-success), #22C55E); }
.zp-progress.danger  > div { background: linear-gradient(90deg, var(--zp-danger), #F87171); }

/* Hero pass/fail banner */
.zp-hero-pass, .zp-hero-fail {
  padding: 2rem; border-radius: var(--zp-radius);
  color: white; text-align: center;
  box-shadow: var(--zp-shadow);
}
.zp-hero-pass { background: linear-gradient(135deg, #059669, #16A34A); }
.zp-hero-fail { background: linear-gradient(135deg, #B91C1C, #DC2626); }
.zp-hero-icon { font-size: 3rem; margin-bottom: .5rem; }
.zp-hero-title { font-size: 2rem; font-weight: 800; letter-spacing: -.02em; }
.zp-hero-sub { font-size: 1rem; opacity: .9; margin-top: .25rem; }

/* Zoom hint overlay on image */
.zp-image-wrap {
  position: relative; cursor: zoom-in;
  display: inline-block; border-radius: var(--zp-radius-sm); overflow: hidden;
  background: var(--zp-neutral-100, #F3F4F6);
  padding: .75rem;
}
.zp-image-wrap .zp-zoom-hint {
  position: absolute; top: 8px; right: 8px;
  background: rgba(0,0,0,.6); color: white;
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; opacity: 0; transition: opacity .2s ease;
  pointer-events: none;
}
.zp-image-wrap:hover .zp-zoom-hint { opacity: 1; }

/* GitHub-style CSS grid heatmap */
.zp-hm { width: 100%; display: block; box-sizing: border-box; }
.zp-hm-months {
  display: grid;
  grid-template-columns: 20px 1fr;
  padding-left: 20px;
  margin-bottom: 4px;
  font-size: .7rem;
  color: var(--zp-text-soft);
}
.zp-hm-months > :first-child { display: none; }
.zp-hm-months {
  display: grid;
  font-size: .7rem;
  color: var(--zp-text-soft);
  margin-bottom: 4px;
}
.zp-hm-month { text-align: left; padding-left: 2px; }
.zp-hm-body {
  display: grid;
  grid-auto-rows: 14px;
  gap: 3px;
  width: 100%;
  max-width: 900px;
}
@media (max-width: 600px) { .zp-hm-body { grid-auto-rows: 10px; gap: 2px; } }
.zp-hm-day {
  font-size: .65rem;
  color: var(--zp-text-soft);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 4px;
}
.zp-hm-cell {
  border-radius: 3px;
  background: #ebedf0;
  width: 100%;
  height: 100%;
}
.zp-hm-l0 { background: #ebedf0; }
.zp-hm-l1 { background: #9be9a8; }
.zp-hm-l2 { background: #40c463; }
.zp-hm-l3 { background: #30a14e; }
.zp-hm-l4 { background: #216e39; }

/* Dark mode heatmap */
body.body--dark .zp-hm-cell { background: #1f2937; }
body.body--dark .zp-hm-l0 { background: #1f2937; }
body.body--dark .zp-hm-l1 { background: #0e4429; }
body.body--dark .zp-hm-l2 { background: #006d32; }
body.body--dark .zp-hm-l3 { background: #26a641; }
body.body--dark .zp-hm-l4 { background: #39d353; }

/* Heatmap legend */
.zp-hm-legend {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  font-size: .7rem;
  color: var(--zp-text-soft);
  margin-top: 6px;
}
.zp-hm-legend .zp-hm-cell {
  width: 12px; height: 12px; aspect-ratio: unset;
  min-width: 12px; min-height: 12px;
}

/* Timer badge */
.zp-timer {
  display: inline-flex; align-items: center; gap: .35rem;
  padding: .4rem .75rem;
  background: var(--zp-primary); color: white;
  border-radius: 999px; font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.zp-timer.warning { background: var(--zp-warning); }
.zp-timer.danger { background: var(--zp-danger); animation: pulse 1s infinite; }
@keyframes pulse { 50% { opacity: .65; } }

/* Sidebar */
.zp-nav-link {
  display: flex; align-items: center; gap: .7rem;
  padding: .6rem .85rem; border-radius: 8px;
  color: var(--zp-text); text-decoration: none !important;
  font-size: .93rem;
  transition: background .12s ease;
}
.zp-nav-link:hover { background: var(--zp-primary-soft); color: var(--zp-primary); }
.zp-nav-link.active { background: var(--zp-primary); color: white; font-weight: 600; }
.zp-nav-icon { width: 20px; text-align: center; }

/* Page container — flex column with children stretching to full width */
.zp-container {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
.zp-container > * { width: 100%; max-width: 100%; }
.zp-container-narrow {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
.zp-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
.zp-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.zp-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
@media (max-width: 900px) { .zp-grid-4 { grid-template-columns: repeat(2, 1fr); } .zp-grid-3 { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) {
  .zp-grid-4, .zp-grid-3, .zp-grid-2 { grid-template-columns: 1fr; }
  .zp-container, .zp-container-narrow { padding: 1rem .75rem; }
  .zp-display { font-size: 1.5rem; }
  .zp-h1 { font-size: 1.3rem; }
  .zp-h2 { font-size: 1.1rem; }
  .zp-hero { padding: 1.25rem; }
  .zp-hero-title { font-size: 1.4rem; }
  .zp-card { padding: 1rem; }
  .zp-tile { min-height: 100px; padding: 1rem; }
  .zp-tile-title { font-size: .95rem; }
  .q-header { padding: .25rem .5rem !important; }
  .zp-header-title { font-size: 1rem !important; }
  .zp-header-sub { font-size: .65rem !important; }
  /* Compact tile icon bubble on mobile */
  .zp-tile .tile-icon-bubble { width: 36px !important; height: 36px !important; }

  /* Hero banner — title + CTA nad sebou misto vedle sebe */
  .zp-hero .zp-row-between {
    flex-wrap: wrap !important;
    white-space: normal !important;
  }
  .zp-hero .zp-row-between > * { width: 100%; }
  .zp-hero .q-btn { margin-top: .75rem; }

  /* Mobile: zrusit nowrap u obecnych rows, dovolit zalomit text */
  .zp-mobile-wrap .zp-nowrap,
  .zp-mobile-wrap .zp-row-between { flex-wrap: wrap !important; }

  /* Long mono text lines (DB path, ids) must break */
  .zp-mono { word-break: break-all; }

  /* Stat card: prevent child overflow */
  .zp-card { overflow-wrap: break-word; word-wrap: break-word; }

  /* kv rows (settings) — stack label + value */
  .zp-kv-row { flex-direction: column !important; align-items: flex-start !important; }
  .zp-kv-row > :first-child { width: auto !important; margin-bottom: .15rem; }

  /* Exam setup: row with 2 inputs → stack */
  .zp-exam-inputs { flex-direction: column !important; }
  .zp-exam-inputs > * { width: 100% !important; }

  /* Hero buttons: icon + text sharable on mobile */
  .zp-hero .q-btn { width: 100%; }
}

/* Global safeguards — prevent horizontal overflow everywhere */
body, html { overflow-x: hidden; max-width: 100vw; }
.q-page-container, .q-page { max-width: 100%; }
.zp-container, .zp-container-narrow, .zp-card, .zp-tile, .zp-hero {
  max-width: 100%; min-width: 0;
}
/* Flex children must be allowed to shrink below content width */
.zp-flex-1 { min-width: 0; }

/* Rating bar (SRS) */
.zp-rate-bar { display: flex; gap: .5rem; flex-wrap: wrap; justify-content: center; padding: .5rem 0; }
.zp-rate-btn {
  flex: 1 1 140px !important;
  min-width: 140px !important;
  min-height: 100px !important;
  padding: .75rem !important;
  border-radius: 10px !important;
  border: 1.5px solid var(--zp-border) !important;
  background: var(--zp-surface) !important;
  color: var(--zp-text) !important;
  font-weight: 600 !important;
  transition: all .15s ease;
}
.zp-rate-btn .q-btn__content {
  flex-direction: column !important;
  gap: 3px !important;
}
.zp-rate-label { font-weight: 700; font-size: .95rem; }
.zp-rate-hint { font-weight: 400; font-size: .7rem; opacity: .75; }
.zp-rate-btn:hover { transform: translateY(-1px); }
.zp-rate-btn.again { border-color: #FCA5A5 !important; color: #B91C1C !important; }
.zp-rate-btn.hard  { border-color: #FCD34D !important; color: #92400E !important; }
.zp-rate-btn.good  { border-color: #93C5FD !important; color: #1E40AF !important; }
.zp-rate-btn.easy  { border-color: #86EFAC !important; color: #065F46 !important; }
.zp-rate-btn.again:hover { background: #FEF2F2 !important; }
.zp-rate-btn.hard:hover  { background: #FFFBEB !important; }
.zp-rate-btn.good:hover  { background: #EFF6FF !important; }
.zp-rate-btn.easy:hover  { background: #F0FDF4 !important; }

/* kbd hint chip */
.zp-kbd {
  display: inline-block; padding: 1px 6px; margin-left: 4px;
  font-family: ui-monospace, monospace; font-size: .7rem;
  background: var(--zp-neutral-200, #E5E7EB); color: var(--zp-text-soft);
  border-radius: 4px; border: 1px solid var(--zp-border);
}

/* Empty state */
.zp-empty { text-align: center; padding: 3rem 1rem; }
.zp-empty-icon { font-size: 3rem; opacity: .4; margin-bottom: .5rem; }

/* Utility spacing & layout */
.zp-mt-xs { margin-top: .25rem; }
.zp-mt-sm { margin-top: .5rem; }
.zp-mt-md { margin-top: 1rem; }
.zp-mt-lg { margin-top: 1.5rem; }
.zp-mt-xl { margin-top: 2rem; }
.zp-mb-sm { margin-bottom: .5rem; }
.zp-mb-md { margin-bottom: 1rem; }
.zp-mb-lg { margin-bottom: 1.5rem; }
.zp-gap-xs { gap: .25rem; }
.zp-gap-sm { gap: .5rem; }
.zp-gap-md { gap: 1rem; }
.zp-gap-lg { gap: 1.5rem; }
.zp-flex-1 { flex: 1; }
.zp-row { display: flex; align-items: center; }
.zp-row-between { display: flex; align-items: center; justify-content: space-between; }
.zp-col { display: flex; flex-direction: column; }
.zp-nowrap { flex-wrap: nowrap; white-space: nowrap; }
.zp-prose { max-width: 62ch; }

/* Accent borders for stat cards */
.zp-accent-primary { border-left: 4px solid var(--zp-primary); }
.zp-accent-success { border-left: 4px solid var(--zp-success); }
.zp-accent-danger  { border-left: 4px solid var(--zp-danger); }
.zp-accent-warning { border-left: 4px solid var(--zp-warning); }

/* Hero gradient banner (shared between dashboard CTA / marathon done / exam result) */
.zp-hero {
  padding: 2rem;
  border-radius: var(--zp-radius);
  color: white;
  box-shadow: var(--zp-shadow);
}
.zp-hero-primary { background: linear-gradient(135deg, #1E40AF 0%, #312E81 100%); }
.zp-hero-success { background: linear-gradient(135deg, #059669, #16A34A); text-align: center; }
.zp-hero-danger  { background: linear-gradient(135deg, #B91C1C, #DC2626); text-align: center; }

/* Empty state container */
.zp-empty-container {
  text-align: center; padding: 3rem 1rem;
}
.zp-empty-container .zp-empty-icon-wrap {
  display: inline-flex;
  width: 64px; height: 64px;
  align-items: center; justify-content: center;
  border-radius: 50%;
  background: var(--zp-primary-soft);
  color: var(--zp-primary);
  margin-bottom: 1rem;
}

/* Page header */
.zp-page-header { margin-bottom: 1.25rem; }
.zp-page-header .zp-eyebrow {
  display: inline-flex; align-items: center; gap: .35rem;
  color: var(--zp-primary); font-weight: 600;
  font-size: .75rem; letter-spacing: .08em; text-transform: uppercase;
  margin-bottom: .25rem;
}

/* Quasar overrides — header musi prebit default tmavy styl */
.q-header {
  box-shadow: 0 1px 0 rgba(0,0,0,.06) !important;
  background: var(--zp-surface) !important;
  color: var(--zp-text) !important;
  min-height: 56px !important;
}
.q-header .q-btn {
  min-width: 40px !important;
  min-height: 40px !important;
  padding: 8px !important;
}
.q-header .q-btn .q-btn__content {
  width: 100%;
  height: 100%;
}
.q-header .q-btn:before {
  /* Quasar default hit area — rozsirit pro lepsi klikatelnost */
  inset: -4px !important;
}

/* Hamburger menu — vetsi hit area na mobile */
.zp-hamburger {
  min-width: 44px !important;
  min-height: 44px !important;
}
.zp-hamburger .q-icon {
  font-size: 28px !important;
}

/* Hide app subtitle when header cramped (mobile) */
@media (max-width: 400px) {
  .zp-header-sub { display: none !important; }
  .zp-brand .q-icon { display: none; } /* brand icon hidden, save space */
}
.zp-header-title {
  font-size: 1.15rem !important;
  font-weight: 700 !important;
  line-height: 1.2 !important;
  color: #111827 !important;
  margin: 0 !important;
}
.zp-header-sub {
  font-size: 0.72rem !important;
  line-height: 1.2 !important;
  color: #6B7280 !important;
  margin: 0 !important;
  letter-spacing: .02em;
}
.q-header .q-btn { color: var(--zp-primary) !important; }

/* Drawer default */
.q-drawer { background: var(--zp-surface) !important; }

/* Dark mode header text */
body.body--dark .zp-header-title { color: #F9FAFB !important; }
body.body--dark .zp-header-sub { color: #9CA3AF !important; }

/* Dark mode overrides for NiceGUI/Quasar */
.dark body, body.body--dark, body.dark { background: var(--zp-bg) !important; color: var(--zp-text) !important; }

/* Header */
body.body--dark .q-header {
  background: #111827 !important;
  border-bottom: 1px solid #374151 !important;
  color: #F9FAFB !important;
}
body.body--dark .q-header .zp-h2,
body.body--dark .q-header .zp-caption,
body.body--dark .q-header .q-btn,
body.body--dark .q-header .q-icon { color: #F9FAFB !important; }

/* Drawer */
body.body--dark .q-drawer {
  background: #111827 !important;
  border-right: 1px solid #374151 !important;
}
body.body--dark .zp-nav-link { color: #E5E7EB !important; }
body.body--dark .zp-nav-link .q-icon { color: #E5E7EB !important; }
body.body--dark .zp-nav-link:hover {
  background: #1E3A8A !important;
  color: #DBEAFE !important;
}
body.body--dark .zp-nav-link.active {
  background: var(--zp-primary) !important;
  color: white !important;
}

/* Cards & tiles */
body.body--dark .zp-card,
body.body--dark .zp-tile,
body.body--dark .zp-stat { background: #1F2937 !important; border-color: #374151 !important; color: var(--zp-text); }
body.body--dark .zp-card .zp-h1,
body.body--dark .zp-card .zp-h2,
body.body--dark .zp-card .zp-h3,
body.body--dark .zp-card .zp-metric,
body.body--dark .zp-card .zp-metric-sm,
body.body--dark .zp-card .zp-body,
body.body--dark .zp-display { color: #F9FAFB !important; }
body.body--dark .zp-card .zp-body-sm,
body.body--dark .zp-card .zp-caption { color: #9CA3AF !important; }
body.body--dark .zp-tile .zp-tile-title { color: #F9FAFB !important; }
body.body--dark .zp-tile .zp-body-sm { color: #9CA3AF !important; }
body.body--dark .zp-tile.primary { background: linear-gradient(135deg, #1E40AF 0%, #312E81 100%) !important; color: white !important; }
body.body--dark .zp-tile.primary .zp-tile-title { color: white !important; }
body.body--dark .zp-tile.primary .zp-body-sm { color: rgba(255,255,255,0.85) !important; }

/* Progress + misc */
body.body--dark .zp-progress { background: #374151 !important; }
body.body--dark .zp-kbd { background: #374151 !important; color: #E5E7EB !important; border-color: #4B5563 !important; }
body.body--dark .zp-rate-btn { background: #1F2937 !important; color: #F9FAFB !important; border-color: #374151 !important; }
body.body--dark .zp-badge.neutral { background: #374151 !important; color: #E5E7EB !important; }

/* Help dialog */
body.body--dark .q-dialog .q-card { background: #1F2937 !important; color: #F9FAFB !important; }

/* Inputs */
body.body--dark .q-field__native,
body.body--dark .q-field__input,
body.body--dark input { color: #F9FAFB !important; }
body.body--dark .q-field__label { color: #9CA3AF !important; }
body.body--dark .q-field__control { background: #1F2937 !important; }

/* Plotly charts — transparent bg in dark mode */
body.body--dark .js-plotly-plot .main-svg { background: transparent !important; }
body.body--dark .js-plotly-plot .bg { fill: transparent !important; }
body.body--dark .js-plotly-plot text { fill: #9CA3AF !important; }
body.body--dark .zp-heatmap-legend { color: #9CA3AF !important; }
body.body--dark .zp-heatmap-legend .sq:first-of-type { background: #374151 !important; }

/* Checkboxes in dark */
body.body--dark .q-checkbox__label { color: #E5E7EB !important; }
.dark .q-header, body.body--dark .q-header, body.dark .q-header {
  background: #1F2937 !important;
  border-bottom: 1px solid #374151 !important;
}
.dark .q-drawer, body.body--dark .q-drawer, body.dark .q-drawer {
  background: #1F2937 !important;
  border-right: 1px solid #374151 !important;
}
.dark .zp-nav-link:hover, body.body--dark .zp-nav-link:hover, body.dark .zp-nav-link:hover {
  background: #1E3A8A !important;
  color: #DBEAFE !important;
}
.dark input, body.body--dark input, body.dark input { color: var(--zp-text) !important; }
"""


def apply_theme():
    """Pridej globalni CSS + nastav primary color palette."""
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")
    ui.colors(
        primary=COLORS["primary"],
        secondary="#6366F1",
        accent=COLORS["accent"],
        positive=COLORS["success"],
        negative=COLORS["danger"],
        warning=COLORS["warning"],
        info=COLORS["info"],
    )
