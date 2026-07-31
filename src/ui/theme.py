"""Design system — tokeny, vrstvy, komponenty.

Tři pravidla, na kterých to stojí:

1. **Tmavý režim předefinuje jen tokeny.** Žádné `body--dark .zp-neco { … }`
   po komponentách. Když komponenta potřebuje v tmavém režimu jinou barvu,
   je to znamení, že jí chybí token — ne že se má přidat výjimka.
2. **Mobile first.** Všechny `@media` jsou `min-width`. Základní pravidlo
   platí na telefonu, breakpoint jen přidává.
3. **Vrstvy místo `!important`.** Vlastní CSS je v `@layer`, kde si pořadí
   řídíme sami. Jediná neuvrstvená sekce je na konci — přebíjení Quasaru.
   (Neuvrstvené CSS má přednost před uvrstveným, takže Quasar se dá porazit
   pořadím v souboru, ne silou.)

CSS se vkládá `shared=True`, takže je v hlavičce jednou pro celou aplikaci.
Dřív se přidávalo přes `add_head_html` v `apply_theme()` při každém sestavení
stránky, tedy do každé odpovědi znovu.
"""
from __future__ import annotations

from nicegui import ui

# Paleta pro `ui.colors()` — Quasar si drží vlastní proměnné, tohle je most.
# Primární barva je petrolejová, ne indigová: tmavá modř #1E40AF působila
# na světlém i tmavém podkladu těžce a v tmavém režimu byla špatně čitelná.
COLORS = {
    "primary": "#10627A",
    "primary_soft": "#DCEEF4",
    "accent": "#F59E0B",
    "success": "#16A34A",
    "danger": "#DC2626",
    "warning": "#F59E0B",
    "info": "#0EA5E9",
}


# ---------------------------------------------------------------------------
# 1. TOKENY
# ---------------------------------------------------------------------------
TOKENS = """
@layer zp.tokens {
  :root {
    color-scheme: light;

    /* --- barvy: role, ne odstíny --- */
    --zp-primary: #10627A;
    --zp-primary-hover: #0C5163;
    --zp-primary-soft: #DCEEF4;
    --zp-primary-line: #92C7D8;
    --zp-on-primary: #FFFFFF;

    --zp-accent: #B45309;
    --zp-accent-soft: #FDF0D5;

    --zp-text: #10151C;
    --zp-text-soft: #5A6473;
    --zp-text-faint: #8A94A3;

    --zp-surface: #FFFFFF;
    --zp-surface-sunk: #F2F5F9;
    --zp-surface-raised: #FFFFFF;
    --zp-bg: #F6F8FB;

    --zp-border: #E1E6ED;
    --zp-border-strong: #C8D0DA;

    /* Stavy. Tohle je ten rozdíl — komponenty sahají sem, ne na hex. */
    --zp-ok-bg: #E9F9F0;
    --zp-ok-fg: #10502F;
    --zp-ok-line: #34A56F;
    --zp-bad-bg: #FDECEC;
    --zp-bad-fg: #7A1A1A;
    --zp-bad-line: #E06060;
    --zp-warn-bg: #FDF4E3;
    --zp-warn-fg: #7A4A08;
    --zp-warn-line: #E0A83C;
    --zp-neutral-bg: #EEF1F5;
    --zp-neutral-fg: #414A57;

    /* Heatmapa — vlastní stupnice, ať v tmavém režimu nezmizí */
    --zp-hm-0: #E4E9EF;
    --zp-hm-1: #A9DCC0;
    --zp-hm-2: #59BC85;
    --zp-hm-3: #2E8E5B;
    --zp-hm-4: #1B5E3B;

    /* --- prostor: 8px mřížka (sp-1 je půlkrok) --- */
    --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px;
    --sp-5: 24px; --sp-6: 32px; --sp-7: 48px; --sp-8: 64px;

    /* --- typografie: role, ne velikosti --- */
    --fs-display: clamp(1.5rem, 1.15rem + 1.7vw, 2rem);
    --fs-h1: clamp(1.25rem, 1.05rem + 1vw, 1.6rem);
    --fs-h2: clamp(1.05rem, .98rem + .4vw, 1.2rem);
    --fs-h3: 1rem;
    --fs-question: clamp(1.05rem, .98rem + .55vw, 1.22rem);
    --fs-body: 1rem;
    --fs-opt: clamp(.94rem, .9rem + .2vw, 1rem);
    --fs-sm: .875rem;
    --fs-xs: .75rem;
    --fs-metric: clamp(1.6rem, 1.3rem + 1.2vw, 2rem);

    --lh-tight: 1.22;
    --lh-snug: 1.4;
    --lh-body: 1.55;

    --ff-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;

    /* --- tvar --- */
    --zp-radius: 12px;
    --zp-radius-sm: 8px;
    --zp-radius-xs: 6px;
    --zp-radius-pill: 999px;

    --zp-shadow-sm: 0 1px 2px rgba(16, 21, 28, .05);
    --zp-shadow: 0 4px 14px rgba(16, 21, 28, .07);
    --zp-shadow-lg: 0 18px 38px rgba(16, 21, 28, .12);

    /* --- pohyb --- */
    --zp-ease: cubic-bezier(.22, .61, .36, 1);
    --zp-dur-fast: 120ms;
    --zp-dur: 180ms;

    --zp-ring: 0 0 0 3px var(--zp-primary-line);
    --zp-tap: 44px;   /* minimální cíl pro palec */
  }

  /* Tmavý režim — JEN předefinování tokenů. Sem se nepřidávají komponenty. */
  body.body--dark, body.dark, .dark, [data-theme="dark"] {
    color-scheme: dark;

    --zp-primary: #6FC7DC;
    --zp-primary-hover: #8AD5E7;
    --zp-primary-soft: #10323E;
    --zp-primary-line: #2E6E84;
    --zp-on-primary: #05191F;

    --zp-accent: #F0B357;
    --zp-accent-soft: #33270F;

    --zp-text: #E9ECF2;
    --zp-text-soft: #9AA4B4;
    --zp-text-faint: #6E7889;

    --zp-surface: #171C24;
    --zp-surface-sunk: #10141B;
    --zp-surface-raised: #1D232D;
    --zp-bg: #0C1015;

    --zp-border: #2A3240;
    --zp-border-strong: #3C475A;

    --zp-ok-bg: #0F3626;
    --zp-ok-fg: #A8EFC8;
    --zp-ok-line: #3FA877;
    --zp-bad-bg: #3B1618;
    --zp-bad-fg: #FBC6C6;
    --zp-bad-line: #C9585B;
    --zp-warn-bg: #35280F;
    --zp-warn-fg: #F5D69B;
    --zp-warn-line: #B98A2E;
    --zp-neutral-bg: #242C38;
    --zp-neutral-fg: #C4CBD6;

    --zp-hm-0: #1A2029;
    --zp-hm-1: #10432C;
    --zp-hm-2: #17714A;
    --zp-hm-3: #2FA36A;
    --zp-hm-4: #56D191;

    --zp-shadow-sm: 0 1px 2px rgba(0, 0, 0, .4);
    --zp-shadow: 0 4px 14px rgba(0, 0, 0, .45);
    --zp-shadow-lg: 0 18px 38px rgba(0, 0, 0, .55);
  }
}
"""


