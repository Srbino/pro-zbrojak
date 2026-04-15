# Pro Zbroják

> **Český trenažér testových otázek pro zkoušku odborné způsobilosti (ZOZ) k vydání zbrojního průkazu.**
> Podle **zákona č. 90/2024 Sb.** a **nařízení vlády č. 238/2025 Sb.** (oba **účinné od 1. 1. 2026**).

Načte oficiální PDF MV ČR (verze **15. 12. 2025**), zorganizuje **837 otázek** (71 s obrázkem) do 6 různých učebních režimů, sleduje tvůj postup algoritmem **FSRS** (moderní nástupce Anki) a umožní exportovat obtížné otázky pro vysvětlení v Claude Code / ChatGPT.

**100 % lokální** — žádný cloud, žádný účet, žádná data neopouštějí tvůj počítač. Aplikace běží na `127.0.0.1:8080`.

---

## 🇨🇿 Pro koho je to

Aplikace je **určena českým uchazečům** o vydání zbrojního průkazu. Otázky jsou **česky**, rozhraní je **česky**, zákonné reference míří na českou legislativu:

- **Zákon č. 90/2024 Sb.**, o zbraních a střelivu — účinný od 1. 1. 2026
- **Nařízení vlády č. 238/2025 Sb.**, o provádění zkoušek podle zákona o zbraních a střelivu — účinné od 1. 1. 2026
- Zdrojové PDF: **„Soubor testových otázek pro teoretickou část ZOZ a komisionální zkoušku"** (MV ČR, verze 15. 12. 2025)

### Pravidla zkoušky podle NV č. 238/2025

- **30 otázek** vybraných náhodně z katalogu
- **40 minut** časový limit
- 3 varianty odpovědí `a) b) c)`, **právě jedna správná**
- **Hranice úspěšnosti:**
  - 🎯 **Standardní zbrojní oprávnění** (dříve skupiny A, B, C) — **≥ 26/30**
  - 🎯 **Rozšířené zbrojní oprávnění** — **≥ 28/30**
- Pass/fail bez bodového vážení

---

## Obsah

