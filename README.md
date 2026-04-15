# Pro Zbroják

> **Český trenažér testových otázek pro zkoušku odborné způsobilosti (ZOZ) k vydání zbrojního průkazu.**
> Dle **zákona č. 90/2024 Sb.** a **nařízení vlády č. 238/2025 Sb.** (oba účinné od 1. 1. 2026).

Oficiální katalog MV ČR **837 otázek** (z toho 71 s obrázkem zbraně), 6 režimů učení, spaced repetition (FSRS), simulace zkoušky, export pro AI vysvětlení.

**Vše běží lokálně** (127.0.0.1:8080) — žádný cloud, žádný účet, žádná data neopouštějí tvůj počítač.

---

## Co aplikace umí

- 🏃 **Marathon** — projdi celý katalog 837 otázek; pozice se pamatuje mezi restarty.
- 🧠 **Denní review (SRS)** — algoritmus FSRS ti ukazuje otázky přesně tehdy, kdy je budeš zapomínat.
- 🎯 **Lekce z chyb** — opakuje jen otázky, kde jsi chyboval.
- 🎓 **Mastery podle oblasti** — trénuj oblast (právo / zbraně / zdrávo) dokud nezvládneš ≥ 90 %.
- 📝 **Simulace zkoušky** — 30 otázek / 40 min; úroveň Standardní (≥ 26/30) nebo Rozšířené (≥ 28/30).
- 🎲 **Náhodné procvičování** — volný kvíz režim.
- 📤 **Export pro AI** — vygeneruje Markdown pro vložení do Claude Code / ChatGPT s promptem na vysvětlení s citacemi zákona.

---

## Instalace

### Požadavky
- **Python 3.11+** (`python3 --version`)
- **Git**

### macOS — dvojklikem

```bash
git clone https://github.com/Srbino/pro-zbrojak.git
cd pro-zbrojak
chmod +x start.command
```

Pak ve **Finderu dvojklik na `start.command`** → otevře Terminál, nainstaluje závislosti (jen poprvé) a spustí aplikaci. Prohlížeč se otevře sám.

### Windows — dvojklikem

Po klonu repa **dvojklik na `start.bat`** v Exploreru.

### Linux / pokročilí

```bash
git clone https://github.com/Srbino/pro-zbrojak.git
cd pro-zbrojak
make install && make run
```

---

## Klávesové zkratky

**V kvízu:**
- `1` `2` `3` nebo `a` `b` `c` — odpověď
- `Enter` / `mezera` — další otázka
- `F` — bookmark

**SRS rating:**
- `1` Znovu (za < 10 min) · `2` Těžké (~1 den) · `3` Dobré (pár dní) · `4` Snadné (týden+)

---

## Pro maintainery — regenerace obsahu

Otázky (`data/questions.json`) a obrázky (`images/`) jsou **přímo v repu**. Uživatel nic nestahuje.

Když MV ČR vydá novou verzi PDF:

```bash
# 1. Stáhni nové PDF z https://www.mvcr.gov.cz/
#    Ulož do kořene repa pod názvem MV-Soubor_testovych_otazek_*.pdf
# 2. Regeneruj:
make parse
# 3. Ověř + commit
make test
git add data/questions.json images/
git commit -m "data: update PDF MV ČR verze YYYYMMDD"
```

Víc v [`data/README.md`](data/README.md).

---

## Licence

**MIT** pro kód ([LICENSE](LICENSE)). Otázky pocházejí z oficiálního PDF MV ČR a zůstávají v držení vydavatele.

---

## ⚠️ Disclaimer

Tato aplikace je **studijní pomůcka**, **není oficiálním zdrojem**. Pro přípravu vždy konzultuj:

- [Zákon č. 90/2024 Sb., o zbraních a střelivu](https://www.zakonyprolidi.cz/cs/2024-90)
- [Nařízení vlády č. 238/2025 Sb.](https://www.zakonyprolidi.cz/cs/2025-238)
- [MV ČR — Zbraně, střelivo a munice](https://www.mvcr.gov.cz/clanek/zbrane-strelivo-munice-a-bezpecnostni-material.aspx)

Autor neodpovídá za chyby v parsování, změny v legislativě ani za neúspěch u zkoušky.

---

<sub>Pro Zbroják · v0.3.0 · autor [Pavel Srba](mailto:srba@unify.cz)</sub>