# ---------------------------------------------------------------------------
# 2. ZÁKLAD
# ---------------------------------------------------------------------------
BASE = """
@layer zp.base {
  *, *::before, *::after { box-sizing: border-box; }

  /* Klávesnicové zaměření musí být vidět všude. Dřív nebylo nikde. */
  :focus-visible {
    outline: 2px solid var(--zp-primary);
    outline-offset: 2px;
    border-radius: var(--zp-radius-xs);
  }
  :focus:not(:focus-visible) { outline: none; }

  ::selection { background: var(--zp-primary-soft); color: var(--zp-text); }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: .01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: .01ms !important;
      scroll-behavior: auto !important;
    }
  }

  /* Typografie — role, ne velikosti */
  .zp-display {
    font-size: var(--fs-display); font-weight: 700; line-height: var(--lh-tight);
    letter-spacing: -.02em; color: var(--zp-text); text-wrap: balance;
  }
  .zp-h1 { font-size: var(--fs-h1); font-weight: 700; line-height: var(--lh-tight); letter-spacing: -.015em; color: var(--zp-text); text-wrap: balance; }
  .zp-h2 { font-size: var(--fs-h2); font-weight: 600; line-height: var(--lh-snug); color: var(--zp-text); text-wrap: balance; }
  .zp-h3 { font-size: var(--fs-h3); font-weight: 600; line-height: var(--lh-snug); color: var(--zp-text); }
  .zp-body { font-size: var(--fs-body); line-height: var(--lh-body); color: var(--zp-text); text-wrap: pretty; }
  .zp-body-sm { font-size: var(--fs-sm); line-height: 1.5; color: var(--zp-text-soft); }
  .zp-caption { font-size: var(--fs-xs); line-height: 1.4; color: var(--zp-text-soft); letter-spacing: .02em; }
  .zp-metric { font-size: var(--fs-metric); font-weight: 700; line-height: 1; letter-spacing: -.02em; color: var(--zp-text); font-variant-numeric: tabular-nums; }
  .zp-metric-sm { font-size: 1.25rem; font-weight: 600; color: var(--zp-text); font-variant-numeric: tabular-nums; }
  .zp-mono { font-family: var(--ff-mono); font-variant-numeric: tabular-nums; }

  /* Text otázky má vlastní roli — je to nejdůležitější text v aplikaci
     a dřív sdílel .zp-h2 s nadpisy sekcí. */
  .zp-question {
    font-size: var(--fs-question); font-weight: 650; line-height: var(--lh-snug);
    color: var(--zp-text); text-wrap: pretty; margin: 0;
  }

}
"""


# ---------------------------------------------------------------------------
# 3. ROZVRŽENÍ
# ---------------------------------------------------------------------------
LAYOUT = """
@layer zp.layout {
  .zp-container, .zp-container-narrow {
    width: 100%; margin-inline: auto;
    padding: var(--sp-4) var(--sp-3) calc(var(--sp-8) + env(safe-area-inset-bottom));
    display: flex; flex-direction: column; align-items: stretch; gap: 0;
  }
  .zp-container { max-width: 960px; }
  .zp-container-narrow { max-width: 720px; }
  .zp-container > *, .zp-container-narrow > * { width: 100%; max-width: 100%; min-width: 0; }
  /* Musí stát AŽ ZA pravidlem výše — to nastavuje potomkům max-width: 100%
     a dřív tím rušilo omezení délky řádku. Souvislý text přes 1400 px
     se čte špatně. */
  .zp-prose { max-width: 62ch; }

  @media (min-width: 600px) {
    .zp-container, .zp-container-narrow { padding: var(--sp-5) var(--sp-5) var(--sp-8); }
  }

  /* Kvízový obal. `container-type` zapíná container queries — karta se řídí
     šířkou svého místa, ne oknem. Vedle navigátoru má 520 px i na 1400px
     monitoru a musí se chovat jako na mobilu. */
  .zp-quiz-wrap {
    width: 100%; max-width: 720px; margin-inline: auto;
    display: flex; flex-direction: column; gap: var(--sp-3);
    container-type: inline-size; container-name: quiz;
  }

  /* Hlavička nad kvízem musí mít stejnou šířku jako karta, jinak text
     a filtry začínají jinde než otázka. */
  .zp-quiz-head {
    width: 100%; max-width: 720px; margin-inline: auto;
    display: flex; flex-direction: column; gap: var(--sp-3);
  }

  .zp-quiz-with-nav { display: flex; flex-direction: column; gap: var(--sp-4); width: 100%; }
  .zp-quiz-with-nav > .zp-quiz-main { flex: 1; min-width: 0; width: 100%; }

  @media (min-width: 1100px) {
    /* Stránka s navigátorem zahazuje vystředěný obal — panel má sedět na
       levém okraji okna, ne uvnitř sloupce širokého 960 px. */
    .zp-container:has(.zp-quiz-with-nav) {
      max-width: none; padding: 0;
    }
    /* Nadpis a filtry nad navigátorem ale nesmí být nalepené na okraj okna —
       odsazení, které si obal zahodil, se jim vrátí zvlášť. */
    .zp-container:has(.zp-quiz-with-nav) > *:not(.zp-quiz-with-nav) {
      padding-inline: var(--sp-5);
    }
    .zp-container:has(.zp-quiz-with-nav) > *:first-child { margin-top: var(--sp-5); }
    .zp-quiz-with-nav { flex-direction: row; align-items: stretch; gap: 0; }
    .zp-quiz-with-nav > .zp-quiz-main { padding: var(--sp-5); }
  }

  .zp-grid-2, .zp-grid-3, .zp-grid-4 { display: grid; grid-template-columns: 1fr; gap: var(--sp-3); }
  @media (min-width: 600px) {
    .zp-grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .zp-grid-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .zp-grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  }
  @media (min-width: 900px) {
    .zp-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .zp-grid-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  }

  .zp-row { display: flex; align-items: center; }
  .zp-row-between { display: flex; align-items: center; justify-content: space-between; }
  .zp-col { display: flex; flex-direction: column; }
  .zp-nowrap { flex-wrap: nowrap; white-space: nowrap; }
  .zp-flex-1 { flex: 1; min-width: 0; }
}
"""


