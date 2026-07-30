# Prompt pro generování podcastu

Zkopíruj text níže a vlož ho jako zadání k souboru z `docs/studium/podcast-po-50/`.
Nahraď `{OKRUH}` a `{POČET}` podle hlavičky toho souboru — třeba
*Nauka o zbraních a střelivu — díl 2/4, otázky 687–724* a *38*.

---

## Plná verze

```
Udělej podcast v češtině pro člověka, který se učí na zkoušku odborné
způsobilosti k vydání zbrojního průkazu. Zdrojem je přiložený soubor:
{OKRUH}, celkem {POČET} otázek.

ZAČNI ROVNOU. Žádný pozdrav, žádné představování, žádné „dnes se podíváme
na zajímavé téma". První věta patří první otázce.

PROJDI VŠECHNY OTÁZKY. Všech {POČET}, jednu po druhé, v pořadí, v jakém
jsou v souboru. Žádnou nevynechej, žádné dvě neslučuj, nikde neříkej
„a podobně to platí i u dalších" ani „zbytek je obdobný". Když ti přijde,
že se otázka opakuje, přesto ji projdi — u zkoušky přijde taky.

U KAŽDÉ OTÁZKY udělej tohle a nic víc:
  1. řekni její číslo a přečti zadání,
  2. řekni správnou odpověď,
  3. VYSVĚTLI JI LIDSKY — proč to tak je, co to znamená v praxi, na co si
     dát pozor. Ne citaci paragrafu jinými slovy, ale to, co za tím stojí:
     čemu má pravidlo zabránit, koho chrání, kdy se použije.
  4. je-li u otázky uvedený paragraf, zmiň ho jednou větou — ale výklad
     musí dávat smysl i tomu, kdo si zákon neotevře.

DÉLKA: u každé otázky zhruba tři až šest vět. Radši stručně a ke věci než
dlouhé odbočky. Celý díl má být souvislý, ne seznam odrážek.

NEVYMÝŠLEJ SI. Drž se toho, co je v souboru. Když k otázce není uvedený
paragraf ani vysvětlení, řekni jen to, co plyne ze znění otázky a odpovědi,
a nedoplňuj čísla, lhůty ani podmínky, které tam nejsou.

POZOR: v souboru jsou schválně jen SPRÁVNÉ odpovědi. Nesprávné varianty
nevymýšlej ani nenaznačuj — posluchač si je jinak zapamatuje.

Na konci žádné shrnutí ani rozloučení. Poslední otázka, a konec.
```

---

## Krátká verze (když nástroj bere jen pár řádků)

```
Podcast v češtině, příprava na zbrojní průkaz. Zdroj: přiložený soubor
({OKRUH}, {POČET} otázek). Začni rovnou první otázkou, bez úvodu.
Projdi VŠECH {POČET} otázek jednu po druhé, žádnou nevynechej ani neslučuj.
U každé: číslo, zadání, správná odpověď a hlavně LIDSKÉ VYSVĚTLENÍ — proč
to tak je a na co si dát pozor, tři až šest vět. Nic si nevymýšlej nad
rámec souboru. Nesprávné odpovědi nezmiňuj. Bez závěrečného shrnutí.
```

---

## Proč je to napsané takhle

| požadavek | proč |
|---|---|
| „Projdi všech {POČET}" s konkrétním číslem | Nástroje rády vyberou „to nejzajímavější" a zbytek shrnou. Číslo jim to znemožní odbýt. |
| „Žádnou neslučuj" | V katalogu je 147 otázek s téměř shodným zadáním. Bez tohohle je model spojí do jedné. |
| „Ne citaci jinými slovy" | Bez toho jen převypráví paragraf — a to je přesně to, čemu člověk nerozumí. |
| „Nevymýšlej si" | Lhůty a počty kusů jsou u zkoušky rozhodující. Domyšlený údaj je horší než žádný. |
| „Nesprávné odpovědi nezmiňuj" | Při poslechu není vidět, která byla ta špatná — snadno se zapamatuje ta nesprávná. |
| „Bez úvodu a závěru" | U 19 dílů je opakovaný obal jen ztracený čas. |
