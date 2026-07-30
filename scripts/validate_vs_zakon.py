#!/usr/bin/env python3
"""
Mechanické ověření otázek proti plnému znění zákona č. 90/2024 Sb.

CO TO DĚLÁ (a co ne)
--------------------
Skript NEROZUMÍ právu. Dělá čistě lexikální práci, ale takovou, která má výpovědní
hodnotu, protože otázky MV ČR jsou z velké části parafráze (často doslovné opisy)
textu zákona:

  1. Rozseká zákon (§ 1 … § 152 + přílohy č. 1–3) až na jednotlivé odstavce,
     písmena a body — celý § je na porovnávání moc hrubé síto.
  2. Pro každou otázku najde kandidátní ustanovení — dotaz se skládá ze znění otázky
     A VŠECH možností dohromady, takže výběr ustanovení není ovlivněn tím, která
     odpověď je označená jako správná.
  3. U každé možnosti (A/B/C…) změří NEJDELŠÍ DOSLOVNOU FRÁZI, kterou sdílí
     s textem těch ustanovení. To je hlavní signál: otázky MV ČR jsou stavěné tak,
     že správná odpověď je opis znění zákona a distraktory jsou jeho drobné
     úpravy (vsunuté/vyměněné slovo). Pouhý překryv slov je nerozliší — obsahují
     stejná slova — ale délka souvislé shody ano.
  4. Ověří, jestli nejlépe podepřená možnost je právě ta, kterou má aplikace
     označenou jako správnou.
  5. Navíc vytáhne ze správné odpovědi tvrdá fakta (lhůty, věky, ráže, odkazy na §,
     kategorie zbraní) a zkontroluje, že se objevují v nalezeném paragrafu.

Kde metoda nemá dost podkladu — krátké možnosti („střelivo."), otázky na
nepříslušnost („…mezi regulované součásti NEpatří"), výčty — se skript záměrně
NEVYJADŘUJE a vrátí NEROZHODNUTO. Validátor, který hádá, je horší než žádný.

Verdikt tedy NEZNAMENÁ „odpověď je právně správná". Znamená: „znění zákona, které
k této otázce patří, podpírá právě tuhle možnost víc než ostatní". Případy NESHODA
a K OVĚŘENÍ jsou seznam míst, kam se má člověk podívat — ne důkaz chyby.

Použití
-------
    python3 scripts/validate_vs_zakon.py                  # prvních 20 otázek
    python3 scripts/validate_vs_zakon.py --range 1-100
    python3 scripts/validate_vs_zakon.py --all --only-problems
    python3 scripts/validate_vs_zakon.py --all --out docs/validace-zakon.md
    python3 scripts/validate_vs_zakon.py --all --chytaky   # čím distraktor mění zákon

Vyžaduje `pdftotext` (poppler).  macOS: brew install poppler
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZAKON_PDF = ROOT / "docs" / "Zákon 90_2024 Sb. (1.1.2026).pdf"
ZAKON_TXT = ROOT / "data" / "zakon_90_2024.txt"  # cache extrakce
QUESTIONS = ROOT / "data" / "questions.json"

# Prahy — vyladěné tak, aby „MIMO ZÁKON" chytalo otázky z nauky o zbraních
# a zdravotního minima, které v zákoně o zbraních prostě nejsou.
# Změřeno na katalogu (F-míra proti jednotkám): oblast „pravo" má p10 = 0.27
# a medián 0.45, kdežto nauka o zbraních medián 0.14 a zdravotní minimum 0.10.
# Práh je odděluje, ale sám o sobě by odřízl i část právních otázek — proto platí
# jen tehdy, když k tomu chybí i doslovná citace zákona.
MIN_SECTION_SCORE = 0.25
TOP_SECTIONS = 3  # kolik jednotek zákona tvoří důkazní materiál
ANCHOR_CANDIDATES = 25  # z kolika jednotek se vybírá odkaz do zákona pro výpis

# Aby se skript vyjádřil, musí vítězná možnost sdílet se zákonem souvislou frázi
# aspoň MIN_WIN_PHRASE slov a mít nad druhou v pořadí náskok MIN_PHRASE_MARGIN
# slov. Jinak → NEROZHODNUTO.
MIN_WIN_PHRASE = 5
MIN_PHRASE_MARGIN = 2


# --------------------------------------------------------------------------
# Normalizace češtiny
# --------------------------------------------------------------------------

STOPWORDS = {
    "a", "aby", "ale", "ani", "ano", "asi", "az", "bez", "bude", "budou", "by",
    "byl", "byla", "byli", "bylo", "byt", "ci", "clen", "co", "coz", "dalsi",
    "do", "ho", "i", "jak", "jako", "je", "jeho", "jej", "jeji", "jejich", "jen",
    "jestlize", "ji", "jine", "jinak", "jiz", "jsem", "jsi", "jsme", "jsou",
    "jste", "k", "kde", "kdo", "kdy", "kdyz", "ke", "ktera", "ktere", "kteri",
    "kterou", "ktery", "kteryc", "ku", "ma", "mai", "me", "mezi", "mi", "mit",
    "mne", "mnou", "muze", "muzeme", "my", "na", "nad", "nam", "napr", "nas",
    "nasi", "ne", "nebo", "nebyl", "nejsou", "nekolik", "nekter", "nemuze",
    "neni", "nez", "nic", "nove", "novy", "nyni", "o", "od", "on", "ona", "ono",
    "pak", "po", "pod", "podle", "pokud", "pouze", "pouzit", "pred", "pres",
    "pri", "pro", "proc", "proto", "prave", "pta", "s", "se", "si", "sice",
    "sve", "svuj", "svych", "svym", "ta", "tak", "take", "takze", "tam", "tato",
    "te", "tedy", "tento", "teto", "tim", "timto", "to", "tohle", "toho",
    "tohoto", "tom", "tomto", "tomuto", "tu", "tuto", "ty", "tyto", "u", "uz",
    "v", "vam", "vas", "vase", "ve", "vice", "vsak", "vsech", "vsechen",
    "vsechny", "vy", "z", "za", "zda", "ze", "zpet",
}

# Číslovky slovy → číslice. Zákon píše lhůty číslicemi („5 let"), otázky někdy
# slovy („pěti let"), takže obě strany srovnáme na číslice.
NUMERALS = {
    "jednoho": 1, "jedne": 1, "jeden": 1, "jedna": 1, "jednim": 1,
    "dvou": 2, "dva": 2, "dve": 2, "dvema": 2,
    "trech": 3, "tri": 3, "tremi": 3,
    "ctyr": 4, "ctyri": 4, "ctyrmi": 4,
    "peti": 5, "pet": 5,
    "sesti": 6, "sest": 6,
    "sedmi": 7, "sedm": 7,
    "osmi": 8, "osm": 8,
    "deviti": 9, "devet": 9,
    "deseti": 10, "deset": 10,
    "dvanacti": 12, "dvanact": 12,
    "patnacti": 15, "patnact": 15,
    "osmnacti": 18, "osmnact": 18,
    "dvaceti": 20, "dvacet": 20,
    "jednadvaceti": 21, "jednadvacet": 21,
    "tricet": 30, "triceti": 30,
    "sedesat": 60, "sedesati": 60,
    "devadesat": 90, "devadesati": 90,
    "sta": 100, "sto": 100,
}


def strip_diacritics(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def tokenize(text: str) -> list[str]:
    """Slova bez diakritiky, malými písmeny, číslovky slovy → číslice.

    Alfanumerické kódy drží pohromadě („R1", „R2", „PO", „12a") — kategorie zbraní
    jsou v těchhle otázkách klíčové a rozpad na „r" + „1" by je zahodil.
    """
    flat = strip_diacritics(text.lower())
    raw = re.findall(r"[a-z]+\d+|\d+[a-z]*|[a-z]+", flat)
    return [str(NUMERALS[t]) if t in NUMERALS else t for t in raw]


def stem(token: str) -> str:
    """Hrubý stemming pro češtinu — ořez na prefix. Sjednotí pády a čísla
    („zbrane"/"zbrani"/"zbran" → „zbran"). Číslice necháváme celé."""
    if token.isdigit():
        return token
    return token[:6]


def content_stems(text: str) -> list[str]:
    return [stem(t) for t in tokenize(text) if t not in STOPWORDS and len(t) > 1]


# --------------------------------------------------------------------------
# Načtení zákona
# --------------------------------------------------------------------------


@dataclass
class LawSection:
    label: str  # „§ 12" nebo „Příloha č. 1"
    heading: str  # nadpis paragrafu, pokud v PDF je
    part: str  # ČÁST PRVNÍ / …
    text: str
    stems: Counter = field(default_factory=Counter)
    stem_set: set[str] = field(default_factory=set)
    norm: str = ""  # normalizovaný text pro hledání frází


def extract_law_text() -> str:
    """PDF → text (přes pdftotext), s cache v data/."""
    if ZAKON_TXT.exists() and ZAKON_TXT.stat().st_mtime >= ZAKON_PDF.stat().st_mtime:
        return ZAKON_TXT.read_text(encoding="utf-8")

    if not ZAKON_PDF.exists():
        sys.exit(f"CHYBA: chybí PDF zákona: {ZAKON_PDF}")
    if not shutil.which("pdftotext"):
        sys.exit("CHYBA: chybí `pdftotext` (poppler). macOS: brew install poppler")

    subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(ZAKON_PDF), str(ZAKON_TXT)],
        check=True,
    )
    return ZAKON_TXT.read_text(encoding="utf-8")


PARAGRAPH_RE = re.compile(r"^§\s?(\d+[a-z]?)$")
ANNEX_RE = re.compile(r"^(Příloha č\.\s*\d+)")
PART_RE = re.compile(r"^ČÁST\s+\w+")


def parse_law(text: str) -> list[LawSection]:
    """Rozseká zákon na bloky podle „§ N" a „Příloha č. N".

    Pozn.: pdftotext lepí na začátek řádku za koncem stránky znak \f, proto se
    nejdřív nahrazuje za nový řádek — jinak by se ztratil každý §, který začíná
    novou stránku.
    """
    lines = text.replace("\f", "\n").split("\n")

    sections: list[LawSection] = []
    part = ""
    pending_heading = ""  # nadpis stojí v zákoně nad značkou §
    current: LawSection | None = None

    for i, raw in enumerate(lines):
        line = raw.strip()

        if PART_RE.match(line):
            part = line
            if i + 1 < len(lines):
                part = f"{line} — {lines[i + 1].strip()}"
            pending_heading = ""
            continue

        m_par = PARAGRAPH_RE.match(line)
        m_annex = ANNEX_RE.match(line)

        if m_par or m_annex:
            label = f"§ {m_par.group(1)}" if m_par else m_annex.group(1)
            current = LawSection(
                label=label,
                heading=pending_heading if m_par else line,
                part=part,
                text="",
            )
            sections.append(current)
            pending_heading = ""
            continue

        if current is None:
            continue

        current.text += line + "\n"

        # Krátký řádek bez tečky bývá nadpis následujícího paragrafu
        # („Vymezení některých pojmů" nad § 2).
        if line and len(line) < 70 and not line.endswith((".", ",", ";", ":")):
            pending_heading = line
        elif line:
            pending_heading = ""

    for s in sections:
        toks = content_stems(f"{s.heading} {s.text}")
        s.stems = Counter(toks)
        s.stem_set = set(toks)
        s.norm = " ".join(tokenize(f"{s.heading} {s.text}"))

    return sections


# --------------------------------------------------------------------------
# Rozpad paragrafu na jednotky: odstavec → písmeno → bod
# --------------------------------------------------------------------------
#
# Celý § je na porovnávání moc hrubé síto. § 7 („Oprávnění nakládat se zbraněmi")
# má pod sebou písmena podle kategorií a v každém vlastní výčet oprávněných osob:
#
#     Osobou oprávněnou nakládat … je v případě zbraní kategorie
#     a) R1
#        1. držitel zbrojní licence skupiny ZL1,
#        2. …
#     b) R2
#        1. …
#
# Otázka „osobou oprávněnou nakládat se zbraní kategorie R2 není: …" jde rozhodnout
# jedině tak, že se sáhne přesně do písmene b) — v celém § jsou totiž doslova
# všechny nabízené možnosti, jen každá pod jinou kategorií.

ODSTAVEC_RE = re.compile(r"^\((\d+)\)\s+")
PISMENO_RE = re.compile(r"^([a-z])\)\s*")
BOD_RE = re.compile(r"^(\d+)\.\s+")


@dataclass
class LawUnit:
    """Jeden uzel zákona — od celého § až po jednotlivý bod výčtu."""

    label: str  # „§ 7 písm. b) bod 2"
    heading: str  # nadpis §
    part: str  # „ČÁST TŘETÍ — …" (pro sestavení ELI cesty)
    lead: str  # návětí nadřazených úrovní („…je v případě zbraní kategorie / R2")
    text: str  # vlastní text VČETNĚ podřízených úrovní
    depth: int  # 0 = celý §, 1 = odstavec, 2 = písmeno, 3 = bod
    own: str = ""  # jen vlastní text, bez podstromu
    siblings: list[str] = field(default_factory=list)  # texty položek téhož výčtu
    stem_set: set[str] = field(default_factory=set)
    norm: str = ""


def _unit_lines(section: LawSection) -> list[tuple[int, str, str]]:
    """Řádky § → (úroveň, značka, text). Pokračovací řádky se lepí k předchozímu."""
    out: list[tuple[int, str, str]] = []
    for raw in section.text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        for level, rx, fmt in (
            (1, ODSTAVEC_RE, "odst. {}"),
            (2, PISMENO_RE, "písm. {})"),
            (3, BOD_RE, "bod {}"),
        ):
            m = rx.match(line)
            if m:
                out.append((level, fmt.format(m.group(1)), line[m.end():].strip()))
                break
        else:
            if out:  # pokračování zalomeného řádku
                lvl, mark, txt = out[-1]
                out[-1] = (lvl, mark, f"{txt} {line}".strip())
            else:  # text před prvním odstavcem = návětí paragrafu
                out.append((0, "", line))
    return out


def split_units(section: LawSection) -> list[LawUnit]:
    """Vyrobí jednotky na všech úrovních. Text jednotky vždy obsahuje i její
    podstrom, takže odpověď opisující celý výčet sedne na odstavec, kdežto
    odpověď citující jednu položku sedne na ten konkrétní bod."""
    rows = _unit_lines(section)
    root = LawUnit(label=section.label, heading=section.heading, part=section.part,
                   lead="", text="", depth=0)
    units: list[LawUnit] = [root]

    open_units: dict[int, LawUnit] = {0: root}  # naposledy otevřená jednotka na úrovni
    marks: dict[int, str] = {}
    children: dict[int, list[LawUnit]] = {}  # id(rodič) → jeho přímé potomky

    for level, mark, text in rows:
        if level == 0:  # návětí paragrafu
            root.text += " " + text
            root.own += " " + text
            continue

        marks[level] = mark
        for deeper in range(level + 1, 4):  # hlubší úrovně se zavírají
            open_units.pop(deeper, None)
            marks.pop(deeper, None)

        parent = open_units[max(k for k in open_units if k < level)]
        path = " ".join(marks[lv] for lv in sorted(marks) if lv <= level)
        unit = LawUnit(
            label=f"{section.label} {path}",
            heading=section.heading,
            part=section.part,
            lead=f"{parent.lead} / {parent.own}".strip(" /"),
            text=text,
            own=text,
            depth=level,
        )
        units.append(unit)
        children.setdefault(id(parent), []).append(unit)
        open_units[level] = unit

        # text položky se promítne do všech nadřazených úrovní
        for lv, ancestor in open_units.items():
            if lv < level:
                ancestor.text += " " + text

    # sourozenci = ostatní položky téhož výčtu (pod stejným rodičem)
    for group in children.values():
        for unit in group:
            unit.siblings = [u.text for u in group if u is not unit]

    for u in units:
        full = f"{u.heading} {u.lead} {u.text}"
        u.stem_set = set(content_stems(full))
        u.norm = " ".join(tokenize(full))
    return units


def build_units(sections: list[LawSection]) -> list[LawUnit]:
    return [u for s in sections for u in split_units(s)]


def build_idf(units: list[LawUnit]) -> dict[str, float]:
    """IDF přes jednotky — dokumentem je odstavec/písmeno, ne celý §, takže váhy
    líp odlišují běžnou právnickou vatu od pojmů, na které se otázka ptá."""
    n = len(units)
    df: Counter = Counter()
    for u in units:
        df.update(u.stem_set)
    # Slova, která nejsou v zákoně vůbec, dostanou nejvyšší váhu (idf pro df=0).
    return {t: math.log(n / (1 + c)) + 1.0 for t, c in df.items()}


DEFAULT_IDF = 4.0


# --------------------------------------------------------------------------
# Skórování
# --------------------------------------------------------------------------


# Váha úplnosti proti přesnosti při výběru jednotky. β > 1 upřednostňuje úplnost
# (aby se našel celý odstavec, když odpověď opisuje celý výčet), ale ne natolik,
# aby vždy vyhrál největší blok.
FSCORE_BETA = 1.5


def unit_score(query_stems: list[str], unit: LawUnit, idf: dict[str, float]) -> float:
    """F-míra mezi dotazem a jednotkou zákona.

    Samotné pokrytí dotazu nestačí — velký § pokryje skoro cokoli, takže by vždy
    přebil ten správný odstavec. Proto se váží i opačný směr: kolik z jednotky je
    vlastně o té otázce. Tím se sama vybere správná úroveň podrobnosti.
    """
    uniq = set(query_stems)
    if not uniq or not unit.stem_set:
        return 0.0
    hit = sum(idf.get(t, DEFAULT_IDF) for t in uniq if t in unit.stem_set)
    if not hit:
        return 0.0
    recall = hit / sum(idf.get(t, DEFAULT_IDF) for t in uniq)
    precision = hit / sum(idf.get(t, DEFAULT_IDF) for t in unit.stem_set)
    b2 = FSCORE_BETA ** 2
    return (1 + b2) * precision * recall / (b2 * precision + recall)


def longest_common_phrase(a_tokens: list[str], b_norm: str) -> tuple[int, str]:
    """Nejdelší souvislá fráze z a_tokens, která je doslova v b_norm.

    Vrací (počet slov, ta fráze). Tohle je jádro celé metody: distraktor vzniká
    z textu zákona vsunutím nebo záměnou slova, čímž se souvislá shoda zlomí,
    zatímco správná odpověď drží dlouhý souvislý úsek.
    """
    best, best_phrase = 0, ""
    n = len(a_tokens)
    for start in range(n):
        if n - start <= best:  # zbytek už nemůže překonat maximum
            break
        end = start + best + 1
        while end <= n:
            phrase = " ".join(a_tokens[start:end])
            if phrase in b_norm:
                best, best_phrase = end - start, phrase
                end += 1
            else:
                break
    return best, best_phrase


def option_support(option_text: str, evidence: str, evidence_stems: set[str],
                   idf: dict[str, float]) -> tuple[int, float, str]:
    """Jak moc je znění možnosti podepřené důkazním textem.

    Vrací (délka nejdelší doslovné fráze ve slovech, pokrytí slov 0..1, ta fráze).
    Řadí se primárně podle fráze; pokrytí je až rozřazovač shodných délek.
    """
    stems = content_stems(option_text)
    uniq = set(stems)
    total = sum(idf.get(t, DEFAULT_IDF) for t in uniq)
    hit = sum(idf.get(t, DEFAULT_IDF) for t in uniq if t in evidence_stems)
    coverage = hit / total if total else 0.0

    # Bez filtrování krátkých slov — obě strany musí být tokenizované stejně,
    # jinak by se souvislá fráze rozpadla na spojkách („R1 a R2").
    phrase_len, phrase = longest_common_phrase(tokenize(option_text), evidence)
    return phrase_len, coverage, phrase


# --------------------------------------------------------------------------
# Tvrdá fakta ve správné odpovědi
# --------------------------------------------------------------------------

UNIT_WORDS = (
    r"let|leta|rok\w*|dn\w+|den|mesic\w*|tydn\w*|hodin\w*|minut\w*|"
    r"mm|kc|korun\w*|ks|kus\w*|procent\w*|kalibr\w*|raze|joul\w*|j"
)
FACT_NUM_RE = re.compile(rf"\b(\d+)\s+({UNIT_WORDS})\b")
FACT_PARAGRAPH_RE = re.compile(r"§\s?(\d+[a-z]?)")
FACT_CATEGORY_RE = re.compile(r"\bkategori\w*\s+([A-D](?:-[IVX]+)?)\b")


def extract_facts(text: str) -> list[tuple[str, str]]:
    """Tvrdá, strojově ověřitelná tvrzení: (typ, hodnota)."""
    facts: list[tuple[str, str]] = []
    norm = " ".join(tokenize(text))  # číslovky slovy jsou tu už jako číslice

    for num, unit in FACT_NUM_RE.findall(norm):
        facts.append(("lhůta/množství", f"{num} {unit}"))
    for par in FACT_PARAGRAPH_RE.findall(text):
        facts.append(("odkaz na §", f"§ {par}"))
    for cat in FACT_CATEGORY_RE.findall(text):
        facts.append(("kategorie", cat))

    seen: set[tuple[str, str]] = set()
    return [f for f in facts if not (f in seen or seen.add(f))]


def fact_in_evidence(fact: tuple[str, str], evidence: str, labels: list[str]) -> bool:
    kind, value = fact
    if kind == "lhůta/množství":
        num, unit = value.split(" ", 1)
        # číslo musí být u jednotky (do 2 slov od sebe), ne kdekoli v paragrafu
        return re.search(rf"\b{num}\b(\s+\S+){{0,2}}\s+{unit[:5]}", evidence) is not None
    if kind == "odkaz na §":
        num = value.split()[1]
        return value in labels or re.search(rf"\b{num}\b", evidence) is not None
    if kind == "kategorie":
        return re.search(rf"kategori\w*\s+{value.lower()}\b", evidence) is not None
    return False


# --------------------------------------------------------------------------
# Vyhodnocení jedné otázky
# --------------------------------------------------------------------------


@dataclass
class Result:
    number: int
    section: str
    question: str
    correct: str
    verdict: str
    reason: str  # proč NEROZHODNUTO / MIMO ZÁKON
    anchor: str  # ustanovení, kterým je správná odpověď doložená
    anchor_quote: str
    top: list[tuple[str, float]]  # (label, skóre)
    phrase_len: dict[str, int]
    coverage: dict[str, float]
    match_phrase: dict[str, str]
    best_option: str
    margin: int
    facts: list[tuple[str, str, bool]]


# Otázky na nepříslušnost („Mezi regulované součásti … NEpatří"). Tady je správná
# odpověď naopak ta, kterou zákon NEuvádí — pořadí se proto obrací.
MEMBERSHIP_NEGATION_RE = re.compile(r"\b(nepatří|nespadá|nezahrnuje|neřadí)", re.IGNORECASE)
# Ostatní negace metoda posoudit umí (bývají to doslovné opisy záporných
# ustanovení), ale je to její slabé místo — u nálezu se to připomene.
OTHER_NEGATION_RE = re.compile(
    r"\b(není|nejsou|nesmí|nelze|nemusí|neplatí|nevztahuje|nepovažuj\w*|"
    r"nepodléhá|nesplňuj\w*|kromě|výjimkou)", re.IGNORECASE
)


def find_quote(option_text: str, unit: LawUnit) -> str:
    """Věta z jednotky, která má se správnou odpovědí největší překryv."""
    # Zákon má dlouhá souvětí s písmennými výčty — dělíme i na „a)", „b)", …
    source = f"{unit.lead} {unit.text}" if unit.depth >= 2 else unit.text
    sentences = re.split(r"(?<=[.;])\s+|(?=\b[a-z]\)\s)", source.replace("\n", " "))
    opt_stems = set(content_stems(option_text))
    best, best_score = "", 0.0
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 25:
            continue
        sent_stems = set(content_stems(sent))
        if not sent_stems:
            continue
        score = len(opt_stems & sent_stems) / max(1, len(opt_stems))
        if score > best_score:
            best, best_score = sent, score
    return best[:400]


def evaluate(q: dict, units: list[LawUnit], idf: dict[str, float]) -> Result:
    options: dict[str, str] = q["options"]
    correct = q["correct"]

    # 1) kandidátní jednotky zákona. Téma určuje hlavně znění otázky, možnosti jen
    #    doplňují — a to VŠECHNY najednou, takže výběr paragrafu nijak nezvýhodní
    #    tu, která je označená za správnou.
    stem_q = content_stems(q["question"])
    stem_opts = content_stems(" ".join(options.values()))
    scored = sorted(
        (
            (0.65 * unit_score(stem_q, u, idf) + 0.35 * unit_score(stem_opts, u, idf), u)
            for u in units
        ),
        key=lambda x: x[0],
        reverse=True,
    )
    # Vybrané jednotky se často překrývají (odstavec i jeho písmeno). Necháme jen
    # ty, které nejsou podmnožinou už vybraného kusu — jinak by důkazní materiál
    # tvořil třikrát tentýž text.
    top: list[tuple[float, LawUnit]] = []
    for score, unit in scored:
        if any(unit.label.startswith(chosen.label) or chosen.label.startswith(unit.label)
               for _, chosen in top):
            continue
        top.append((score, unit))
        if len(top) == TOP_SECTIONS:
            break

    # 2) důkazní materiál
    evidence = " ".join(s.norm for _, s in top)
    evidence_stems: set[str] = set()
    for _, s in top:
        evidence_stems |= s.stem_set
    labels = [s.label for _, s in top]

    # 3) podpora jednotlivých možností
    phrase_len: dict[str, int] = {}
    coverage: dict[str, float] = {}
    match_phrase: dict[str, str] = {}
    for key, text in options.items():
        phrase_len[key], coverage[key], match_phrase[key] = option_support(
            text, evidence, evidence_stems, idf
        )

    # U otázek typu „mezi X nepatří" hledáme naopak možnost NEJMÉNĚ podepřenou —
    # tu, kterou výčet v zákoně neobsahuje.
    inverted = bool(MEMBERSHIP_NEGATION_RE.search(q["question"]))
    ranked = sorted(
        phrase_len.items(),
        key=lambda x: (x[1], coverage[x[0]]),
        reverse=not inverted,
    )
    best_option, best_len = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0
    # U obrácených otázek je „náskok" vzdálenost od druhé nejméně podepřené.
    margin = (runner_up - best_len) if inverted else (best_len - runner_up)
    win_len = max(phrase_len.values()) if inverted else best_len

    # Jaká část možnosti je doslova v zákoně. Rozlišuje „celá věta je opsaná"
    # od „dlouhý úsek je opsaný, ale je k němu přilepená podmínka navíc".
    ratio = {
        k: phrase_len[k] / max(1, len(tokenize(t)))
        for k, t in options.items()
    }
    # Dvě pasti, ve kterých délka fráze nic neznamená a skript se proto
    # nevyjádří:
    #
    # a) Distraktor vzniklý PŘIDÁNÍM podmínky je delší, a tím i doslovně
    #    shodnější, než správná krátká odpověď, která je v zákoně celá
    #    („tlumič je regulovanou součástí" × „…je jí za předpokladu, že…").
    # b) Otázky na členství ve výčtu („osobou oprávněnou … není", „mimo jiné").
    #    Tam jsou doslovné VŠECHNY možnosti — jenže každá z jiného seznamu.
    #    Vyhraje prostě ta nejdelší položka výčtu, bez ohledu na správnost.
    verbatim = [k for k in options if ratio[k] >= 0.99]
    ambiguous_verbatim = not inverted and (
        len(verbatim) >= 2 or (verbatim and ratio[best_option] < 0.95)
    )

    # 4) tvrdá fakta ve správné odpovědi
    facts_raw = extract_facts(options[correct])
    facts = [(k, v, fact_in_evidence((k, v), evidence, labels)) for k, v in facts_raw]

    # 5) verdikt — se zabudovanou abstencí
    reason = ""
    if top[0][0] < MIN_SECTION_SCORE and win_len < MIN_WIN_PHRASE:
        verdict, reason = "MIMO ZÁKON", "žádný paragraf nemá s otázkou dost společného"
    elif win_len < MIN_WIN_PHRASE:
        verdict = "NEROZHODNUTO"
        reason = f"nejdelší doslovná shoda je jen {win_len} slov — příliš krátké možnosti"
    elif margin < MIN_PHRASE_MARGIN:
        verdict = "NEROZHODNUTO"
        reason = f"možnosti jsou doložené srovnatelně ({best_len} vs {runner_up} slov)"
    elif ambiguous_verbatim:
        verdict = "NEROZHODNUTO"
        reason = (
            f"doslovných možností je víc ({', '.join(verbatim)}) — otázka na výčet"
            if len(verbatim) >= 2
            else "jiná možnost je v zákoně celá doslova, vítězná má podmínku navíc"
        )
    elif best_option != correct:
        verdict = "NESHODA"
        if OTHER_NEGATION_RE.search(q["question"]):
            reason = "pozor: v otázce je zápor, tam se metoda plete nejčastěji"
    elif any(not ok for _, _, ok in facts):
        verdict = "K OVĚŘENÍ"
    else:
        verdict = "DOLOŽENO"
    if inverted and verdict in {"DOLOŽENO", "NESHODA", "K OVĚŘENÍ"}:
        reason = (reason + " · " if reason else "") + "otázka na nepříslušnost (obrácené pořadí)"

    # Kotva pro výpis: ze širšího okolí vybereme tu jednotku, se kterou správná
    # odpověď sdílí nejdelší doslovný úsek. Dělá se to AŽ TEĎ, když je verdikt
    # hotový — samotné rozhodnutí tím nesmí být ovlivněno, jinak by se skript
    # ptal na výsledek, který teprve hledá. Jde čistě o to, aby u odpovědi stál
    # správný odkaz („§ 1 odst. 2", ne nejbližší jiný paragraf).
    anchor_score, anchor = top[0]
    best_anchor = -1
    for _score, unit in scored[:ANCHOR_CANDIDATES]:
        hit, _ = longest_common_phrase(tokenize(options[correct]), unit.norm)
        if hit > best_anchor or (hit == best_anchor and unit.depth > anchor.depth):
            best_anchor, anchor = hit, unit

    return Result(
        number=q["pdf_number"],
        section=q["section"],
        question=q["question"],
        correct=correct,
        verdict=verdict,
        reason=reason,
        anchor=f"{anchor.label}" + (f" — {anchor.heading}" if anchor.heading else ""),
        anchor_quote=find_quote(options[correct], anchor),
        top=[(s.label + (f" — {s.heading}" if s.heading else ""), sc) for sc, s in top],
        phrase_len=phrase_len,
        coverage=coverage,
        match_phrase=match_phrase,
        best_option=best_option,
        margin=margin,
        facts=facts,
    )


# --------------------------------------------------------------------------
# Výstup
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Chytáky — čím přesně se distraktor liší od znění zákona
# --------------------------------------------------------------------------


def trap_diff(correct_text: str, distractor_text: str) -> list[tuple[str, str, str]]:
    """Rozdíl mezi správnou odpovědí a distraktorem po slovech.

    Má smysl jen u otázek s verdiktem DOLOŽENO — tam je ověřeno, že správná
    odpověď opisuje zákon, takže každý rozdíl proti ní je právě ta nastražená
    změna. Vrací seznam (operace, znění v zákoně, znění v distraktoru).
    """
    a = correct_text.split()
    b = distractor_text.split()
    out: list[tuple[str, str, str]] = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        out.append((op, " ".join(a[i1:i2]), " ".join(b[j1:j2])))
    return out


def print_traps(r: Result, q: dict) -> None:
    print(f"\n#{r.number}  {r.anchor.split(' — ')[0]}")
    print(f"    zákon říká:  {q['options'][r.correct]}")
    for key, text in q["options"].items():
        if key == r.correct:
            continue
        diffs = trap_diff(q["options"][r.correct], text)
        if not diffs:
            continue
        print(f"    past {key}):")
        for op, orig, fake in diffs:
            if op == "insert":
                print(f"        + vsunuto:  „{fake}\"")
            elif op == "delete":
                print(f"        - vypuštěno: „{orig}\"")
            else:
                print(f"        ~ „{orig}\"  →  „{fake}\"")


VERDICTS = ("DOLOŽENO", "K OVĚŘENÍ", "NESHODA", "NEROZHODNUTO", "MIMO ZÁKON")

VERDICT_MARK = {
    "DOLOŽENO": "OK  ",
    "K OVĚŘENÍ": "?   ",
    "NESHODA": "!!  ",
    "NEROZHODNUTO": "..  ",
    "MIMO ZÁKON": "--  ",
}


def print_result(r: Result, q: dict, verbose: bool) -> None:
    print(f"\n{VERDICT_MARK[r.verdict]}#{r.number} [{r.section}] {r.verdict}"
          + (f" — {r.reason}" if r.reason else ""))
    print(f"    {r.question}")
    for key, text in q["options"].items():
        flag = "*" if key == r.correct else " "
        top = "  <- nejdelší shoda" if key == r.best_option else ""
        print(f"   {flag}{key}) {r.phrase_len[key]:>2} slov / pokrytí {r.coverage[key]:.2f}"
              f"  {text[:78]}{top}")
    print(f"    ustanovení: {r.anchor}")
    print(f"    hledáno v:  {r.top[0][0]}  (skóre {r.top[0][1]:.2f})")
    if r.match_phrase[r.correct]:
        print(f"    shoda:      „{r.match_phrase[r.correct][:150]}\"")
    if r.anchor_quote:
        print(f"    zákon:      „{r.anchor_quote}\"")
    for kind, value, ok in r.facts:
        print(f"    fakt:     {'nalezeno  ' if ok else 'NENALEZENO'} {kind}: {value}")
    if verbose:
        print(f"    další §:  {', '.join(f'{l} {s:.2f}' for l, s in r.top[1:])}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--range", help="rozsah čísel otázek, např. 1-20")
    g.add_argument("--all", action="store_true", help="všech 837 otázek")
    ap.add_argument("--section", help="jen daná oblast (pravo, nauka_o_zbranich, …)")
    ap.add_argument("--only-problems", action="store_true", help="vypsat jen NESHODA / K OVĚŘENÍ")
    ap.add_argument("--chytaky", action="store_true",
                    help="u doložených otázek ukázat, kterým slovem distraktor mění zákon")
    ap.add_argument("--verbose", action="store_true", help="vypsat i další kandidátní paragrafy")
    ap.add_argument("--out", help="uložit report do markdown souboru")
    ap.add_argument("--strict", action="store_true",
                    help="skončit chybou, pokud je nějaká NESHODA (pro CI)")
    args = ap.parse_args()

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))

    if args.all:
        selected = questions
    else:
        lo, hi = (1, 20)
        if args.range:
            parts = args.range.split("-")
            lo, hi = int(parts[0]), int(parts[-1])
        selected = [q for q in questions if lo <= q["pdf_number"] <= hi]

    if args.section:
        selected = [q for q in selected if q["section"] == args.section]

    print("Načítám zákon č. 90/2024 Sb. …", file=sys.stderr)
    sections = parse_law(extract_law_text())
    units = build_units(sections)
    idf = build_idf(units)
    print(f"  {len(sections)} bloků (§ + přílohy) → {len(units)} jednotek "
          f"(odstavce/písmena/body), {len(idf)} unikátních kmenů", file=sys.stderr)
    print(f"Ověřuji {len(selected)} otázek…", file=sys.stderr)

    results = [evaluate(q, units, idf) for q in selected]
    by_number = {q["pdf_number"]: q for q in selected}

    for r in results:
        if args.chytaky:
            if r.verdict == "DOLOŽENO":
                print_traps(r, by_number[r.number])
            continue
        if args.only_problems and r.verdict != "NESHODA" and r.verdict != "K OVĚŘENÍ":
            continue
        print_result(r, by_number[r.number], args.verbose)

    counts = Counter(r.verdict for r in results)
    decided = counts["DOLOŽENO"] + counts["K OVĚŘENÍ"] + counts["NESHODA"]
    print("\n" + "=" * 74)
    print(f"SOUHRN — {len(results)} otázek")
    for verdict in VERDICTS:
        if counts[verdict]:
            pct = 100 * counts[verdict] / len(results)
            print(f"  {verdict:<13} {counts[verdict]:>4}  ({pct:.0f} %)")
    if decided:
        print(f"\n  z {decided} rozhodnutých souhlasí {counts['DOLOŽENO'] + counts['K OVĚŘENÍ']}"
              f"  ({100 * (decided - counts['NESHODA']) / decided:.1f} %)")
    print("=" * 74)
    print("DOLOŽENO     = zákon podpírá právě tu možnost, kterou má aplikace za správnou")
    print("K OVĚŘENÍ    = souhlasí, ale číselný údaj/odkaz ze správné odpovědi se v § nenašel")
    print("NESHODA      = jinou možnost podpírá znění zákona víc — podívat se ručně")
    print("NEROZHODNUTO = metoda nemá dost podkladu (krátké možnosti, výčty, negace)")
    print("MIMO ZÁKON   = otázka nemá oporu v zák. 90/2024 (nauka o zbraních, zdravotní min., NV)")
    print("\nPozn.: jde o lexikální shodu se zněním zákona, ne o právní posouzení.")

    if args.out:
        write_markdown(Path(args.out), results, by_number, counts)
        print(f"\nReport uložen: {args.out}", file=sys.stderr)

    # Ve výchozím stavu končíme úspěchem — NESHODA je fronta na ruční kontrolu,
    # ne prokázaná chyba. Pro CI je od toho --strict.
    return 1 if (args.strict and counts["NESHODA"]) else 0


def write_markdown(path: Path, results: list[Result], by_number: dict[int, dict],
                   counts: Counter) -> None:
    lines = [
        "# Ověření otázek proti zákonu č. 90/2024 Sb.",
        "",
        "Strojové (lexikální) ověření — skript `scripts/validate_vs_zakon.py` hledá",
        "ke každé otázce paragrafy zákona a měří, se kterou z možností sdílí zákon",
        "nejdelší doslovnou frázi. **Není to právní posouzení**, je to ukazatel,",
        "kam se podívat. Kde metoda nemá dost podkladu, vrací NEROZHODNUTO.",
        "",
        f"Zdroj: `{ZAKON_PDF.name}` · otázek: {len(results)}",
        "",
        "| verdikt | počet |",
        "|---|---|",
    ]
    for verdict in VERDICTS:
        if counts[verdict]:
            lines.append(f"| {verdict} | {counts[verdict]} |")
    lines += ["", "---", ""]

    for r in results:
        q = by_number[r.number]
        lines.append(f"### #{r.number} — {r.verdict}" + (f" ({r.reason})" if r.reason else ""))
        lines.append("")
        lines.append(f"**{r.question}**")
        lines.append("")
        for key, text in q["options"].items():
            mark = "**✔**" if key == r.correct else "　"
            lines.append(f"- {mark} `{r.phrase_len[key]:>2} slov` **{key})** {text}")
        lines.append("")
        lines.append(f"Ustanovení: **{r.anchor}**")
        if r.anchor_quote:
            lines.append("")
            lines.append(f"> {r.anchor_quote}")
        if r.facts:
            lines.append("")
            for kind, value, ok in r.facts:
                lines.append(f"- {'✔' if ok else '✗'} {kind}: `{value}`")
        lines += ["", "---", ""]

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