# ---------------------------------------------------------------------------
# 4. KOMPONENTY
# ---------------------------------------------------------------------------
COMPONENTS = """
@layer zp.components {

  /* ---- karta ---- */
  .zp-card {
    background: var(--zp-surface);
    border: 1px solid var(--zp-border);
    border-radius: var(--zp-radius);
    box-shadow: var(--zp-shadow-sm);
    padding: var(--sp-4);
    color: var(--zp-text);
    overflow-wrap: break-word; min-width: 0;
    transition: box-shadow var(--zp-dur) var(--zp-ease),
                transform var(--zp-dur-fast) var(--zp-ease),
                border-color var(--zp-dur) var(--zp-ease);
  }
  @media (min-width: 600px) { .zp-card { padding: var(--sp-5); } }
  .zp-card.clickable { cursor: pointer; }
  .zp-card.clickable:hover { box-shadow: var(--zp-shadow); transform: translateY(-2px); border-color: var(--zp-primary); }

  .zp-accent-primary { border-left: 4px solid var(--zp-primary); }
  .zp-accent-success { border-left: 4px solid var(--zp-ok-line); }
  .zp-accent-danger  { border-left: 4px solid var(--zp-bad-line); }
  .zp-accent-warning { border-left: 4px solid var(--zp-warn-line); }

  /* ---- dlaždice režimů ---- */
  .zp-tile {
    background: var(--zp-surface);
    border: 1px solid var(--zp-border);
    border-radius: var(--zp-radius);
    padding: var(--sp-4);
    cursor: pointer; position: relative; overflow: hidden;
    display: flex; flex-direction: column; gap: var(--sp-1);
    min-height: 96px; color: var(--zp-text);
    transition: transform var(--zp-dur-fast) var(--zp-ease),
                box-shadow var(--zp-dur) var(--zp-ease),
                border-color var(--zp-dur) var(--zp-ease);
  }
  .zp-tile:hover { transform: translateY(-2px); box-shadow: var(--zp-shadow); border-color: var(--zp-primary); }
  .zp-tile .zp-tile-title { font-size: var(--fs-h3); font-weight: 600; color: var(--zp-text); }
  .zp-tile .zp-body-sm, .zp-tile .zp-caption { color: var(--zp-text-soft); }
  .zp-tile.primary {
    background: linear-gradient(135deg, #0F5F76 0%, #0A3F52 100%);
    color: #fff; border-color: transparent;
  }
  .zp-tile.primary .zp-tile-title { color: #fff; }
  .zp-tile.primary .zp-body-sm, .zp-tile.primary .zp-caption { color: rgba(255,255,255,.85); }
  .zp-tile-badge {
    position: absolute; top: var(--sp-2); right: var(--sp-2);
    background: var(--zp-accent-soft); color: var(--zp-accent);
    border: 1px solid var(--zp-warn-line);
    font-size: .7rem; font-weight: 700; padding: 2px 8px;
    border-radius: var(--zp-radius-pill); font-variant-numeric: tabular-nums;
  }
  .zp-tile.primary .zp-tile-badge { background: #F59E0B; color: #111827; border-color: transparent; }

  /* ---- možnosti odpovědi ---- */
  /* Písmeno má vlastní sloupec. Dřív bylo uvnitř textu, takže se druhý řádek
     zalomil pod badge — na mobilu se to nedalo číst. */
  .zp-opt {
    display: flex; align-items: flex-start; gap: var(--sp-3);
    width: 100%; text-align: left;
    background: var(--zp-surface); color: var(--zp-text);
    border: 1.5px solid var(--zp-border);
    border-radius: var(--zp-radius-sm);
    padding: var(--sp-3);
    margin: 0;
    font-size: var(--fs-opt); line-height: var(--lh-snug);
    font-weight: 400; font-family: inherit;
    text-transform: none; letter-spacing: normal;
    cursor: pointer; min-height: var(--zp-tap);
    transition: border-color var(--zp-dur-fast) var(--zp-ease),
                background var(--zp-dur-fast) var(--zp-ease);
  }
  @media (min-width: 600px) { .zp-opt { padding: var(--sp-3) var(--sp-4); } }

  .zp-opt > .opt-key {
    flex: none;
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px; border-radius: var(--zp-radius-xs);
    background: var(--zp-neutral-bg); color: var(--zp-neutral-fg);
    font-weight: 700; font-size: .8rem; font-variant-numeric: tabular-nums;
  }
  .zp-opt > .opt-text { flex: 1; min-width: 0; padding-top: 3px; text-wrap: pretty; }

  .zp-opt:hover { border-color: var(--zp-primary); background: var(--zp-primary-soft); }
  .zp-opt.selected {
    border-color: var(--zp-primary); border-width: 2px;
    background: var(--zp-primary-soft); font-weight: 600;
  }
  .zp-opt.selected > .opt-key { background: var(--zp-primary); color: var(--zp-on-primary); }

  /* Po vyhodnocení: správná se rozsvítí, ostatní jen zešednou obrys.
     Nic se netlumí — otázka musí zůstat čitelná. */
  .zp-opt.correct {
    border-color: var(--zp-ok-line); border-width: 2px;
    background: var(--zp-ok-bg); color: var(--zp-ok-fg); font-weight: 600;
  }
  .zp-opt.correct > .opt-key { background: var(--zp-ok-line); color: #fff; }
  .zp-opt.wrong {
    border-color: var(--zp-bad-line); border-width: 2px;
    background: var(--zp-bad-bg); color: var(--zp-bad-fg);
  }
  .zp-opt.wrong > .opt-key { background: var(--zp-bad-line); color: #fff; }
  .zp-opt.disabled { pointer-events: none; }
  .zp-opt.disabled:not(.correct):not(.wrong):not(.selected) { opacity: .85; }

  /* ---- štítky ---- */
  .zp-badge {
    display: inline-flex; align-items: center; gap: var(--sp-1);
    padding: 3px 10px; border-radius: var(--zp-radius-pill);
    font-size: .72rem; font-weight: 600; letter-spacing: .02em;
    background: var(--zp-primary-soft); color: var(--zp-primary);
    white-space: nowrap;
  }
  .zp-badge.success { background: var(--zp-ok-bg); color: var(--zp-ok-fg); }
  .zp-badge.danger  { background: var(--zp-bad-bg); color: var(--zp-bad-fg); }
  .zp-badge.warning { background: var(--zp-warn-bg); color: var(--zp-warn-fg); }
  .zp-badge.neutral { background: var(--zp-neutral-bg); color: var(--zp-neutral-fg); }

  /* ---- ukazatel postupu ---- */
  .zp-progress {
    width: 100%; height: 6px; background: var(--zp-neutral-bg);
    border-radius: var(--zp-radius-pill); overflow: hidden;
  }
  .zp-progress > div {
    height: 100%; background: var(--zp-primary);
    border-radius: var(--zp-radius-pill);
    transition: width .4s var(--zp-ease);
  }
  .zp-progress.success > div { background: var(--zp-ok-line); }
  .zp-progress.danger  > div { background: var(--zp-bad-line); }

  /* ---- měřidlo s hranicí (Mastery) ---- */
  /* Procento bez měřítka nic neříká — hranice 90 % je proto na pruhu vidět. */
  .zp-meter { position: relative; height: 10px; background: var(--zp-neutral-bg); border-radius: var(--zp-radius-pill); margin-top: 18px; }
  .zp-meter-fill { position: absolute; top: 0; bottom: 0; left: 0; border-radius: var(--zp-radius-pill); background: var(--zp-primary); transition: width .4s var(--zp-ease); }
  .zp-meter-fill.ok { background: var(--zp-ok-line); }
  .zp-meter-fill.low { background: var(--zp-bad-line); }
  /* Šrafování = málo dat. Poctivější než číslo uměle stlačit dolů. */
  .zp-meter-fill.sparse {
    background-image: repeating-linear-gradient(45deg,
      rgba(255,255,255,.55) 0 3px, transparent 3px 6px);
  }
  .zp-meter-mark { position: absolute; top: -4px; bottom: -4px; width: 2px; background: var(--zp-warn-line); border-radius: 1px; }
  .zp-meter-mark::after {
    content: attr(data-label); position: absolute; top: -15px; left: 50%;
    transform: translateX(-50%); font-size: .62rem; color: var(--zp-text-soft);
    white-space: nowrap; font-variant-numeric: tabular-nums;
  }

  /* ---- pokrytí oblasti (Mastery) ---- */
  /* Kolik různých otázek oblasti člověk vůbec viděl. Bez toho se nedá
     posoudit, jestli procento úspěšnosti stojí na celé oblasti, nebo
     na třiceti opakovaných otázkách. */
  .zp-cov { position: relative; height: 4px; margin-top: var(--sp-3);
    background: var(--zp-neutral-bg); border-radius: var(--zp-radius-pill); }
  .zp-cov-fill { position: absolute; top: 0; bottom: 0; left: 0;
    background: var(--zp-text-faint); border-radius: var(--zp-radius-pill);
    transition: width .4s var(--zp-ease); }
  .zp-cov-fill.ok { background: var(--zp-ok-line); }
  .zp-cov-label { font-size: var(--fs-xs); color: var(--zp-text-soft);
    margin-top: 5px; font-variant-numeric: tabular-nums; }
  .zp-cov-label b { color: var(--zp-text); font-weight: 600; }

  /* ---- odkaz na paragraf / chyták ---- */
  .zp-law-chip {
    border: 1px solid var(--zp-border-strong);
    border-radius: var(--zp-radius-pill);
    font-size: var(--fs-sm); font-weight: 600;
    white-space: nowrap; min-height: 36px;
  }
  .zp-law-chip:hover { border-color: var(--zp-primary); background: var(--zp-primary-soft); }

  .zp-law-ref {
    margin-top: var(--sp-3); padding: var(--sp-3) var(--sp-4);
    border-left: 3px solid var(--zp-primary);
    background: var(--zp-surface-sunk);
    border-radius: 0 var(--zp-radius) var(--zp-radius) 0;
  }
  .zp-law-ref-link { font-weight: 600; font-size: var(--fs-sm); color: var(--zp-primary); text-decoration: none; }
  .zp-law-ref-link:hover { text-decoration: underline; }
  .zp-law-ref-quote { font-size: var(--fs-body); line-height: 1.65; color: var(--zp-text); font-style: italic; text-wrap: pretty; }

  /* Slovo v zadání, které obrací smysl otázky. Ukáže se až po vyhodnocení. */
  .zp-stem-mark {
    background: var(--zp-warn-bg); color: var(--zp-warn-fg);
    box-shadow: inset 0 -2px 0 var(--zp-warn-line);
    padding: 0 2px; border-radius: 2px; font-weight: 800;
  }

  /* ---- rozbor chytáku ---- */
  .zp-trap-box {
    margin-top: var(--sp-3); padding: var(--sp-3) var(--sp-4);
    border-left: 3px solid var(--zp-warn-line);
    background: var(--zp-warn-bg);
    border-radius: 0 var(--zp-radius) var(--zp-radius) 0;
  }
  .zp-trap-title {
    font-size: var(--fs-xs); font-weight: 700; letter-spacing: .05em;
    text-transform: uppercase; color: var(--zp-warn-fg); margin-bottom: var(--sp-2);
  }
  .zp-trap-item { padding: var(--sp-1) 0; }
  .zp-trap-op { font-size: var(--fs-sm); color: var(--zp-text-soft); }
  .zp-trap-good { font-size: var(--fs-opt); font-weight: 600; color: var(--zp-ok-fg); }
  .zp-trap-stem { font-size: var(--fs-opt); font-weight: 700; color: var(--zp-warn-fg); }
  .zp-trap-bad {
    font-size: var(--fs-opt); font-weight: 600; color: var(--zp-bad-fg);
    text-decoration: line-through; text-decoration-thickness: 1px;
  }

  /* ---- navigátor otázek ---- */
  /* Mobile first: panel je vysunovací zásuvka mimo obrazovku. Teprve od
     1100 px se z něj stane připíchnutý sloupec vedle karty. */
  .zp-qnav {
    position: fixed; inset-block: 0; inset-inline-start: 0;
    z-index: 2100; width: min(88vw, 340px);
    padding: var(--sp-4) var(--sp-3);
    padding-top: max(var(--sp-4), env(safe-area-inset-top));
    border-right: 1px solid var(--zp-border);
    background: var(--zp-surface);
    box-shadow: var(--zp-shadow-lg);
    transform: translateX(-102%);
    transition: transform var(--zp-dur) var(--zp-ease);
    overflow-y: auto; overscroll-behavior: contain;
    display: flex; flex-direction: column;
  }
  .zp-qnav.open { transform: translateX(0); }

  .zp-qnav-backdrop {
    position: fixed; inset: 0; z-index: 2050;
    background: rgba(8, 12, 18, .5);
    opacity: 0; pointer-events: none;
    transition: opacity var(--zp-dur) var(--zp-ease);
  }
  .zp-qnav-backdrop.open { opacity: 1; pointer-events: auto; }

  .zp-qnav-toggle {
    align-self: flex-start; min-height: var(--zp-tap);
    border: 1px solid var(--zp-border); border-radius: var(--zp-radius-pill);
  }

  /* Od 1100 px je z panelu sloupec přisazený k levému okraji okna a vysoký
     přes celou stránku. Proto se stránka s navigátorem zbavuje svého
     vystředěného obalu — viz .zp-container:has() v sekci rozvržení. */
  @media (min-width: 1100px) {
    .zp-qnav {
      position: sticky; inset-block: auto; inset-inline-start: auto;
      top: 0; z-index: auto;
      width: 320px; flex-shrink: 0;
      height: calc(100dvh - 56px);
      padding: var(--sp-4) var(--sp-3);
      border: 0; border-right: 1px solid var(--zp-border); border-radius: 0;
      box-shadow: none; transform: none;
      background: var(--zp-surface);
    }
    .zp-qnav-list { max-height: none; flex: 1; margin-right: calc(var(--sp-2) * -1); padding-right: var(--sp-2); }
    .zp-qnav-toggle, .zp-qnav-close, .zp-qnav-backdrop { display: none; }
  }
  .zp-qnav-title { font-size: var(--fs-xs); font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--zp-text-soft); }
  .zp-qnav-filters { display: flex; flex-wrap: wrap; gap: 4px; margin-top: var(--sp-2); }
  .zp-qnav-filter {
    border: 1px solid var(--zp-border); border-radius: var(--zp-radius-pill);
    font-size: .72rem; min-height: 28px; padding: 0 10px;
  }
  .zp-qnav-filter.active {
    background: var(--zp-primary); color: var(--zp-on-primary);
    border-color: var(--zp-primary);
  }
  .zp-qnav-info { display: block; margin: var(--sp-1) 0 var(--sp-2); }
  .zp-qnav-list { max-height: min(56vh, 620px); overflow-y: auto; overscroll-behavior: contain; }

  .zp-qnav-item {
    display: flex; gap: var(--sp-3); align-items: baseline;
    padding: var(--sp-2) var(--sp-2) var(--sp-2) var(--sp-3);
    border-radius: var(--zp-radius-xs);
    cursor: pointer; min-height: 40px;
    position: relative;
    transition: background var(--zp-dur-fast) var(--zp-ease);
  }
  /* Stav je tenký proužek u levé hrany, ne rámeček — barevný okraj kolem
     každé položky dělá ze seznamu tapetu. */
  .zp-qnav-item::before {
    content: ""; position: absolute; left: 0; top: 6px; bottom: 6px;
    width: 3px; border-radius: 3px; background: transparent;
  }
  .zp-qnav-item:hover { background: var(--zp-surface-sunk); }
  .zp-qnav-num {
    font-family: var(--ff-mono); font-size: .7rem; font-weight: 600;
    color: var(--zp-text-faint); min-width: 2.4rem;
    font-variant-numeric: tabular-nums;
  }
  .zp-qnav-text {
    font-size: .8125rem; line-height: 1.4; color: var(--zp-text-soft);
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  }
  .zp-qnav-item.correct::before { background: var(--zp-ok-line); }
  .zp-qnav-item.wrong::before { background: var(--zp-bad-line); }

  /* Aktuální otázka: světlejší plocha, plný text a výrazný proužek.
     Dřív to byla tmavě modrá výplň, ve které text zanikal. */
  .zp-qnav-item.current {
    background: var(--zp-surface-sunk);
    box-shadow: inset 0 0 0 1px var(--zp-border);
  }
  .zp-qnav-item.current::before { background: var(--zp-primary); width: 4px; top: 0; bottom: 0; }
  .zp-qnav-item.current .zp-qnav-text { font-weight: 600; color: var(--zp-text); }
  .zp-qnav-item.current .zp-qnav-num { color: var(--zp-primary); }

  /* ---- hodnocení SRS ---- */
  .zp-rate-bar {
    display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--sp-2); width: 100%; max-width: 720px; margin-inline: auto;
    padding: var(--sp-2) 0;
  }
  @media (min-width: 600px) { .zp-rate-bar { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
  .zp-rate-btn {
    width: 100%; min-height: 76px; padding: var(--sp-3) var(--sp-2);
    border-radius: var(--zp-radius-sm);
    border: 1px solid var(--zp-border);
    border-top: 3px solid var(--zp-border-strong);
    background: var(--zp-surface); color: var(--zp-text);
    transition: transform var(--zp-dur-fast) var(--zp-ease),
                background var(--zp-dur-fast) var(--zp-ease);
  }
  .zp-rate-btn .q-btn__content { flex-direction: column; gap: 2px; }
  /* Klávesa je drobný nadpis nahoře, ne odznak dole — vede oko shora dolů:
     čím zmáčknout → co to znamená → kdy se otázka vrátí. */
  .zp-rate-key {
    display: block; font-family: var(--ff-mono); font-size: .62rem;
    font-weight: 700; letter-spacing: .1em; color: var(--zp-text-faint);
  }
  .zp-rate-label { display: block; font-weight: 700; font-size: var(--fs-body); color: var(--zp-text); }
  .zp-rate-hint {
    display: block; font-weight: 600; font-size: var(--fs-sm);
    font-variant-numeric: tabular-nums;
  }
  .zp-rate-btn:hover { transform: translateY(-1px); }
  .zp-rate-btn.again { border-top-color: var(--zp-bad-line); }
  .zp-rate-btn.hard  { border-top-color: var(--zp-warn-line); }
  .zp-rate-btn.good  { border-top-color: var(--zp-primary); }
  .zp-rate-btn.easy  { border-top-color: var(--zp-ok-line); }
  .zp-rate-btn.again .zp-rate-hint { color: var(--zp-bad-fg); }
  .zp-rate-btn.hard  .zp-rate-hint { color: var(--zp-warn-fg); }
  .zp-rate-btn.good  .zp-rate-hint { color: var(--zp-primary); }
  .zp-rate-btn.easy  .zp-rate-hint { color: var(--zp-ok-fg); }
  .zp-rate-btn.again:hover { background: var(--zp-bad-bg); }
  .zp-rate-btn.hard:hover  { background: var(--zp-warn-bg); }
  .zp-rate-btn.good:hover  { background: var(--zp-primary-soft); }
  .zp-rate-btn.easy:hover  { background: var(--zp-ok-bg); }

  /* ---- odpočet ---- */
  .zp-timer {
    display: inline-flex; align-items: center; gap: var(--sp-1);
    padding: var(--sp-1) var(--sp-3);
    background: var(--zp-primary); color: var(--zp-on-primary);
    border-radius: var(--zp-radius-pill); font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
  .zp-timer.warning { background: var(--zp-warn-line); color: #1A1206; }
  .zp-timer.danger { background: var(--zp-bad-line); color: #fff; animation: zp-pulse 1s infinite; }
  @keyframes zp-pulse { 50% { opacity: .6; } }

  /* ---- průběh zkoušky ---- */
  .zp-dots {
    display: flex; flex-wrap: wrap; gap: 5px;
    justify-content: center; margin-top: var(--sp-4);
    max-width: 720px; margin-inline: auto;
  }
  .zp-dot {
    width: 12px; height: 12px; border-radius: 3px;
    border: 1px solid var(--zp-border-strong); background: transparent;
  }
  .zp-dot.done { background: var(--zp-primary); border-color: var(--zp-primary); }
  .zp-dot.skipped { background: var(--zp-warn-line); border-color: var(--zp-warn-line); }
  .zp-dot.cur { border-color: var(--zp-text); border-width: 2px; background: transparent; }
  .zp-dots-legend {
    text-align: center; font-size: var(--fs-xs); color: var(--zp-text-soft);
    margin-top: var(--sp-2); font-variant-numeric: tabular-nums;
  }

  /* ---- výsledek zkoušky ---- */
  /* Střízlivěji než barevná plocha přes celou šířku — informace je skóre
     proti hranici, ne to, jak velká je ta plocha. */
  .zp-verdict {
    display: flex; flex-direction: column; align-items: center; gap: var(--sp-1);
    padding: var(--sp-5); border-radius: var(--zp-radius);
    border: 1px solid var(--zp-border); background: var(--zp-surface-sunk);
    border-top: 4px solid var(--zp-border-strong);
  }
  .zp-verdict.pass { border-top-color: var(--zp-ok-line); }
  .zp-verdict.fail { border-top-color: var(--zp-bad-line); }
  .zp-verdict-label {
    font-size: var(--fs-xs); font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: var(--zp-text-soft);
  }
  .zp-verdict.pass .zp-verdict-label { color: var(--zp-ok-fg); }
  .zp-verdict.fail .zp-verdict-label { color: var(--zp-bad-fg); }
  .zp-verdict-score {
    font-size: clamp(2rem, 1.5rem + 2.4vw, 3rem); font-weight: 800;
    letter-spacing: -.03em; line-height: 1; color: var(--zp-text);
    font-variant-numeric: tabular-nums;
  }
  .zp-verdict-sub { font-size: var(--fs-sm); color: var(--zp-text-soft); text-align: center; }

  /* ---- boční menu ---- */
  .zp-nav-group { font-size: .68rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--zp-text-faint); padding: var(--sp-3) var(--sp-3) var(--sp-1); }
  .zp-nav-link {
    display: flex; align-items: center; gap: var(--sp-3);
    padding: var(--sp-2) var(--sp-3); border-radius: var(--zp-radius-xs);
    color: var(--zp-text); text-decoration: none;
    font-size: .93rem; min-height: 40px;
    transition: background var(--zp-dur-fast) var(--zp-ease);
  }
  .zp-nav-link:hover { background: var(--zp-primary-soft); color: var(--zp-primary); }
  .zp-nav-link.active { background: var(--zp-primary); color: var(--zp-on-primary); font-weight: 600; }
  .zp-nav-link.active .q-icon { color: var(--zp-on-primary); }
  .zp-nav-icon { width: 20px; text-align: center; }
  .zp-nav-count {
    margin-left: auto; font-size: .7rem; font-weight: 700;
    font-variant-numeric: tabular-nums;
    background: var(--zp-neutral-bg); color: var(--zp-neutral-fg);
    padding: 1px 7px; border-radius: var(--zp-radius-pill);
  }
  .zp-nav-link.active .zp-nav-count { background: rgba(255,255,255,.22); color: var(--zp-on-primary); }

  /* ---- spodní lišta (mobil) ---- */
  .zp-tabbar {
    display: flex; align-items: stretch;
    background: var(--zp-surface);
    border-top: 1px solid var(--zp-border);
    padding-bottom: env(safe-area-inset-bottom);
  }
  .zp-tabbar-item {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 2px;
    padding: var(--sp-2) var(--sp-1); min-height: var(--zp-tap);
    color: var(--zp-text-soft); text-decoration: none;
    font-size: .66rem; letter-spacing: .01em; position: relative;
  }
  .zp-tabbar-item.active { color: var(--zp-primary); font-weight: 700; }
  .zp-tabbar-item.active::before {
    content: ""; position: absolute; top: 0; left: 22%; right: 22%;
    height: 2px; background: var(--zp-primary); border-radius: 0 0 2px 2px;
  }
  .zp-tabbar-dot {
    position: absolute; top: 6px; left: 50%; margin-left: 6px;
    min-width: 15px; height: 15px; padding: 0 3px;
    border-radius: var(--zp-radius-pill);
    background: var(--zp-bad-line); color: #fff;
    font-size: .58rem; font-weight: 700; line-height: 15px; text-align: center;
    font-variant-numeric: tabular-nums;
  }

  /* ---- hlavička ---- */
  .zp-header-title { font-size: 1.05rem; font-weight: 700; line-height: 1.2; color: var(--zp-text); margin: 0; }
  .zp-header-sub { font-size: .7rem; line-height: 1.2; color: var(--zp-text-soft); margin: 0; letter-spacing: .02em; }
  .zp-user-name {
    max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    color: var(--zp-text);
  }
  /* Na mobilu se stejné číslo ukazuje jako puntík ve spodní liště, tady
     by jen ubíralo místo tlačítkům. */
  .zp-streak { display: none; }
  @media (min-width: 900px) { .zp-streak { display: inline-flex; } }
  .zp-streak {
    align-items: center; gap: var(--sp-1);
    padding: 3px 9px; border-radius: var(--zp-radius-pill);
    border: 1px solid var(--zp-border); background: var(--zp-surface-sunk);
    font-size: var(--fs-xs); font-weight: 600; color: var(--zp-text-soft);
    font-variant-numeric: tabular-nums; white-space: nowrap;
  }
  .zp-streak.due { border-color: var(--zp-primary-line); color: var(--zp-primary); background: var(--zp-primary-soft); }

  /* ---- hero ---- */
  .zp-hero { padding: var(--sp-5); border-radius: var(--zp-radius); color: #fff; box-shadow: var(--zp-shadow); }
  @media (min-width: 600px) { .zp-hero { padding: var(--sp-6); } }
  .zp-hero-primary { background: linear-gradient(135deg, #0F5F76 0%, #0A3F52 100%); }
  .zp-hero-success { background: linear-gradient(135deg, #059669, #16A34A); text-align: center; }
  .zp-hero-danger  { background: linear-gradient(135deg, #B91C1C, #DC2626); text-align: center; }
  .zp-hero-title { font-size: clamp(1.4rem, 1.1rem + 1.4vw, 2rem); font-weight: 800; letter-spacing: -.02em; }
  .zp-hero-sub { font-size: var(--fs-body); opacity: .9; margin-top: var(--sp-1); }
  .zp-hero-pass { padding: var(--sp-5); border-radius: var(--zp-radius); color: #fff; text-align: center; background: linear-gradient(135deg, #059669, #16A34A); }
  .zp-hero-fail { padding: var(--sp-5); border-radius: var(--zp-radius); color: #fff; text-align: center; background: linear-gradient(135deg, #B91C1C, #DC2626); }

  /* Na úzkém displeji jde tlačítko pod text, ne vedle něj — jinak se
     přes sebe překrývají. Přebíjí .zp-nowrap vyšší specificitou. */
  .zp-hero .zp-row-between {
    flex-wrap: wrap; white-space: normal; gap: var(--sp-3);
  }
  .zp-hero .zp-row-between > * { min-width: 0; }
  .zp-hero .q-btn { width: 100%; }
  @media (min-width: 600px) {
    .zp-hero .zp-row-between { flex-wrap: nowrap; }
    .zp-hero .q-btn { width: auto; }
  }

  /* ---- heatmapa ---- */
  /* Sloupec = týden, řádek = den. Dřív to bylo `1fr`, takže se buňky
     roztáhly na pruhy přes celý týden a měsíce spadly pod sebe. */
  .zp-hm { display: flex; gap: var(--sp-2); align-items: flex-start; }
  /* Popisky dnů stojí mimo posuvnou část, ale musí začít až pod řádkem
     měsíců — odtud to odsazení nahoře (16px řádek + 4px mezera). */
  .zp-hm-days { display: flex; flex-direction: column; gap: 3px; flex: none; padding-top: 20px; }
  .zp-hm-days span { font-size: .6rem; height: 11px; line-height: 11px; color: var(--zp-text-soft); text-align: right; }
  .zp-hm-scroll { flex: 1; min-width: 0; overflow-x: auto; padding-bottom: 4px; }
  .zp-hm-months { display: flex; height: 16px; margin-bottom: 4px; font-size: var(--fs-xs); color: var(--zp-text-soft); }
  .zp-hm-month { flex: none; overflow: hidden; white-space: nowrap; }
  .zp-hm-body { display: grid; grid-template-rows: repeat(7, 11px); grid-auto-flow: column; grid-auto-columns: 11px; gap: 3px; }
  .zp-hm-cell { border-radius: 2px; background: var(--zp-hm-0); }
  .zp-hm-l0 { background: var(--zp-hm-0); }
  .zp-hm-l1 { background: var(--zp-hm-1); }
  .zp-hm-l2 { background: var(--zp-hm-2); }
  .zp-hm-l3 { background: var(--zp-hm-3); }
  .zp-hm-l4 { background: var(--zp-hm-4); }
  .zp-hm-legend { display: flex; align-items: center; justify-content: flex-end; gap: 4px;
    font-size: var(--fs-xs); color: var(--zp-text-soft); margin-top: var(--sp-2); }
  .zp-hm-legend .zp-hm-cell { width: 11px; height: 11px; }

  /* ---- klávesa ---- */
  .zp-kbd {
    display: inline-block; padding: 1px 6px; margin-left: 4px;
    font-family: var(--ff-mono); font-size: .7rem;
    background: var(--zp-neutral-bg); color: var(--zp-neutral-fg);
    border-radius: 4px; border: 1px solid var(--zp-border);
  }

  /* ---- prázdný stav ---- */
  .zp-empty, .zp-empty-container { text-align: center; padding: var(--sp-7) var(--sp-4); }
  .zp-empty-icon { font-size: 3rem; opacity: .4; margin-bottom: var(--sp-2); }
  .zp-empty-container .zp-empty-icon-wrap {
    display: inline-flex; width: 64px; height: 64px;
    align-items: center; justify-content: center; border-radius: 50%;
    background: var(--zp-primary-soft); color: var(--zp-primary);
    margin-bottom: var(--sp-3);
  }

  /* ---- nadpis stránky ---- */
  .zp-page-header { margin-bottom: var(--sp-4); }
  .zp-page-header .zp-eyebrow {
    display: inline-flex; align-items: center; gap: var(--sp-1);
    color: var(--zp-primary); font-weight: 600;
    font-size: var(--fs-xs); letter-spacing: .08em; text-transform: uppercase;
    margin-bottom: var(--sp-1);
  }

  /* ---- studium: řádek s filtry ---- */
  /* Na telefonu se čtyři ovládací prvky skládaly pod sebe a i s nadpisem
     ukrojily 500 z 844 pixelů — otázka začínala až pod přehybem. */
  .zp-study-controls { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2) var(--sp-3); }
  .zp-study-controls > * { min-width: 0 !important; }
  .zp-study-controls > .zp-flex-1 { grid-column: 1 / -1; text-align: left !important; }
  @media (min-width: 900px) {
    .zp-study-controls { display: flex; }
    .zp-study-controls > .zp-flex-1 { text-align: right !important; }
  }

  /* ---- studium ---- */
  .zp-study-grid { display: flex; flex-wrap: wrap; gap: 5px; max-height: 240px; overflow-y: auto; padding: 6px 2px; }
  .zp-chip {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 40px; height: 32px; padding: 0 7px; font-size: var(--fs-xs);
    border: 1px solid var(--zp-border); border-radius: 7px;
    background: var(--zp-surface); color: var(--zp-text); cursor: pointer;
    font-variant-numeric: tabular-nums; user-select: none;
    transition: background var(--zp-dur-fast), border-color var(--zp-dur-fast);
  }
  .zp-chip:hover { border-color: var(--zp-primary); }
  .zp-chip.seen { background: var(--zp-primary-soft); border-color: var(--zp-primary-line); }
  .zp-chip.known { background: var(--zp-ok-bg); border-color: var(--zp-ok-line); color: var(--zp-ok-fg); font-weight: 600; }
  .zp-chip.cur { outline: 2px solid var(--zp-primary); outline-offset: 1px; font-weight: 700; }

  /* Plná šířka, ať se odpovědi nezarovnávají každá jinak podle délky textu. */
  .zp-answer-correct, .zp-answer-neutral {
    display: block; width: 100%;
    border-radius: var(--zp-radius-sm); padding: var(--sp-3) var(--sp-4);
    text-wrap: pretty;
  }
  .zp-answer-correct {
    border: 1.5px solid var(--zp-ok-line); background: var(--zp-ok-bg);
    color: var(--zp-ok-fg); font-size: var(--fs-body); font-weight: 500;
  }
  .zp-answer-neutral {
    border: 1px solid var(--zp-border); font-size: var(--fs-opt); color: var(--zp-text-soft);
  }

  /* ---- obrázek otázky ---- */
  .zp-image-wrap {
    position: relative; cursor: zoom-in; display: inline-block;
    border-radius: var(--zp-radius-sm); overflow: hidden;
    background: var(--zp-surface-sunk); padding: var(--sp-2);
  }
  .zp-image-wrap .zp-zoom-hint {
    position: absolute; top: 8px; right: 8px;
    background: rgba(0,0,0,.6); color: #fff;
    width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
    border-radius: 50%; opacity: 0; transition: opacity var(--zp-dur) var(--zp-ease);
    pointer-events: none;
  }
  .zp-image-wrap:hover .zp-zoom-hint { opacity: 1; }
}
"""