- [Funkce](#funkce)
- [Instalace krok za krokem](#instalace-krok-za-krokem)
  - [macOS / Linux](#macos--linux)
  - [Windows](#windows)
- [Stažení oficiálního PDF](#stažení-oficiálního-pdf)
- [Spuštění aplikace](#spuštění-aplikace)
- [Klávesové zkratky](#klávesové-zkratky)
- [Doporučený workflow učení](#doporučený-workflow-učení)
- [Řešení problémů (FAQ)](#řešení-problémů-faq)
- [Architektura](#architektura)
- [Testy](#testy)
- [Pro vývojáře](#pro-vývojáře)
- [Licence](#licence)

---

## Funkce

| | |
|---|---|
| 🏃 **Marathon** | Sekvenční průchod všech 837 otázek. Pozice se pamatuje mezi restarty. |
| 🧠 **Denní review (SRS)** | Spaced repetition algoritmem **FSRS**. Ohodnoť obtížnost 1–4 a algoritmus rozhodne, kdy otázku ukáže znovu (za < 10 min / 1 den / pár dní / týden+). |
| 🎯 **Lekce z chyb** | Opakuje jen otázky, kde jsi chyboval. |
| 🎓 **Mastery podle oblasti** | Trénuj oblast (právo / zbraně / zdrávo) dokud nezvládneš ≥ 90 % na 30 odpovědích. |
| 📝 **Simulace zkoušky** | 30 otázek, 40 min (nastavitelné), volba úrovně: Standardní (≥ 26/30) nebo Rozšířené (≥ 28/30). |
| 🎲 **Náhodné procvičování** | Volný kvíz režim. |
| ⭐ **Bookmarky** | Flagni si otázky k zamyšlení. |
| 📤 **Export pro AI** | Vygeneruje Markdown s chybami + hotovým promptem pro Claude Code / ChatGPT. |
| 📊 **Statistiky** | Úspěšnost per oblast, trend simulací, heatmapa aktivity za 90 dní. |
| 🌗 **Light / Dark mode** | Přepnutelné |
| 📱 **Mobile responsive** | Funguje i na telefonu a tabletu (stačí otevřít `127.0.0.1:8080`). |

---

## Instalace krok za krokem

### Požadavky

- **Python 3.11 nebo novější** (ověř: `python3 --version`)
- **Git** (pro klon repa)
- ~ **400 MB místa** na disku (venv + chromium pro testy)

### macOS / Linux

**1. Zkontroluj Python verzi:**
```bash
python3 --version
# Musí být 3.11, 3.12 nebo 3.13
```

Pokud ne:
```bash
# macOS (Homebrew)
brew install python@3.13

# Ubuntu / Debian
sudo apt update && sudo apt install python3.13 python3.13-venv
```

**2. Naklonuj repo:**
```bash
git clone https://github.com/Srbino/pro-zbrojak.git
cd pro-zbrojak
```

**3. Nainstaluj:**
```bash
make install
```
> Vytvoří `.venv/`, nainstaluje všechny závislosti (NiceGUI, pdfplumber, fsrs…) + Chromium pro UI testy. Trvá ~1–2 min.

Bez `make`:
```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

### Windows

**1. Nainstaluj Python 3.11+** z [python.org](https://www.python.org/downloads/) — zaškrtni **„Add Python to PATH"**.

**2. Otevři `cmd` nebo PowerShell, naklonuj repo:**
```cmd
git clone https://github.com/Srbino/pro-zbrojak.git
cd pro-zbrojak
```

**3. Nainstaluj:**
```cmd
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
```

---

## Stažení oficiálního PDF

Repo **neobsahuje PDF** (licenční důvody + velikost 3 MB). Stáhni si ho ručně:

**1. Jdi na stránku MV ČR:**
👉 https://www.mvcr.gov.cz/clanek/zbrane-strelivo-munice-a-bezpecnostni-material.aspx

**2. Najdi „Soubor testových otázek pro teoretickou část ZOZ a komisionální zkoušku"** (verze 15. 12. 2025) a stáhni PDF.

**3. Ulož do kořene repa** — název musí začínat `MV-Soubor_testovych_otazek_`:
```
pro-zbrojak/
├── MV-Soubor_testovych_otazek_pro_teoretickou_cast_ZOZ_a_komisionalni_zkousku_-_20251215.pdf
├── app.py
└── ...
```

**4. Naparsuj PDF** (jednorázově, trvá ~30 s):
```bash
make parse
```

Bez `make`:
```bash
.venv/bin/python parse_pdf.py      # macOS/Linux
.venv\Scripts\python parse_pdf.py  # Windows
```

Výsledek:
```
✅ Zapsáno: 837 otázek → data/questions.json
📷 S obrázkem: 71
⚠️ Nedořešeno: 0
```

---

## Spuštění aplikace

```bash
make run
```

Bez `make`:
```bash
./run.sh          # macOS / Linux
run.bat           # Windows
```

Automaticky se otevře **http://127.0.0.1:8080** v tvém prohlížeči. 🎯

**Ukončení:** `Ctrl+C` v terminálu.

---

## Klávesové zkratky

### V kvízu

| Klávesa | Akce |
|---|---|
| `1` / `a` | Odpověď A |
| `2` / `b` | Odpověď B |
| `3` / `c` | Odpověď C |
| `Enter` / `mezera` | Další otázka |
| `F` | Přepnout bookmark |
| `?` (ikona v headeru) | Zobrazit zkratky |

### SRS rating (po odpovědi)

| Klávesa | Rating | Příští výskyt |
|---|---|---|
| `1` | Znovu | za < 10 min |
| `2` | Těžké | za ~1 den |
| `3` | Dobré | za pár dní |
| `4` | Snadné | za týden+ |

---

## Doporučený workflow učení

**Fáze 1 — Seznámení (týden 1–2)**
- Spusť `Marathon` a projdi **celý katalog 837 otázek**. Nejsi povinný si všechno hned zapamatovat — algoritmus zaznamenává, kde chybuješ.

**Fáze 2 — Denní rutina (2 min ráno, 5 min večer)**
- `Denní review (SRS)` — dnešní fronta otázek ti vyskočí na dashboard.
- Ohodnoť obtížnost po každé odpovědi. Algoritmus ti obtížné otázky příště ukáže dřív, lehké později.

**Fáze 3 — Utužení (1–2× týdně)**
- `Lekce z chyb` — opakování slabých míst.
- `Mastery podle oblasti` — zvlášť pro každou ze tří oblastí (právo / zbraně / zdrávo) dokud nezvládneš ≥ 90 %.

**Fáze 4 — Před zkouškou (poslední týden)**
- `Simulace zkoušky` — **3× pro úroveň, kterou skládáš** (Standardní nebo Rozšířené).
- Po každé simulaci projdi chybné otázky a exportuj je pro AI vysvětlení.

**Fáze 5 — Když nerozumíš**
- U otázky klikni na **export** → otevři vygenerovaný `.md` v Claude Code / ChatGPT.
- AI ti vysvětlí s citacemi ze zákona č. 90/2024 Sb. a mnemotechnikou.

---

## Řešení problémů (FAQ)

**„`python3: command not found`" na Windows**
→ Použij `python` místo `python3`.

**„Error: PDF file not found" při `make parse`**
→ Zkontroluj, že PDF leží v kořeni repa a název začíná `MV-Soubor_testovych_otazek_`.

**„Port 8080 is already in use"**
→ Některá jiná aplikace obsadila port. Ukonči ji, nebo uprav `app.py`:
```python
ui.run(host="127.0.0.1", port=8081, ...)
```

**Aplikace běží, ale prohlížeč se neotevřel**
→ Otevři manuálně http://127.0.0.1:8080.

**Po reinstalaci chci zachovat historii pokusů**
→ Zálohuj `data/stats.db` před `make clean`. Po instalaci ji nakopíruj zpět.

**Chci začít od nuly (reset historie)**
→ V aplikaci: `Nastavení → Reset historie` (dvojí potvrzení).

**Stránky se pomalu nahrávají / mobilní chybí layout**
→ Hard-refresh (`Cmd+Shift+R` / `Ctrl+Shift+R`) pro cache bust.

**Jak aplikaci aktualizovat?**
```bash
git pull
make install   # re-instaluje případné nové závislosti
```

**MV ČR vydalo novou verzi PDF — co s tím?**
→ Nahraď starou PDF novou ve stejné složce a spusť `make parse`. Databáze úspěšnosti se zachová díky hash-ID otázek (viz architektura).

---

## Architektura

```
pro-zbrojak/
├── app.py                    spouštěč NiceGUI (39 řádků, jen bootstrap)
├── parse_pdf.py              jednorázový parser PDF → JSON + images
├── pyproject.toml            závislosti + ruff + pytest config
├── Makefile                  make install / parse / run / test / mindmap / clean
├── LICENSE                   MIT
├── README.md                 tento soubor
├── PRD.md                    původní produktový návrh
├── src/
│   ├── parser/               pydantic models pro otázky
│   ├── db/                   SQLite store (attempts, SRS state, bookmarks, exam results)
│   ├── learning/             FSRS wrapper, heatmap data
│   ├── export/               Markdown export pro Claude Code
│   └── ui/
│       ├── theme.py          design tokens, CSS utility classes, dark mode
│       ├── icons.py          Material Symbols registry
│       ├── layout.py         NAV_ITEMS + page_shell (header + drawer)
│       ├── components.py     sdílené UI primitivy + QuizSession
│       ├── quiz.py           QuizCard (inline obrázek + zoom dialog)
│       └── pages/            Dashboard / Marathon / SRS / Mastery / Exam / ...
├── scripts/
│   └── generate_mindmap.py   generátor QUESTIONS_MINDMAP.md pro ruční kontrolu
├── tests/                    129+ testů (pytest + Playwright)
├── data/                     questions.json, stats.db (gitignored)
└── images/                   extrahované obrázky z PDF (gitignored)
```

### Technologie

**Python 3.11+** · [**NiceGUI 3**](https://nicegui.io/) (Quasar + Vue) · [**pdfplumber**](https://github.com/jsvine/pdfplumber) · [**PyMuPDF**](https://pymupdf.readthedocs.io/) · [**pydantic v2**](https://docs.pydantic.dev/) · [**sqlite-utils**](https://sqlite-utils.datasette.io/) · [**fsrs**](https://github.com/open-spaced-repetition/py-fsrs) · [**plotly**](https://plotly.com/python/) · [**rich**](https://rich.readthedocs.io/) · [**pytest + Playwright**](https://playwright.dev/python/).

### Parser — jak to funguje

1. **Textová segmentace** (pdfplumber): regex `^(\d+)\.\s*` pro otázky, `^([ABCabc])\)\s+` pro varianty.
2. **Detekce správné odpovědi**: PDF MV ČR označuje správnou variantu **šedým pozadím** (fill ≈ `0.827` grayscale). Parser čte `page.rects`, spáruje s textovým řádkem.
3. **Font glyph fix**: PDF má rozbitou CMap (`Ɵ`→`ti`, `ơ`→`ti`, `Ō`→`ft`, `ﬁ`→`fi`). Post-process tabulka normalizuje text.
4. **Obrázky**: `page.get_pixmap(clip=rect, dpi=170)` rasterizuje **výřez stránky včetně overlay čísel 1–6** (pouhá extrakce embedded JPEG by ztratila anotace).
5. **Stabilní hash-ID**: SHA-1 z textu otázky + odpovědí. **Přežije přečíslování** v nové verzi PDF — tvoje DB úspěšnosti zůstane nedotčená.

**Výsledek**: 837 otázek, **0 nedořešených**, 71 obrázků správně přiřazených, 100 % textu bez broken glyphů.

---

## Testy

```bash
make test              # vše (129+ testů, ~2.5 min)
make test-ui           # jen UI E2E (Playwright)
pytest tests/test_images.py -v
```

| Soubor | Testů | Co ověřuje |
|---|---:|---|
| `test_parser_invariants` | 18 | shape, distribuce A/B/C, unique IDs, žádné broken glyphy |
| `test_parser_known_questions` | 11 | ručně ověřené Q1–5, Q234, Q711 (Glock) |
| `test_parser_cross_validation` | 2 | 50 náhodných otázek znovu porovnáno proti PDF |
| `test_db` | 7 | SQLite store, attempts, bookmarks, reset |
| `test_srs` | 4 | FSRS wrapper |
| `test_export` | 3 | Markdown export pro Claude Code |
| `test_images` | 9 | každý PNG validní, HTTP 200, DOM naturalWidth > 0, zoom dialog |
| `test_icons_render` | 1 | každý Material Icon glyph se vykreslí |
| `test_no_emoji_in_ui` | 3 | statický audit — žádná emoji v `src/` |
| `test_ui_icons` | 5 | DOM obsahuje `<q-icon>` místo emoji |
| `test_ui_e2e` | 12 | quiz flow, exam, dark mode, mobile |
| `test_ui_interactions` | 13 | keyboard, drawer, bookmark, SRS rating, help |
| `test_responsive` | 10 | hamburger 44 px, mobile drawer, perf budget |
| `test_responsive_gallery` | 30 | 10 stránek × 3 viewporty, zero horizontal overflow |

### Myšlenková mapa otázek pro ruční validaci

```bash
make mindmap
# → vygeneruje QUESTIONS_MINDMAP.md (~1900 řádků)
```

Obsahuje všech 837 otázek rozdělených po oblastech + **inline thumbnails** 71 obrázkových otázek. Otevři v editoru s Markdown preview (VS Code, Typora) a porovnej s PDF.

---

## Pro vývojáře

```bash
make install        # .venv + dev deps + playwright chromium
make lint           # ruff check + format
make test           # pytest
make clean          # smaže DB, obrázky, cache
make clean-all      # + smaže venv
```

### Design principy (KISS + DRY)

- **`app.py` = 39 řádků** — jen bootstrap + `ui.run()`. Každá stránka má vlastní modul v `src/ui/pages/`.
- **`NAV_ITEMS`** v `layout.py` — jediný zdroj pravdy pro navigaci (drawer + dashboard tiles).
- **`QuizSession`** — sjednocuje `random / mistakes / flagged / mastery` v jednom runneru.
- **`icons.py`** — sémantický název → Material Symbol glyph.
- **Sdílené komponenty** v `components.py`: `stat_card`, `mode_tile`, `hero_result`, `rating_bar`, `empty_state`.
- **Design system**: `theme.py` s design tokens (`--zp-primary`, `--zp-radius`, `.zp-display`, `.zp-grid-3` …). Dark mode přes `body.body--dark` overrides.

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

Přidej `from . import moje_stranka` v `src/ui/pages/__init__.py` a záznam do `NAV_ITEMS` v `layout.py`.

---

## Licence

**MIT** pro kód aplikace — viz [LICENSE](LICENSE).

**Otázky** jsou odvozené z oficiálního PDF Ministerstva vnitra ČR a zůstávají v držení jejich vydavatele. Aplikace je jen „čtečka" na existující obsah.

---

## ⚠️ Důležitý disclaimer

Tato aplikace je **studijní pomůcka**, **není oficiálním zdrojem**.

Pro finální přípravu a výklad **vždy konzultuj**:
- **Zákon č. 90/2024 Sb.**, o zbraních a střelivu (aktuální znění)
- **Nařízení vlády č. 238/2025 Sb.**, o provádění zkoušek (aktuální znění)
- **Oficiální materiály** MV ČR a Policie ČR

Autor neodpovídá za případné chyby v parsování PDF, za změny v legislativě, ani za neúspěch u zkoušky. **Zbrojní průkaz je vážná věc** — vlastnictví a nošení zbraně nese právní i etickou odpovědnost.

---

## Zdroje

- [Zákon č. 90/2024 Sb., o zbraních a střelivu](https://www.zakonyprolidi.cz/cs/2024-90) (účinný od 1. 1. 2026)
- [Nařízení vlády č. 238/2025 Sb., o provádění zkoušek](https://www.zakonyprolidi.cz/cs/2025-238) (účinné od 1. 1. 2026)
- [MV ČR — Zbraně, střelivo a munice](https://www.mvcr.gov.cz/clanek/zbrane-strelivo-munice-a-bezpecnostni-material.aspx)
- [Policie ČR — Zkoušky odborné způsobilosti](https://policie.gov.cz/zkousky-odborne-zpusobilosti.aspx)
- [FSRS algoritmus (Free Spaced Repetition Scheduler)](https://github.com/open-spaced-repetition/fsrs4anki/wiki)

---

## Přispívání

Issues + PR vítány na GitHubu. Před PR spusť `make test` a `make lint`.

## Kontakt

Autor: [Pavel Srba](mailto:srba@unify.cz)

---

<sub>Pro Zbroják · v0.3.0 · aktualizováno 15. 4. 2026</sub>
