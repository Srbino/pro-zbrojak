# Pro Zbroják

> **Český trenažér testových otázek pro zkoušku odborné způsobilosti (ZOZ) k vydání zbrojního průkazu.**
> Dle **zákona č. 90/2024 Sb.** a **nařízení vlády č. 238/2025 Sb.** (oba účinné od 1. 1. 2026).

Oficiální katalog MV ČR **837 otázek** (z toho 71 s obrázkem zbraně), 6 režimů učení, spaced repetition (FSRS), simulace zkoušky, export pro AI vysvětlení.

**Vše běží lokálně** (127.0.0.1:8080) — žádný cloud, žádný účet, žádná data neopouštějí tvůj počítač.

> ## 📚 [Příručka ke zkoušce ZOZ →](https://srbino.github.io/pro-zbrojak/prirucka.html)
> **Přehledně, bod po bodu: co zkouší komisař · jaké zbraně tam budou · teorie · střelba · peníze · postup.**
> Ověřeno proti zákonu č. 90/2024 Sb. a NV č. 238/2025 Sb.
> · [online rozcestník](https://srbino.github.io/pro-zbrojak/) · [podrobná verze s paragrafy](docs/o-zkousce.md)

---

## ✅ Ověření obsahu ([online přehled](https://srbino.github.io/pro-zbrojak/))

Všech **837 správných odpovědí je ověřeno proti oficiálnímu PDF MV ČR** (nezávislou
detekcí šedého zvýraznění) — **837/837 sedí**. K nahlédnutí:

- **[Porovnání odpovědí: PDF vs aplikace](https://srbino.github.io/pro-zbrojak/porovnani.html)** — u každé otázky vedle sebe odpověď z PDF a z aplikace.
- **[Přehled všech 837 otázek](https://srbino.github.io/pro-zbrojak/otazky.html)** — se správnou odpovědí, hledáním a filtrem oblastí.

Ověření je zabudované jako test (`tests/test_all_answers_vs_pdf.py`), takže hlídá i budoucí aktualizace.

**Druhá, nezávislá kontrola — proti plnému znění zákona** (`make validate-zakon`):
skript `scripts/validate_vs_zakon.py` rozseká zák. č. 90/2024 Sb. až na jednotlivé
odstavce, písmena a body a u každé otázky měří, se kterou z možností sdílí zákon
nejdelší doslovnou frázi. Otázky MV ČR jsou totiž z velké části opisy znění zákona
a distraktory vznikají vsunutím či záměnou slova — což souvislou shodu zlomí.
Z 273 otázek, kde má metoda dost podkladu, podpírá zákon označenou odpověď
u 231 (**85 %**); u zbytku si skript netroufá rozhodnout a řekne to (výčty, negace,
parafráze). **Není to právní posouzení** — je to ukazatel, kam se podívat.

Vedlejší produkt je užitečnější než samotná kontrola:

- **Odkaz do e-Sbírky** — u doložených otázek zná aplikace přesné ustanovení
  (`§ 7 písm. b) bod 2`) a proklikne přímo na jeho znění na
  [e-Sbírce MV ČR](https://e-sbirka.gov.cz/sb/2024/90/2026-01-01#par_7-pism_b-bod_2).
  **Znění zákona v repu nedržíme** — zdrojem pravdy zůstává stát, my vedeme jen
  otázky a odkaz (`data/law_refs.json`, generuje `scripts/gen_law_links.py`).
  Odkazy nejsou hádané: skript sestaví ELI cestu, stáhne k ní metadata z
  otevřených dat e-Sbírky a zapíše jen ta, u kterých úřad potvrdí totéž
  označení. Co neprojde, odkaz nedostane.
- **Rozbor chytáků** (`--chytaky`) — porovná distraktory se zněním zákona po
  slovech a ukáže, čím přesně matou. Např. u otázky #4 stačí ministerstvu vsunout
  dvě slova: *„palná zbraň, plynová zbraň, **chladná zbraň**, a další zařízení…"*.

📄 **[Kompletní přehled o zkoušce ZOZ](docs/o-zkousce.md)** — teorie, praktická část, postupy podle
přílohy č. 2 NV 238/2025 Sb., střelnice, poplatky, časté mýty — vše s odkazy na paragrafy.

---

## Co aplikace umí

- 🏃 **Marathon** — projdi celý katalog 837 otázek; pozice se pamatuje mezi restarty.
- 🧠 **Denní review (SRS)** — algoritmus FSRS ti ukazuje otázky přesně tehdy, kdy je budeš zapomínat.
- ⚠️ **Chytáky** — 309 otázek, kde se dá snadno šlápnout vedle: drobně upravená odpověď, zápor v zadání, nebo dvojče se skoro stejným zadáním. Po odpovědi ti ukáže, kde přesně je nastraženo.
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
chmod +x bin/start.command
```

Pak ve **Finderu dvojklik na `bin/start.command`** → otevře Terminál, nainstaluje závislosti (jen poprvé) a spustí aplikaci. Prohlížeč se otevře sám.

### Windows — dvojklikem

Po klonu repa **dvojklik na `bin\start.bat`** v Exploreru.

### Linux / pokročilí

```bash
git clone https://github.com/Srbino/pro-zbrojak.git
cd pro-zbrojak
make install && make run
```

---

## Klávesové zkratky

**V kvízu:**
- `1` `2` `3` nebo `a` `b` `c` — **vybrat** odpověď (jde překlikat, nic se neodešle)
- `Enter` / `mezera` — vyhodnotit výběr, podruhé další otázka
- `F` — bookmark

> Odpověď se odesílá až potvrzením („Vyhodnotit"). Samotný klik do možnosti jen
> vybírá, takže omylem — třeba při označování textu myší — nejde nic zkazit.

**SRS rating:**
- `1` Znovu (za < 10 min) · `2` Těžké (~1 den) · `3` Dobré (pár dní) · `4` Snadné (týden+)


---

## Chytáky

U zkoušky se nepadá na tom, že člověk látku nezná, ale že přehlédne jedno slovo:

| správně | chyták |
|---|---|
| **regulovanou** součástí zbraně | **ne**regulovanou součástí zbraně |
| v posledních **3** letech | v posledních **5** letech |
| R1, R2, S1 a S2 | R1, R2, **R3, R4,** S1 a S2 |

Past ale nebývá jen v odpovědích. Režim **Chytáky** (`/traps`) hledá na třech
místech a po odpovědi ukáže rozbor:

| kde | co to je | otázek |
|---|---|---|
| v odpovědích | distraktor sdílí se správnou odpovědí ≥ 60 % slov a liší se nanejvýš třemi zásahy | 101 |
| v zadání | zápor („se **ne**považuje"), výjimka („s výjimkou", „kromě"), absolutní tvrzení („vždy", „pouze") | 109 |
| mezi otázkami | **dvojčata** — skoro stejné zadání, jiná správná odpověď (`…nepatří` × `…patří`, „selhání" × „zádržka") | 147 |

Dohromady **309 z 837** (s překryvy). Seznam generuje `scripts/gen_traps.py`
(`make traps`) z katalogu; **znění zákona k tomu nepotřebuje**, takže běží i bez
zdrojových PDF.

Slova v zadání jsou kurátorovaná, ne regulární výraz: hledat `ne\w+` by chytalo
i „nebo" a „nebezpečí", a `mimo` je v katalogu 53× z 55 jako „mimo jiné", což
výjimka není. Šablonovitá zadání („Vyberte správné tvrzení", 11 otázek) se mezi
dvojčata nepočítají — tam není co splést.

---

## Prohazování možností

Možnosti se zobrazují v **jiném pořadí, než jsou v katalogu** — jinak by se místo
látky člověk naučil polohu („správně bývá b)"), což je u zkoušky k ničemu.

Děje se to **výhradně při vykreslování** (`src/ui/shuffle.py`). Soubor
`data/questions.json` si drží pořadí přesně podle oficiálního PDF MV ČR a nikdy se
nepřepisuje — stojí na něm ověření odpovědí proti PDF i proti zákonu. Do statistik,
SRS a vyhodnocení zkoušky se vždycky zapisuje **původní písmeno z katalogu**;
hlídá to `tests/test_shuffle.py`.

Pořadí je odvozené z dvojice uživatel + otázka a v rámci dne stálé (aby se
možnosti nepřeskládaly uprostřed odpovídání), přes den se otočí. Vypnout se dá
přes `PRO_ZBROJAK_SHUFFLE=0`.

---

## Struktura repozitáře

```
app.py                  vstupní bod aplikace
bin/                    spouštěče (start.command, start.bat, run.sh, run.bat)
data/                   questions.json, law_refs.json, traps.json, vyklady*.json
docs/                   dokumentace + ověřovací stránky (GitHub Pages)
  studium/              generované materiály: příručka, podcast, okruhy, klíč
images/                 obrázky k otázkám (q<číslo>.png)
scripts/                generátory a validátory (gen_*.py, validate_*.py)
src/                    aplikace — db/, learning/, parser/, ui/, export/
tests/                  testy
parse_pdf.py            parser oficiálního PDF → questions.json + images/
```

Co je **generované** a nemá se editovat ručně: `docs/studium/**`,
`docs/otazky.html`, `docs/porovnani.html`, `data/law_refs.json`,
`data/traps.json`. Ručně psaný text patří do `data/vyklady.json`
a `data/vyklady-okruhy.json`, odkud se do materiálů vkládá.

---

## Čtecí JSON API

Aby si aktuální postup mohl vzít nástroj, ne jen člověk — typicky pustit na
svoje výsledky AI a nechat si poradit, co doučit.

**API je vypnuté**, dokud nenastavíš `PRO_ZBROJAK_API_TOKEN`. Zapomenutá
proměnná tedy neznamená otevřená data, ale nedostupné API.

```bash
export TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"

curl -H "Authorization: Bearer $TOKEN" https://…/api/kontext
```

| endpoint | co vrací |
|---|---|
| `/api` | rozcestník s popisem endpointů |
| `/api/stav` | úspěšnost celkem i po oblastech, série, kolik čeká na review |
| `/api/chyby` | otázky, kde chybuješ — se zněním, správnou odpovědí a paragrafem |
| `/api/kontext` | vše podstatné v jednom balíku, i s pokynem pro AI |

Parametry: `?email=` (čí data, výchozí první admin), `?limit=` (kolik otázek).

Token jde poslat i jako `?token=…` kvůli nástrojům, které neumí hlavičky —
ale zapíše se do logů proxy, takže hlavička je lepší. Všechny endpointy jsou
**jen ke čtení**, žádný nic nemění.

---

## Známé dluhy

- **E-maily v git historii.** Sedm souborů `.nicegui/storage-user-*.json`
  s 19 e-maily se do historie dostalo dřív. Ze sledování jsou odebrané
  a `.gitignore` je drží venku, ale z historie zmizí až jejím přepsáním
  (`git filter-repo`) a force-pushem.
- **Reset v Nastavení** maže jen řádky přihlášeného uživatele, ale tváří se
  jako „smazat vše" (`tests/test_ui_interactions.py::test_settings_reset_actually_deletes_data`).
- **Dialog se zkratkami** se v testu hledá na `/settings`, kde není
  (`test_help_dialog_opens_on_header_click`).
- **Mapování na zákon** má jen 224 z 837 otázek. Zbytek je bez ověřeného
  paragrafu, takže u nich studijní materiály nemají co vysvětlovat.

---

## Pro maintainery — regenerace obsahu

Otázky (`data/questions.json`) a obrázky (`images/`) jsou **přímo v repu**. Uživatel nic nestahuje.

Když MV ČR vydá novou verzi PDF:

```bash
# 1. Stáhni nové PDF z https://www.mvcr.gov.cz/
#    Ulož do docs/ pod názvem MV-Soubor_testovych_otazek_*.pdf
# 2. Regeneruj:
make parse
# 3. Ověř proti zdroji (odpovědi, textace za písmeny, obrázky) + commit
make test-data
make test
git add data/questions.json images/
git commit -m "data: update PDF MV ČR verze YYYYMMDD"
```

Zdrojová PDF **v repu nejsou** — mají 3 MB a jsou veřejně ke stažení.
Důsledek: testy porovnávající katalog se zdrojem se bez nich **samy přeskočí**,
takže v CI neběží. Lokálně je pouští `make test-data`, které na chybějící PDF
upozorní místo tichého přeskočení.

Víc v [`data/README.md`](data/README.md) a [`docs/README.md`](docs/README.md).

---

## Nasazení na server (Coolify / Docker)

Aplikaci lze vedle lokálního dvojkliku provozovat i jako kontejner — např. na
**Coolify** (Proxmox homelab). Obsah (837 otázek + obrázky) je součástí image,
takže po startu nic nestahuje.

### Coolify

1. **New Resource → Public Repository → Docker Compose**, ukaž na tento repozitář (`docker-compose.yaml`).
2. Coolify sám doplní doménu, HTTPS (Traefik) i health-check.
3. **Persistentní volume** `pro-zbrojak-state` (`/state`) drží progres uživatele
   (SQLite `data/stats.db` + exporty) přes redeploy — je už v compose souboru.

### Přímo přes Docker

```bash
docker build -t pro-zbrojak .
docker run -d --name pro-zbrojak -p 8080:8080 \
  -v pro-zbrojak-state:/state pro-zbrojak
# → http://SERVER:8080   (health: /healthz)
```

### Konfigurace (env)

| Proměnná | Výchozí | Popis |
|---|---|---|
| `HOST` | `127.0.0.1` (lokálně) / `0.0.0.0` (Docker) | Rozhraní, na kterém se poslouchá |
| `PORT` | `8080` | Port aplikace |
| `SHOW` | `true` / `false` (Docker) | Otevřít systémový prohlížeč po startu |
| `PRO_ZBROJAK_STATE_DIR` | kořen repa / `/state` (Docker) | Kam se ukládají DB + exporty |
| `STORAGE_SECRET` | dev fallback | Podpis session cookie — **mimo localhost povinný**, jinak se aplikace nespustí |
| `PRO_ZBROJAK_ADMINS` | prázdný | Čárkami oddělení admini (vidí `/admin`). Prázdné = nikdo |
| `PRO_ZBROJAK_DISPLAY_NAMES` | prázdný | Přezdívky: `mail=Jméno,mail2=Jiné`. Bez nich část e-mailu před `@` |
| `PRO_ZBROJAK_LOGIN_CODE` | prázdný | Volitelný sdílený kód pro LAN login |
| `PRO_ZBROJAK_API_TOKEN` | prázdný | Token pro čtecí JSON API. **Prázdný = API vypnuté** |

Viz [`.env.example`](.env.example).

**Vygeneruj si vlastní `STORAGE_SECRET`:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Aplikace odmítne nastartovat s výchozím tajemstvím, pokud poslouchá jinde než
na localhostu — to tajemství je veřejné ve zdrojácích a kdokoli by si s ním
podepsal cizí session.

### Více uživatelů (multi-user)

Aplikace je **multi-user** — každý má vlastní izolovaný progres (statistiky, SRS,
bookmarky, simulace). Identita se bere automaticky z **Cloudflare Access** hlavičky
`Cf-Access-Authenticated-User-Email` (přihlášení přes e-mailový kód, žádná hesla).
Bez Cloudflare Access (např. v LAN) appka nabídne jednoduchý fallback login.
Admini (viz `PRO_ZBROJAK_ADMINS`) mají na `/admin` přehled všech uživatelů.

> ⚠️ **Data jsou single-user.** Aplikace vede jednu společnou databázi progresu.
> Při vystavení více lidem sdílejí všichni stejné statistiky a SRS. Pro veřejné
> nasazení dej appku za autentizaci (Coolify Basic Auth / privátní síť).

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

<sub>Pro Zbroják · v0.4.0 · autor [Pavel Srba](mailto:srba@unify.cz)</sub>