# ---------------------------------------------------------------------------
# 5. UTILITY
# ---------------------------------------------------------------------------
UTILITIES = """
@layer zp.utils {
  .zp-mt-xs { margin-top: var(--sp-1); }
  .zp-mt-sm { margin-top: var(--sp-2); }
  .zp-mt-md { margin-top: var(--sp-3); }
  .zp-mt-lg { margin-top: var(--sp-5); }
  .zp-mt-xl { margin-top: var(--sp-6); }
  .zp-mb-sm { margin-bottom: var(--sp-2); }
  .zp-mb-md { margin-bottom: var(--sp-3); }
  .zp-mb-lg { margin-bottom: var(--sp-5); }
  .zp-gap-xs { gap: var(--sp-1); }
  .zp-gap-sm { gap: var(--sp-2); }
  .zp-gap-md { gap: var(--sp-3); }
  .zp-gap-lg { gap: var(--sp-5); }

  /* Jen na mobilu / jen od tabletu výš */
  .zp-only-mobile { display: revert; }
  .zp-from-md { display: none; }
  @media (min-width: 900px) {
    .zp-only-mobile { display: none; }
    .zp-from-md { display: revert; }
  }
}
"""


# ---------------------------------------------------------------------------
# 6. PŘEBÍJENÍ QUASARU — záměrně MIMO vrstvy
# ---------------------------------------------------------------------------
# Neuvrstvené CSS má v kaskádě přednost před uvrstveným. Quasar a Tailwind
# jsou neuvrstvené, takže tenhle blok je jediné místo, kde se s nimi potkáváme
# — a proto jediné, kde má smysl `!important`.
QUASAR = """
html, body { overflow-x: hidden; max-width: 100vw; }
body {
  background: var(--zp-bg) !important;
  color: var(--zp-text) !important;
  -webkit-font-smoothing: antialiased;
  text-size-adjust: 100%;
}
.q-page-container, .q-page { max-width: 100%; }

.q-header {
  background: var(--zp-surface) !important;
  color: var(--zp-text) !important;
  border-bottom: 1px solid var(--zp-border) !important;
  box-shadow: none !important;
  min-height: 56px;
}
/* Ikony v hlavičce jsou tiché. Čtyři barevná tlačítka vedle sebe soupeří
   o pozornost s obsahem stránky — barva naskočí až na najetí. */
.q-header .q-btn { color: var(--zp-text-soft) !important; }
.q-header .q-btn:hover { color: var(--zp-primary) !important; }
.q-header .zp-hamburger { color: var(--zp-primary) !important; }
.q-header .q-btn { min-width: 40px; min-height: 40px; padding: 8px; }
.q-header .q-btn::before { inset: -4px; }

.q-footer { background: transparent !important; box-shadow: none !important; }

.q-drawer {
  background: var(--zp-surface) !important;
  border-right: 1px solid var(--zp-border) !important;
  color: var(--zp-text);
}
.q-drawer .q-icon { color: inherit; }

.q-separator { background: var(--zp-border) !important; }

.q-dialog .q-card { background: var(--zp-surface) !important; color: var(--zp-text) !important; }

/* Formulářové prvky — Quasar si je barví sám */
.q-field__native, .q-field__input, .q-field__prefix, .q-field__suffix { color: var(--zp-text) !important; }
.q-field__label { color: var(--zp-text-soft) !important; }
.q-field--outlined .q-field__control { background: var(--zp-surface) !important; }
.q-field--outlined .q-field__control::before { border-color: var(--zp-border) !important; }
.q-checkbox__label, .q-radio__label, .q-toggle__label { color: var(--zp-text) !important; }
.q-item { color: var(--zp-text); }

/* Filtry v navigátoru jsou Quasar tlačítka — barvu popisku si nastavují samy
   podle propu `color`, takže aktivní chip vycházel v barvě textu na stejně
   barevném podkladu a nebyl vidět. */
.zp-qnav-filter.active,
.zp-qnav-filter.active .q-btn__content { color: var(--zp-on-primary) !important; }

/* Hamburger. Na mobilu ho nahrazuje položka Menu ve spodní liště — dva
   vstupy do stejné navigace by si jen konkurovaly. */
.zp-hamburger { display: none !important; }
@media (min-width: 900px) {
  .zp-hamburger {
    display: inline-flex !important;
    min-width: var(--zp-tap) !important; min-height: var(--zp-tap) !important;
  }
  .zp-hamburger .q-icon { font-size: 28px !important; }
}

/* NiceGUI obaluje obsah stránky vlastním `.nicegui-content` s odsazením 16 px.
   U stránek s navigátorem musí panel sedět na hraně okna, takže se ruší. */
@media (min-width: 1100px) {
  .nicegui-content:has(.zp-quiz-with-nav) { padding: 0 !important; gap: 0 !important; }
}

/* Obsah nesmí končit pod spodní lištou. */
.zp-container, .zp-container-narrow { padding-bottom: calc(var(--sp-8) + 56px + env(safe-area-inset-bottom)); }
@media (min-width: 900px) {
  .zp-container, .zp-container-narrow { padding-bottom: var(--sp-8); }
}

/* Plotly — průhledné pozadí, ať sedí do obou režimů */
.js-plotly-plot .main-svg { background: transparent !important; }
.js-plotly-plot .bg { fill: transparent !important; }
body.body--dark .js-plotly-plot text, body.dark .js-plotly-plot text { fill: #9AA4B4 !important; }

/* Na velmi úzkých displejích ustupuje podtitulek a jméno */
@media (max-width: 560px) { .zp-user-name { display: none; } }
@media (max-width: 400px) { .zp-header-sub { display: none; } }
"""


GLOBAL_CSS = TOKENS + BASE + LAYOUT + COMPONENTS + UTILITIES + QUASAR

# Vloží se do hlavičky jednou pro celou aplikaci, ne při každém sestavení
# stránky. `apply_theme()` už jen nastavuje paletu Quasaru.
ui.add_head_html(f"<style>{GLOBAL_CSS}</style>", shared=True)


def apply_theme() -> None:
    """Nastaví paletu Quasaru. CSS je vloženo sdíleně už při importu."""
    ui.colors(
        primary=COLORS["primary"],
        secondary="#3F8EA3",
        accent=COLORS["accent"],
        positive=COLORS["success"],
        negative=COLORS["danger"],
        warning=COLORS["warning"],
        info=COLORS["info"],
    )
