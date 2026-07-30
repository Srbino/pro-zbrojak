# PRD — Trenažér testových otázek pro zbrojní průkaz (ZOZ)

**Verze:** 0.3
**Datum:** 2026-04-15
**Autor:** srba@unify.cz
**Stav:** Návrh k odsouhlasení

> **Změny v 0.3:**
> - Zvolen stack: **Python 3.11+ + NiceGUI** (zdůvodnění v sekci 4).
> - Přidána sekce **5. Metodiky učení** — 6 vědecky podložených režimů (FSRS, Leitner, Mastery, Confidence-based, Two-phase, Marathon).
> - Přidán **First Pass Marathon** s perzistencí pozice a resume.
> - Přidána **integrace s Claude Code** pro vysvětlení obtížných otázek.
> - Stabilní **hash-ID** otázek (přežije novou verzi PDF).
> - Bookmarky, vlastní poznámky, time tracking, kategorizace per oblast.
> - Test fixtures pro parser, logging, MoSCoW, rizika.

---

## 1. Cíl produktu

Lokální multiplatformní aplikace pro samostudium teoretické části zkoušky odborné způsobilosti (ZOZ) k vydání zbrojního průkazu. Aplikace převede oficiální PDF MV ČR „Soubor testových otázek pro teoretickou část ZOZ a komisionální zkoušku" (verze 15. 12. 2025, ~800 otázek) na interaktivní trenažér, sleduje pokroky a chyby, pomáhá se učit dle moderních pedagogických metod a umožňuje exportovat obtížné otázky pro vysvětlení v Claude Code.

**Primární uživatel:** uchazeč o ZP, který se učí na zkoušku a chce:
- projít celý katalog ~800 otázek (alespoň jednou),
- procvičovat opakovaně až do zvládnutí,
- soustředit se na slabá místa (zvlášť právní oblast),
- ověřit a porozumět složitým otázkám pomocí AI (Claude Code).

---

## 2. Kontext zdrojového PDF

Parser musí respektovat:

1. **Číslování otázek:** `1)`, `2)`, … `800)` (číslo + uzavírací závorka), na samostatném řádku.
2. **Tři varianty odpovědí:** `a)`, `b)`, `c)`.
3. **Správná odpověď je vizuálně označena šedým podbarvením.** Hlavní strojový signál → parser čte `page.rects` (obdélníky s výplní), ne jen text.
4. **Některé otázky mají obrázky** (typicky fotografie zbraní s číslovanými částmi). Bez obrázku nelze odpovědět. Parser je extrahuje validně.
5. „Vyberte správnou odpověď:" — kotva pro parser.
6. Hlavičky/patičky/úvodní strany ignorovat.

### 2.1 Zdroj otázek

PDF MV ČR z 15. 12. 2025, kompletní katalog (~800 otázek). Při ostré zkoušce se z něj losuje 30 otázek.

---

## 3. Metodiky učení (jádro produktu)

Místo jednoho generického „kvízu" aplikace nabízí **6 režimů**, každý s konkrétním pedagogickým záměrem. Uživatel je kombinuje podle fáze přípravy.

### 3.1 First Pass Marathon (poprvé projít celý katalog)
**Pedagogický základ:** _Pretest effect_ + _Active recall_ — i špatná odpověď před výkladem zlepšuje budoucí zapamatování.

