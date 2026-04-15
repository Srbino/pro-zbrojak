# ZP Trenažér

**Lokální trenažér testových otázek pro zkoušku odborné způsobilosti k vydání zbrojního průkazu** (ZOZ podle zákona č. 90/2024 Sb. a NV č. 238/2025 Sb.).

Načte oficiální PDF MV ČR (837 otázek, 71 s obrázkem), zorganizuje je do 6 různých učebních režimů, sleduje tvůj postup pomocí algoritmu **FSRS** (Free Spaced Repetition Scheduler — moderní nástupce Anki), a umožní exportovat obtížné otázky pro vysvětlení v Claude Code / jakékoli AI.

**Vše běží lokálně** — žádný cloud, žádný účet, žádná data neopouští tvůj počítač.

![ZP Trenažér dashboard](docs/screenshots/dashboard.png)

---

## Funkce

| | |
|---|---|
| 🏃 **Marathon** | Sekvenční průchod všech 837 otázek. Pozice se pamatuje, můžeš přerušit a pokračovat. |
| 🧠 **Denní review (SRS)** | Spaced repetition algoritmus FSRS. Ohodnoť obtížnost, algoritmus rozhodne, kdy otázku ukázat znovu (za 10 min / 1 den / pár dní / týden+). |
| 🎯 **Lekce z chyb** | Opakuj jen otázky, kde jsi chyboval. |
| 🎓 **Mastery podle oblasti** | Trénuj oblast (právo / zbraně / zdrávo) dokud nezvládneš ≥ 90 % na posledních 30 odpovědích. |
| 📝 **Simulace zkoušky** | 30 otázek, 40 min, volba úrovně: Standardní (≥ 26/30) nebo Rozšířené (≥ 28/30). Bez okamžité zpětné vazby. |
| 🎲 **Náhodné procvičování** | Volný quiz režim. |
| ⭐ **Bookmarky + poznámky** | Flagni si otázky k zamyšlení. |
| 📤 **Export pro AI** | Vygeneruje Markdown s otázkami, tvými chybami a hotovým promptem pro Claude Code / ChatGPT — nech si vysvětlit obtížné otázky s citacemi zákona. |
| 📊 **Statistiky + heatmapa** | Úspěšnost per oblast, trend simulací, aktivita za 90 dní (GitHub-style). |

---

## Rychlý start

### Požadavky
- **Python 3.11+** (ověř: `python3 --version`)
- **Oficiální PDF** MV ČR (neredistribuováno v repu, viz níže)

### Instalace

```bash
git clone https://github.com/pavelsrba/zp-trenazer.git
cd zp-trenazer
make install
```

### Stažení PDF

Oficiální PDF „Soubor testových otázek pro teoretickou část ZOZ a komisionální zkoušku" stáhni z MV ČR a **ulož do kořene repa** pod názvem začínajícím `MV-Soubor_testovych_otazek_...pdf`:

👉 https://www.mvcr.gov.cz/clanek/zbrane-strelivo-munice-a-bezpecnostni-material.aspx

### Spuštění

```bash
make run
# → otevře http://127.0.0.1:8080
```

První spuštění automaticky naparsuje PDF (~30 s, vygeneruje `data/questions.json` + 71 obrázků). Další spuštění jsou okamžitá.

Alternativně bez Makefile:
```bash
./run.sh           # macOS / Linux
run.bat            # Windows
```

---

## Klávesové zkratky

### Quiz
| Klávesa | Akce |
|---|---|
| `1` / `a` | Odpověď A |
| `2` / `b` | Odpověď B |
| `3` / `c` | Odpověď C |
| `Enter` / `mezera` | Další otázka |
| `F` | Přepnout bookmark |

### SRS rating (po odpovědi)
| Klávesa | Rating | Další výskyt |
|---|---|---|
| `1` | Znovu | za < 10 min |
| `2` | Těžké | za ~1 den |
| `3` | Dobré | za pár dní |
| `4` | Snadné | za týden+ |

Nápovědu k zkratkám otevřeš kdykoli `?` ikonou v headeru.

