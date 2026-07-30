# Dokumentace

## Pro studium

| | |
|---|---|
| [Přehled o zkoušce ZOZ](o-zkousce.md) | Teorie, praktická část, postupy podle vyhlášky. |
| [Studijní materiály](studium/) | Generované z katalogu — příručka, podcast, okruhy, klíč odpovědí. |

## Ověření obsahu (publikováno přes GitHub Pages)

| soubor | adresa |
|---|---|
| `index.html` | https://srbino.github.io/pro-zbrojak/ |
| `prirucka.html` | https://srbino.github.io/pro-zbrojak/prirucka.html |
| `otazky.html` | https://srbino.github.io/pro-zbrojak/otazky.html |
| `porovnani.html` | https://srbino.github.io/pro-zbrojak/porovnani.html |

Generují je `scripts/gen_questions_html.py` a `scripts/gen_comparison_html.py`.
Jsou to **veřejné adresy odkazované z README** — když se soubory přesunou,
odkazy se rozbijí.

## Ostatní

- [PRD.md](PRD.md) — zadání produktu.

## Co v repozitáři není

Zdrojová PDF (soubor otázek MV ČR, znění zákona) verzovaná nejsou — jsou
veřejně ke stažení a mají 3 MB na kus. Kdo je potřebuje:

| soubor | kam | k čemu |
|---|---|---|
| `MV-Soubor_testovych_otazek_…pdf` | `docs/` | `make parse`, `make test-data` |
| `zakon_90_2024.txt` | `data/` | `make okruhy`, `make validate-zakon` |

Bez nich aplikace i studijní materiály fungují normálně — jen se nedá
přegenerovat katalog a **testy porovnávající katalog se zdrojem se přeskočí**.