- Sekvenční průchod **všech ~800 otázek** od první do poslední.
- **Pozice se ukládá do DB** → po zavření aplikace lze pokračovat tam, kde jsi skončil (`Continue` / `Restart` / `Jump to N`).
- Po každé odpovědi okamžitá zpětná vazba + správná odpověď.
- Volitelné mikropoznámky („nevím proč", „složité, ověřit").
- Konec marathonu = milník („Prošel jsi kompletní katalog"). DB ukládá `marathon_run_id` a datum.
- Lze spustit **další marathon** — předchozí výsledky se neztrácí, lze je porovnat.

### 3.2 Spaced Repetition (SRS) — denní review
**Pedagogický základ:** _Ebbinghausova křivka zapomínání_ + algoritmus **FSRS** (Free Spaced Repetition Scheduler — moderní nástupce SM-2 z Anki, otevřená MIT licence). Knihovna `py-fsrs`.

- DB pro každou otázku drží `stability`, `difficulty`, `next_due`.
- Aplikace každý den nabídne fronty otázek, jejichž `next_due ≤ dnes`.
- Po odpovědi uživatel ohodnotí (1–4): _Znovu / Těžké / Dobré / Snadné_ → FSRS posune `next_due`.
- **Nejlepší dlouhodobý nástroj** — řekne ti, kdy se která otázka má vrátit, abys ji nezapomněl.
- Indikátor „dnes ti vyprší X otázek" na hlavní obrazovce.

### 3.3 Mistake Drill (lekce z chyb)
**Pedagogický základ:** _Targeted practice_ — soustředěné opakování slabých míst.

- Generuje krátkou lekci (default 20 otázek) z otázek, kde uživatel chyboval.
- Filtry: posledních N dní, kategorie (právo / zbraně / zdrávo), počet chyb ≥ X.
- Po lekci automaticky aktualizuje SRS stav opravených otázek.

### 3.4 Mastery by Section (zvládnutí oblasti)
**Pedagogický základ:** _Mastery learning_ (Bloom, 1968) — pokračuj, až když máš oblast skutečně zvládnutou.

- Aplikace dělí otázky do oblastí podle NV 238/2025: **právo / nauka o zbraních a střelivu / zdravotnické minimum**.
- Uživatel zvolí oblast → trenažér ji opakuje, dokud nedosáhne ≥ 90 % na posledních 30 odpovědích.
- Vizualizuje pokrok („Právo: 78 % zvládnutí, zbývá 22 otázek").

### 3.5 Confidence-Based Repetition (sebehodnocení jistoty)
**Pedagogický základ:** _Metacognition_ — uvědomit si, čemu nerozumíš.

- Po každé odpovědi uživatel označí „Jsem si jistý / Tipnul / Nemám tušení".
- Otázky z kategorie „Tipnul/Nemám tušení" se vracejí dříve, i když byly odpovězeny správně.
- Cíl: odhalit „false positives" — náhodné správné odpovědi, které jsou ve skutečnosti slepá místa.

### 3.6 Exam Simulation (simulace zkoušky)
**Pedagogický základ:** _Cumulative testing_ + _Test-enhanced learning_.

- Podle NV 238/2025: 30 náhodných otázek, 40 min default (nastavitelné 5–120 min).
- Volba úrovně: **Standardní** (≥ 26/30) / **Rozšířené** (≥ 28/30).
- **Bez okamžité zpětné vazby** — výsledek až na konci (jako reálná zkouška).
- Možnost přeskočit otázku a vrátit se k ní.
- Výsledková obrazovka: skóre, pass/fail, seznam chyb, čas na otázku.
- Persistence — historie všech simulací s datem a skórem (graf trendu).

### Doporučený workflow uživatele
1. **Týden 1–2:** First Pass Marathon — projdi vše jednou.
2. **Denně:** SRS review (10–20 min ráno).
3. **Po Marathonu:** Mistake Drill 2× týdně.
4. **Před zkouškou (poslední týden):** Mastery na slabých oblastech + 3× Exam Simulation.

---

## 4. Stack — rozhodnutí

**Vybráno: Python 3.11+ + NiceGUI.**

### Důvody (proč ne Flask + vanilla, ne React, ne Streamlit)

| Kritérium | Flask + vanilla JS | NiceGUI | FastAPI + React | Streamlit |
|---|---|---|---|---|
| Multiplatformnost | ✅ | ✅ | ✅ | ✅ |
| Build step | ❌ | ❌ | ✅ npm | ❌ |
| Reaktivní komponenty | ručně | ✅ vestavěné | ✅ | omezeně |
| Časovač / live UI updates | manuální WS | ✅ vestavěné | ✅ | ⚠️ rerun model |
| Tabulky, grafy, dialogy | sám | ✅ Quasar/Plotly | ✅ shadcn/ui | ✅ |
| Dark mode | sám | ✅ zdarma | ✅ | ✅ |
| Jeden jazyk (parser+UI+DB) | ✅ Python | ✅ Python | ❌ Py+JS | ✅ Python |
| Křivka učení | nízká | nízká | vysoká | nejnižší |
| Vhodné pro quiz s časovačem | OK | **ideální** | ideální | špatné (rerun) |

**Verdikt:** NiceGUI dává reaktivní UI a hotové komponenty (jako React) bez budovacího kroku a v jednom jazyce s parserem. Robustnější než vanilla JS, jednodušší než React, lepší pro stavový quiz než Streamlit.

### Kompletní stack a knihovny

| Vrstva | Knihovna | Účel |
|---|---|---|
| UI | **NiceGUI** | Reaktivní web-UI v Pythonu (Quasar/Vue interně) |
| PDF text + rects | **pdfplumber** | Detekce šedého podbarvení (správné odpovědi) |
| PDF obrázky | **PyMuPDF (`fitz`)** | Spolehlivá extrakce obrázků (lepší než pdfplumber) |
| Image processing | **Pillow** | Crop, resize, optimize PNG |
| DB | **sqlite3** (stdlib) + **sqlite-utils** | Schema, migrace, dotazy |
| Validace dat | **pydantic v2** | Typovaný model otázky, kontrola JSON |
| Spaced repetition | **py-fsrs** | Algoritmus FSRS pro režim 3.2 |
| CLI parser logging | **rich** | Progress bar, barvy, tabulky během parsu |
| Grafy | **plotly** (přes NiceGUI) | Heatmapa aktivity, trend simulací |
| Testy | **pytest** | Test parseru s fixturami |

Vše MIT/BSD/Apache, pip-installovatelné, žádný build step.

---

## 5. Funkční požadavky

### 5.1 Parser PDF
- **F1.** Skript `parse_pdf.py` převede PDF na `data/questions.json` + `images/<hash>.png`.
- **F2.** Detekce správné odpovědi přes šedý rect (pdfplumber `page.rects`, `non_stroking_color ≈ (0.85, 0.85, 0.85)`).
- **F3.** Extrakce obrázků přes PyMuPDF (`page.get_images()` + `extract_image()`); fallback render výřezu.
- **F4.** Stabilní ID = SHA-1 hash znění otázky (prvních 200 znaků). Pole `pdf_number` drží původní pořadové číslo.
- **F5.** Idempotentní; vypisuje progress přes `rich`.
- **F6.** Otázky bez detekované správné → `data/unparsed.json` + log.
- **F7.** Validace přes pydantic; špatně tvarované otázky se logují, neházejí.
- **F8.** Detekce sekce/oblasti (právo / zbraně / zdrávo) z hlaviček PDF, pokud možné.

### 5.2 Učební režimy (viz sekce 3)
- **F9.** First Pass Marathon s perzistencí pozice a Continue/Restart.
- **F10.** SRS denní review (FSRS).
- **F11.** Mistake Drill (lekce z chyb, filtrovatelná).
- **F12.** Mastery by Section.
- **F13.** Confidence-Based.
- **F14.** Exam Simulation (Standardní/Rozšířené, časovač, bez okamžité zpětné vazby).
- **F15.** Free Random — volné náhodné procvičování (pro krátké pauzy).

### 5.3 Quiz UI
- **F16.** Zobrazení otázky, obrázku (pokud existuje), 3 tlačítek `a/b/c`.
- **F17.** Klávesové zkratky `1/2/3`, `a/b/c`, Enter = další, F = bookmark, N = poznámka, ? = otevřít vysvětlení v Claude Code.
- **F18.** Po odpovědi zelená/červená + zvýraznění správné varianty (mimo Exam mode).
- **F19.** Klikatelný **zoom obrázku** (modal s plnou velikostí).
- **F20.** Indikátor postupu, časovač (Exam mode).
- **F21.** Dark / light mode toggle.

### 5.4 Bookmarky a poznámky
- **F22.** Flag/bookmark otázku (návrat „k zamyšlení") — i správně odpovězenou.
- **F23.** Vlastní textová poznámka per otázka (markdown).
- **F24.** Poznámka může obsahovat **AI-generovaný výklad** (zpětně vložený z Claude Code).

### 5.5 Statistiky
- **F25.** Dashboard: počet pokusů, % úspěšnosti celkem i per oblast, aktuální streak.
- **F26.** Heatmapa aktivity za posledních 90 dní.
- **F27.** Top 20 nejvíce chybovaných otázek.
- **F28.** Trend Exam Simulation skóre v čase (graf).
- **F29.** Per-otázka histogram (kolikrát zkoušeno, % správně, čas-medián).
- **F30.** Reset historie (s dvojím potvrzením).

### 5.6 Integrace s Claude Code (hlavní AI workflow)
- **F31.** Tlačítko **„Vysvětlit otázku v Claude Code"** u každé otázky:
  - vygeneruje markdown s otázkou, odpověďmi, správnou odpovědí, mojí odpovědí a poznámkou,
  - přidá **prompt template** (níže),
  - uloží do `exports/explain_q<hash>_<timestamp>.md`,
  - zkopíruje cestu do schránky a otevře soubor v defaultní aplikaci,
  - vypíše instrukci: „Otevři Claude Code v této složce a nakrm mu tento soubor".
- **F32.** **Bulk export** vybraných chybných otázek (např. všechny z oblasti „právo") do jednoho `.md`.
- **F33.** **Re-import vysvětlení** — uživatel uloží odpověď z Claude Code do souboru, aplikace ji načte a připojí k poznámce u otázky (parsing podle hash-id v hlavičce souboru).

#### Prompt template pro Claude Code
```markdown
# Žádost o vysvětlení testové otázky ZOZ (zbrojní průkaz)

**Hash:** {hash}
**PDF č.:** {pdf_number}
**Oblast:** {section}

## Otázka
{question_text}

{image_markdown}

## Možnosti
- a) {a}
- b) {b}
- c) {c}

**Správná odpověď podle PDF MV ČR:** {correct}
**Moje odpověď:** {my_answer} ({correct_or_not})

## Moje poznámka
{user_note_or_empty}

---

## Co potřebuji
1. **Vysvětli laicky**, proč je správná odpověď `{correct}`.
2. **Cituj konkrétní paragraf** zákona č. 90/2024 Sb. nebo NV č. 238/2025 Sb., na který se otázka váže.
3. Pokud možno **odkaz** na oficiální zdroj (zakonyprolidi.cz, mv.gov.cz).
4. **Proč jsou ostatní odpovědi špatně** — krátce u každé.
5. **Pomůcka pro zapamatování** (mnemotechnika, příklad ze života).

Pokud máš podezření, že odpověď v PDF je zastaralá nebo chybná (nesoulad s aktuálním zněním zákona), upozorni mě.
```

### 5.7 Export
- **F34.** JSON export chyb pro strojové zpracování (otázka, varianty, moje odp., správná, počet chyb, datum, image, note).
- **F35.** Markdown export pro AI chat (čitelný, s prompt templatem).
- **F36.** Backup celé DB (`data/stats.db`) — stáhnout / nahrát.

### 5.8 Spuštění
- **F37.** `./run.sh` (Mac/Linux), `run.bat` (Windows): venv → install → start → otevři browser.
- **F38.** Při prvním běhu, pokud chybí `questions.json`, automaticky parser + onboarding screen s progresem.
- **F39.** Server vázaný na **127.0.0.1:8080** (localhost-only).

---

## 6. Nefunkční požadavky

- **N1. Multiplatformnost:** macOS + Windows (+Linux). NiceGUI funguje všude identicky.
- **N2. Lokalita:** žádný cloud, žádný internet potřeba k běhu (pouze pro AI export workflow uživatel sám použije Claude Code).
- **N3. Localhost-only:** server `127.0.0.1`, žádná expozice do sítě.
- **N4. Závislosti:** všechny pip-installovatelné, jeden `requirements.txt`. Žádné npm.
- **N5. Perzistence:** SQLite DB přežije restart i upgrade `questions.json` (díky hash-ID).
- **N6. Výkon:** start < 3 s, odezva quizu < 100 ms, parser PDF < 60 s.
- **N7. Robustnost parseru:** ≥ 95 % otázek detekováno automaticky; zbytek do `unparsed.json`, neházet.
- **N8. Logging:** `logs/parser.log`, `logs/app.log` s timestampy a kontextem.
- **N9. Disclaimer:** v UI footer + README — „studijní pomůcka, neoficiální, autoři nezodpovídají za chyby; konzultuj s oficiálními zdroji."
- **N10. Verzování:** `__version__` v UI footer i v exportech.

---

## 7. Datový model

### 7.1 `data/questions.json`
```json
{
  "id": "a3f2b1c8…",                           // SHA-1 hash znění otázky (stabilní)
  "pdf_number": 711,                           // pořadí v PDF (může se měnit)
  "section": "nauka_o_zbranich",               // "pravo" | "nauka_o_zbranich" | "zdravotni_minimum" | null
  "question": "Vyberte správnou odpověď:",
  "question_context": "(volitelný úvodní text)",
  "image": "images/a3f2b1c8.png",              // null pokud bez obrázku
  "options": {
    "a": "...",
    "b": "...",
    "c": "..."
  },
  "correct": "c",
  "source_page": 142,
  "source_pdf": "MV-Soubor_testovych_otazek...20251215.pdf",
  "parsed_at": "2026-04-15T11:30:00Z"
}
```

### 7.2 `data/stats.db` (SQLite)
```sql
-- Každá odpověď
CREATE TABLE attempts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id TEXT NOT NULL,                     -- hash-ID
  chosen      TEXT NOT NULL,                     -- 'a' | 'b' | 'c'
  correct     TEXT NOT NULL,
  is_correct  INTEGER NOT NULL,
  confidence  TEXT,                              -- 'sure' | 'guess' | 'no_idea' | NULL
  mode        TEXT NOT NULL,                     -- 'marathon' | 'srs' | 'mistakes' | 'mastery' | 'confidence' | 'exam' | 'random'
  time_ms     INTEGER,
  ts          INTEGER NOT NULL                   -- unix timestamp
);
CREATE INDEX idx_attempts_qid ON attempts(question_id);
CREATE INDEX idx_attempts_correct ON attempts(is_correct);
CREATE INDEX idx_attempts_mode ON attempts(mode);

-- FSRS stav per otázka
CREATE TABLE srs_state (
  question_id TEXT PRIMARY KEY,
  stability   REAL NOT NULL,
  difficulty  REAL NOT NULL,
  next_due    INTEGER NOT NULL,                  -- unix ts
  reps        INTEGER NOT NULL DEFAULT 0,
  lapses      INTEGER NOT NULL DEFAULT 0,
  last_review INTEGER
);
CREATE INDEX idx_srs_due ON srs_state(next_due);

-- Marathon perzistence (resume)
CREATE TABLE marathon_runs (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at  INTEGER NOT NULL,
  finished_at INTEGER,                           -- NULL = běžící
  position    INTEGER NOT NULL,                  -- aktuální index
  total       INTEGER NOT NULL,
  correct     INTEGER NOT NULL DEFAULT 0
);

-- Bookmarky + uživatelské poznámky
CREATE TABLE bookmarks (
  question_id TEXT PRIMARY KEY,
  flagged     INTEGER NOT NULL DEFAULT 0,
  note        TEXT,                              -- markdown, může obsahovat AI vysvětlení
  updated_at  INTEGER NOT NULL
);

-- Exam simulation results (pro trendový graf)
CREATE TABLE exam_results (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  level       TEXT NOT NULL,                     -- 'standard' | 'extended'
  score       INTEGER NOT NULL,                  -- 0..30
  total       INTEGER NOT NULL,                  -- typicky 30
  passed      INTEGER NOT NULL,                  -- 0/1
  duration_s  INTEGER NOT NULL,
  ts          INTEGER NOT NULL
);

-- FTS5 fulltext (pro hledání v otázkách)
CREATE VIRTUAL TABLE questions_fts USING fts5(question_id, content);
```

### 7.3 Adresářová struktura
```
shooting/
├── MV-Soubor_testovych_otazek...pdf
├── PRD.md
├── README.md
├── parse_pdf.py
├── app.py                         (NiceGUI app)
├── pyproject.toml / requirements.txt
├── run.sh / run.bat
├── src/
│   ├── parser/                    (PDF parsing modul)
│   ├── db/                        (sqlite-utils wrappery)
│   ├── learning/                  (FSRS, mastery, mistake drill logika)
│   ├── ui/                        (NiceGUI views)
│   └── export/                    (JSON/MD export, prompt template)
├── data/
│   ├── questions.json
│   ├── unparsed.json
│   └── stats.db
├── images/
│   └── <hash>.png
├── exports/                       (generované MD pro Claude Code)
├── logs/
│   ├── parser.log
│   └── app.log
└── tests/
    ├── fixtures/
    │   ├── sample_questions.pdf   (5–10 otázek, ručně vybrané)
    │   └── expected.json
    └── test_parser.py
```

---

## 8. Strategie parseru

### 8.1 Detekce správné odpovědi (šedý rect)
1. Pro každou stránku: `page.rects` filtr na `non_stroking_color` blízko `(0.85, 0.85, 0.85)` (tolerance ±0.1).
2. Pro každý šedý rect najít odpověď `a/b/c`, jejíž `bbox` se s rectem překrývá.
3. Tu variantu označit jako `correct`.
4. **Fallback** (pokud rect chybí): `char["fontname"]` obsahuje „Bold" → tučně vyznačená správná.
5. **Sentinel** (pokud ani jedno): otázka do `unparsed.json`, log.

### 8.2 Extrakce obrázků (PyMuPDF)
1. `doc[page].get_images()` → list embedded obrázků.
2. `doc.extract_image(xref)` → bytes + ext.
3. Uložit jako `images/<question_hash>.png` (přes Pillow konverze).
4. **Heuristika přiřazení k otázce:** obrázek patří otázce, jejíž hlavička (`N)`) je nejblíž nad obrázkem a před další otázkou.
5. **Fallback** (vektorová grafika): `page.get_pixmap(clip=bbox, dpi=200)` → PNG.

### 8.3 Segmentace
- `^(\d{1,4})\)\s*$` → start otázky.
- `^([abc])\)\s+(.+)$` → varianta odpovědi.
- Volné řádky se připojují k poslední části (otázka / poslední varianta).

### 8.4 Hash-ID
```python
import hashlib
qid = hashlib.sha1(question_text[:200].encode("utf-8")).hexdigest()
```

### 8.5 Detekce oblasti
- Hledat v PDF nadpisy typu „I. Oblast práva", „II. Nauka o zbraních a střelivu", „III. Zdravotnické minimum".
- Otázky pod nadpisem dědí oblast.
- Pokud detekce selže, oblast = `null`, statistika tuto kategorii vynechá.

---

## 9. UI principy
- **NiceGUI Quasar komponenty** (tabulky, dialogy, grafy zdarma).
- **Dark mode** z UI toggle (Quasar nativně).
- **Responzivní** — mobile-friendly out of the box.
- **Klávesové ovládání** všude (1/2/3, Enter, šipky, F=flag, N=note).
- **Hlavní menu (sidebar):** Marathon · SRS dnes · Mistake Drill · Mastery · Exam · Volný režim · Statistiky · Bookmarky · Nastavení.
- **Onboarding** při prvním spuštění: progress parseru → souhrn → nabídka „Začít Marathon".

---

## 10. MoSCoW priority

### Must (MVP — týden 1)
- Parser PDF (pdfplumber + PyMuPDF), hash-ID, validace pydantic
- Režimy: Marathon (s resume), Random, Exam Simulation
- SQLite + attempts + bookmarks + exam_results
- Quiz UI v NiceGUI (klávesy, obrázek, zoom)
- Export JSON/MD + prompt template pro Claude Code
- Dashboard se základními statistikami
- Test fixtures + test parseru
- Disclaimer, log, confirm reset

### Should (verze 0.5)
- SRS s py-fsrs (denní review)
- Mistake Drill (lekce z chyb)
- Mastery by Section (kategorizace)
- Confidence-based hodnocení
- Heatmapa aktivity, graf trendu Examů
- Re-import vysvětlení do poznámek
- Backup/restore DB

### Could (1.0)
- FTS5 hledání v otázkách
- Bulk operace nad bookmarky
- Per-otázka detail s historií
- Light/dark theme switcher v real-time

### Won't (teď)
- Multi-user / účty
- Cloud sync
- Mobil-app / PWA
- Distribuce jako binárka (pyinstaller) — později
- AI integrace přímo v aplikaci (stačí export do Claude Code)

---

## 11. Rizika a mitigace

| Riziko | Pravděpodobnost | Dopad | Mitigace |
|---|---|---|---|
| Parser nedetekuje šedé pozadí spolehlivě | střední | vysoký | Test fixtures (5 ručních otázek), fallback na font, `unparsed.json` |
| Obrázky složené z vektorů (ne embedded) | střední | střední | PyMuPDF fallback render výřezu stránky |
| MV ČR vydá novou verzi PDF s jiným formátem | nízká | vysoký | Hash-ID otázek → DB přežije; verze PDF v metadatech |
| Otázka na zlomu stránky | střední | nízký | Parser sleduje stav přes stránky, ne per-page |
| Uživatel ztratí DB | nízká | vysoký | Backup tlačítko; varování při resetu |
| Otázky v PDF jsou špatně (zastaralé znění) | známé | nízký | AI verifikace přes Claude Code je explicitní cíl |
| FSRS curve out-of-the-box je pro nového uživatele suboptimální | nízká | nízký | Použít defaulty `py-fsrs`, později kalibrovat |

---

## 12. Akceptační kritéria

1. ✅ `./run.sh` (resp. `run.bat`) na čistém systému s Pythonem 3.11+ rozjede aplikaci a otevře `127.0.0.1:8080`.
2. ✅ Parser zpracuje celé PDF, ≥ 95 % otázek má detekovanou správnou odpověď.
3. ✅ Otázka s obrázkem (např. č. 711) se zobrazí s obrázkem; klik = zoom modal.
4. ✅ **Marathon** lze přerušit a pokračovat z poslední pozice.
5. ✅ **SRS** denně nabízí fronty otázek dle FSRS, hodnocení 1–4 funguje.
6. ✅ **Mistake Drill** vygeneruje lekci z otázek s ≥ 1 chybou.
7. ✅ **Exam Simulation** drží časový limit, výsledek se uloží do DB, graf trendu se updatuje.
8. ✅ **Bookmark + poznámka** persistuje, viditelné v detailu i v dashboardu.
9. ✅ **Export pro Claude Code** vygeneruje MD soubor s prompt templatem; cesta v clipboardu.
10. ✅ **Re-import** AI vysvětlení (soubor se hash-id v hlavičce) připojí text k poznámce otázky.
11. ✅ Reset historie vyžaduje dvojí potvrzení.
12. ✅ Test parseru (`pytest`) prochází na 5 fixture otázkách.

---

## 13. Otevřené otázky (vyřeším při implementaci)

- Přesný text nadpisů sekcí v PDF (právo / zbraně / zdrávo) — uvidím při prvním parsu.
- Defaultní FSRS parametry vs. ručně doladěné pro tuto doménu.
- Zda mít „guest mode" bez ukládání nebo pouze single-user (zatím pouze single).

---

## Zdroje
- [Trigger Service: Nový zkušební řád od 1. 1. 2026](https://www.triggerservice.cz/zbrojni-prukaz/novy-zkusebni-rad-od-1-1-2026/)
- [Nařízení vlády č. 238/2025 Sb. (Zákony pro lidi)](https://www.zakonyprolidi.cz/cs/2025-238)
- [MV ČR: Výkladové stanovisko k provádění zkoušek na přelomu 2025/2026 (LEX)](https://gunlex.cz/zbrane-a-legislativa/stanoviska-statu/4495-mv-cr-vykladove-stanovisko-k-provadeni-zkousek-na-prelomu-roku-2025-a-2026)
- [QPQ.cz: Nový zkušební řád platný od 2026](https://www.qpq.cz/blog/novy-zkusebni-rad/)
- [Policie ČR — Zkoušky odborné způsobilosti](https://policie.gov.cz/zkousky-odborne-zpusobilosti.aspx)
- [NiceGUI documentation](https://nicegui.io/)
- [py-fsrs (FSRS algorithm)](https://github.com/open-spaced-repetition/py-fsrs)
- [PyMuPDF documentation](https://pymupdf.readthedocs.io/)