---

## Doporučený workflow učení

1. **Týden 1–2**: spusť `Marathon`, projdi celý katalog (~ 2 h denně = za týden hotovo).
2. **Denně (5–10 min)**: `Denní review (SRS)` — algoritmus ti nabídne dnešní frontu.
3. **2× týdně**: `Lekce z chyb` — utužení slabých míst.
4. **Týden před zkouškou**:
   - `Mastery` na každé oblasti až do 90 %
   - 3–5× `Simulaci zkoušky` (Standard / Rozšířené)
5. **Když něčemu nerozumíš**: `/export` → otevři výsledný `.md` v Claude Code → AI vysvětlí s citacemi zákona.

---

## Architektura

```
zp-trenazer/
├── app.py                  spouštěč NiceGUI (39 řádků)
├── parse_pdf.py            jednorázový parser PDF → JSON + images
├── pyproject.toml          závislosti + ruff + pytest config
├── Makefile                make install / parse / run / test / mindmap
├── src/
│   ├── parser/             pydantic models pro otázky
│   ├── db/                 SQLite store (attempts, SRS state, bookmarks, exam results)
│   ├── learning/           FSRS wrapper, heatmap data
│   ├── export/             Markdown export pro Claude Code
│   └── ui/
│       ├── theme.py        design tokens, CSS utility classes
│       ├── icons.py        Material Symbols registry
│       ├── layout.py       NAV_ITEMS + page_shell (header + drawer)
│       ├── components.py   sdílené UI primitivy + QuizSession
│       ├── quiz.py         QuizCard (inline obrázek + zoom dialog)
│       └── pages/          Dashboard / Marathon / SRS / Mastery / Exam / ...
├── scripts/
│   └── generate_mindmap.py    generátor QUESTIONS_MINDMAP.md
├── tests/                  129 testů (pytest + Playwright)
├── data/
│   ├── questions.json      vyparsováno z PDF (gitignored)
│   └── stats.db            SQLite historie (gitignored)
└── images/                 extrahované obrázky z PDF (gitignored)
```

### Technologie

**Python 3.11+** · **NiceGUI 3** (Quasar + Vue) · **pdfplumber** (text + rect detekce) · **PyMuPDF** (rasterizace obrázků) · **pydantic v2** · **sqlite-utils** · **fsrs** (spaced repetition) · **plotly** (grafy) · **rich** (CLI) · **pytest + Playwright** (E2E).

### Parser — jak to funguje

1. **Textová segmentace** (pdfplumber): regex `^(\d+)\.\s*` pro otázky, `^([abcABC])\)\s+` pro varianty.
2. **Detekce správné odpovědi**: oficiální PDF označuje správnou variantu **šedým pozadím** (fill ≈ `0.827` grayscale). Parser čte `page.rects`, spáruje s textovým řádkem.
3. **Font glyph fix**: PDF má rozbitou CMap (`Ɵ` → `ti`, `ơ` → `ti`, `Ō` → `ft`, `ﬁ` → `fi`). Post-process tabulka normalizuje.
4. **Obrázky**: `page.get_pixmap(clip=rect, dpi=170)` rasterizuje **celý výřez stránky včetně overlay čísel 1–6** (extrakce embedded JPEG by ztratila anotace).
5. **Stabilní hash-ID**: SHA-1 z textu otázky + odpovědí. Odolné vůči přečíslování při nové verzi PDF.

Výsledek: **837 otázek, 0 nedořešených, 71 obrázků.**

---

## Testy

```bash
make test          # vše (129 testů, ~2.5 min)
make test-ui       # jen UI E2E
pytest tests/test_images.py -v     # konkrétní soubor
```

