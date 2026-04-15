# Data — obsah aplikace

Tento adresář obsahuje **veškerý obsah aplikace** potřebný za runtime. Uživatel,
který si klonne repo, dostane aplikaci **plně funkční** bez nutnosti stahovat PDF.

## Soubory

| Soubor | Velikost | Status | Účel |
|---|---:|---|---|
| `questions.json` | ~ 788 KB | **✅ committed** | 837 otázek (pole objektů) |
| `../images/*.png` | ~ 14 MB (71 souborů) | **✅ committed** | Rasterizované obrázky zbraní s overlay čísly |
| `stats.db` | — | `.gitignore` | SQLite historie uživatele (per-install) |
| `unparsed.json` | — | `.gitignore` | Parser diagnostika (prázdné při správném parsu) |

## Formát `questions.json`

Pole objektů ve struktuře (pydantic model `src/parser/models.py::Question`):

```json
{
  "id": "a3f2b1c8…",
  "pdf_number": 711,
  "section": "nauka_o_zbranich",
  "question": "Vyberte správnou odpověď:",
  "image": "images/5088bbe1cd6c62d6ab49b5437dc9ee5112385cbc.png",
  "options": {
    "A": "Závěr je na obrázku výše označen číslem „3" a pažba je označena číslem „4".",
    "B": "Tělo zbraně je na obrázku výše označeno čísly „1" a „4"…",
    "C": "Závěr je na obrázku výše označen čísly „3" a „2"…"
  },
  "correct": "C",
  "source_page": 188,
  "source_pdf": "MV-Soubor_testovych_otazek_pro_teoretickou_cast_ZOZ_a_komisionalni_zkousku_-_20251215.pdf",
  "parsed_at": "2026-04-15T11:30:00+00:00"
}
```

### Pole

| Pole | Typ | Popis |
|---|---|---|
| `id` | string | SHA-1 hash z textu otázky + odpovědí (40 hex znaků). **Stabilní napříč verzemi PDF** — historie úspěšnosti v `stats.db` přežije regeneraci. |
| `pdf_number` | int | Pořadové číslo otázky v PDF (1–837). Může se změnit v nové verzi PDF; slouží jen jako reference. |
| `section` | string \| null | Oblast: `pravo` / `provadeci_predpisy` / `jine_predpisy` / `nauka_o_zbranich` / `zdravotni_minimum`. |
| `question` | string | Text otázky (po normalizaci font glyphů — `Ɵ`→`ti` atd.). |
| `options` | object | `{A, B, C}` → text varianty. Vždy právě 3. |
| `correct` | `"A"` \| `"B"` \| `"C"` | Správná odpověď, detekovaná z šedého pozadí v PDF (fill ≈ 0.827). |
| `image` | string \| null | Relativní cesta k PNG obrázku (`images/<hash>.png`). Null pro otázky bez obrázku. |
| `source_page` | int | Stránka PDF (1-based), kde se otázka nachází. |
| `source_pdf` | string | Název zdrojového PDF souboru pro audit. |
| `parsed_at` | ISO 8601 | Kdy parser vygeneroval tento záznam. |

## Známé duplicity v PDF MV ČR

| Otázky | Hash sdílí | Příčina |
|---|---|---|
| Q523 a Q529 | ✅ | PDF obsahuje dva identické zápisy (chyba vydavatele) |
| Q587 a Q590 | ✅ | Dtto |

Parser tyto duplicity detekuje (sdílejí stejný hash-ID). Pro uživatele to znamená,
že v Marathon režimu narazí na „stejnou" otázku dvakrát — ale SRS/statistiky je
považují za jeden záznam.

## Obrázky v `../images/`

- **71 otázek** (~ 8 % katalogu) má přiřazený obrázek, typicky fotografie zbraně
  s vyznačenými čísly částí (1, 2, 3, …).
- Obrázky jsou **rasterizované výřezy stránek PDF** přes `PyMuPDF.get_pixmap(clip=rect, dpi=170)`.
  Metoda `extract_image(xref)` by vrátila jen base JPEG **bez overlay čísel** — proto rasterizace.
- Název souboru = SHA-1 hash obsahu otázky (stejný jako `id` v JSON).

## Regenerace obsahu (pro maintainery)

Když MV ČR vydá novou verzi PDF:

```bash
# 1. Stáhni nové PDF z https://www.mvcr.gov.cz/...
# 2. Ulož do kořene repa pod názvem MV-Soubor_testovych_otazek_*.pdf
# 3. Regeneruj:
make parse

# 4. Ověř počty (~837 otázek, ~71 obrázků, 0 nedořešených)
make test

# 5. Commit změn
git add data/questions.json images/
git commit -m "data: update z PDF MV ČR verze YYYYMMDD"
git push
```

Stabilní hash-ID znamená, že existující `stats.db` uživatelů **zůstane platný**
— otázky, které zůstaly beze změny, se spárují podle hashe.

## Statistiky aktuálního `questions.json`

| Metrika | Hodnota |
|---|---:|
| Celkem otázek | 837 |
| S obrázkem | 71 |
| Právo | 561 |
| Prováděcí předpisy | 48 |
| Jiné předpisy | 39 |
| Nauka o zbraních a střelivu | 151 |
| Zdravotnické minimum | 38 |
| Duplicitní otázky | 2 skupiny (Q523/Q529, Q587/Q590) |
| Zdrojová verze PDF | 15. 12. 2025 |