| Suite | Testů | Co ověřuje |
|---|---:|---|
| `test_parser_invariants` | 18 | shape, distribuce A/B/C, žádné broken glyphy, unique IDs |
| `test_parser_known_questions` | 11 | ručně ověřené Q1–5, Q234, Q711 (Glock) |
| `test_parser_cross_validation` | 2 | 50 náhodných otázek znovu porovnáno proti PDF |
| `test_db` | 7 | SQLite store, attempts, bookmarks, reset |
| `test_srs` | 4 | FSRS wrapper |
| `test_export` | 3 | Markdown export |
| `test_images` | 9 | každý PNG validní, HTTP 200, naturalWidth>0, zoom dialog funguje |
| `test_icons_render` | 1 | každý Material Icon glyph se reálně vykreslí |
| `test_no_emoji_in_ui` | 3 | statický audit — žádná emoji v `src/` |
| `test_ui_icons` | 5 | DOM obsahuje `<q-icon>` místo emoji |
| `test_ui_e2e` | 12 | quiz flow, dark mode, mobile, exam |
| `test_ui_interactions` | 13 | keyboard, drawer, bookmark, SRS rating, help |
| `test_responsive` | 10 | hamburger 44 px, mobile drawer, perf budget |
| `test_responsive_gallery` | 30 | 10 stránek × 3 viewporty, zero horizontal overflow |

---

## Myšlenková mapa otázek

Pro ruční ověření otázek proti PDF:

```bash
make mindmap
# → vygeneruje QUESTIONS_MINDMAP.md (~1900 řádků)
```

Obsahuje **všech 837 otázek** rozdělených po oblastech + **inline thumbnails** všech 71 obrázkových otázek. Otevři v editoru s Markdown preview (VS Code, Typora) a porovnej s PDF.

---

## Vývoj

```bash
make install        # .venv + dev deps + playwright chromium
make lint           # ruff check + format
make test           # pytest
make clean          # smaže DB, obrázky, cache
```

### Struktura kódu

- **KISS**: `app.py` je 39 řádků (jen bootstrap + ui.run). Každá stránka má svůj modul v `src/ui/pages/`.
- **DRY**:
  - `NAV_ITEMS` v `layout.py` — jediný zdroj pravdy pro navigaci (drawer + dashboard tiles).
  - `QuizSession` — sjednocuje `random / mistakes / flagged / mastery` v jednom runneru.
  - Sdílené komponenty v `components.py` (`stat_card`, `mode_tile`, `hero_result`, `rating_bar`, `empty_state`, …).
  - Icon registry v `icons.py` — sémantické jméno → Material Symbol.
- **Design system**: `theme.py` CSS s design tokens (`--zp-primary`, `--zp-radius`, `.zp-display`, `.zp-grid-3`, atd.). Dark mode přes `body.body--dark` overrides.

### Přidání nové stránky

```python
# src/ui/pages/moje_stranka.py
from nicegui import ui
from src.ui.layout import page_shell

@ui.page("/moje-stranka")
def moje_stranka():
    with page_shell("Moje stránka", active_path="/moje-stranka"):
        ui.label("Obsah").classes("zp-h1")
```

Pak přidej `from . import moje_stranka` v `src/ui/pages/__init__.py` a záznam do `NAV_ITEMS` v `layout.py`.

---

## Licence

MIT pro kód. Otázky jsou odvozené z oficiálního PDF MV ČR — viz [LICENSE](LICENSE).

**Disclaimer**: Tato aplikace je **studijní pomůcka**, není oficiálním zdrojem. Pro přípravu vždy konzultuj zákon č. 90/2024 Sb. a NV č. 238/2025 Sb. v aktuálním znění a oficiální materiály MV ČR.

---

## Zdroje

- [Zákon č. 90/2024 Sb., o zbraních a střelivu](https://www.zakonyprolidi.cz/cs/2024-90)
- [Nařízení vlády č. 238/2025 Sb., o provádění zkoušek](https://www.zakonyprolidi.cz/cs/2025-238)
- [MV ČR — Zbraně, střelivo a munice](https://www.mvcr.gov.cz/clanek/zbrane-strelivo-munice-a-bezpecnostni-material.aspx)
- [NiceGUI dokumentace](https://nicegui.io/)
- [FSRS algoritmus](https://github.com/open-spaced-repetition/fsrs4anki/wiki)
