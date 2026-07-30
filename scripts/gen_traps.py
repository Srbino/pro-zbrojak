#!/usr/bin/env python3
"""
Najde v katalogu „chytáky" — otázky, kde je distraktor jen drobně upravená
správná odpověď.

PROČ
----
Zkoušku člověk nesype na tom, že látku nezná, ale na tom, že přehlédne jedno
slovo. „Regulovanou součástí zbraně" × „NEregulovanou součástí zbraně".
„R1, R2, S1 a S2" × „R1, R2, R3, R4, S1 a S2". Takové otázky se vyplatí trénovat
zvlášť — a hlavně si po odpovědi ukázat, co přesně tam bylo nastražené.

JAK SE POZNAJÍ
--------------
Hledá se ve třech místech, protože past nebývá jen v odpovědích:

1. V ODPOVĚDÍCH — správná odpověď se porovná s každým distraktorem po slovech
   (difflib). Past je, když distraktor sdílí se správnou odpovědí aspoň
   MIN_SHARE slov a liší se nanejvýš MAX_OPS zásahy. Tím projdou drobné úpravy
   (vsunuté slovo, záměna čísla, vypuštěná položka výčtu) a neprojdou možnosti,
   které jsou prostě jiný text.

2. V ZADÁNÍ — zápor („se NEpovažuje", „NEpatří"), výjimka („s výjimkou",
   „kromě") a absolutní tvrzení („vždy", „pouze", „nikdy"). Kdo přehlédne zápor,
   odpoví přesně naopak. Seznam slov je kurátorovaný; hledat prostě „ne\\w+" by
   chytalo i „nebo" a „nebezpečí".

3. MEZI OTÁZKAMI — dvojčata, tedy otázky se skoro totožným zadáním, ale jinou
   správnou odpovědí („…NEpatří" × „…patří", „selhání" × „zádržka"). To je
   nejzákeřnější druh: člověk si vybaví odpověď od sesterské otázky. Šablonovitá
   zadání („Vyberte správné tvrzení") se vyřazují — tam není co splést.

Detekce NEPOTŘEBUJE znění zákona — porovnává jen možnosti mezi sebou uvnitř
otázky. Běží tedy i bez PDF a nezávisle na `validate_vs_zakon.py`.

VÝSTUP
------
`data/traps.json` — pro každou nalezenou otázku seznam pastí (co bylo vsunuto,
zaměněno, vypuštěno). Písmena možností se ZÁMĚRNĚ neukládají: v aplikaci se
pořadí A/B/C míchá (viz src/ui/shuffle.py), takže by nic neznamenala.

POUŽITÍ
-------
    python3 scripts/gen_traps.py
    python3 scripts/gen_traps.py --show 15      # vypsat ukázky
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "data" / "questions.json"
OUT_PATH = ROOT / "data" / "traps.json"

# Vyladěno na katalogu: 0.60/3 dává 101 otázek a všechny ručně prohlédnuté vzorky
# byly skutečné chytáky. Přísnější práh (0.70) jich najde jen 64 a vypadnou i
# poctivé pasti typu „zakázanými zbraněmi" × „z povinnosti registrace vyňaty".
MIN_SHARE = 0.60
MAX_OPS = 3

OP_LABEL = {"insert": "vsunuto", "delete": "vypuštěno", "replace": "záměna"}

# Dvojčata: podobnost zadání, od které se otázky považují za zaměnitelné.
TWIN_SIMILARITY = 0.85
# Zadání sdílené aspoň tolika otázkami je šablona, ne past („Vyberte správné tvrzení").
TEMPLATE_MIN_USES = 5
TEMPLATE_MIN_WORDS = 6  # kratší zadání nenese dost obsahu, aby šlo co splést
MAX_TWINS_STORED = 6

# Kurátorované stopy v zadání. Pozor na plošné „ne\w+" — chytalo by „nebo",
# „nebezpečí", „neoprávněný" i tam, kde o zápor vůbec nejde.
STEM_MARKERS: dict[str, tuple[str, ...]] = {
    "zápor": (
        "nepovažuj", "nepatří", "nespadá", "nezahrnuje", "nesmí", "nelze",
        "nemusí", "neplatí", "nevztahuje", "nepodléhá", "nesplňuj", "neodpovídá",
        "není", "nejsou", "nemá", "nemůže", "nezaniká",
    ),
    # „mimo" tu záměrně NENÍ: z 55 výskytů v katalogu je 53× „mimo jiné",
    # což není výjimka, ale „mimo jiné také". Zbylé dva případy nestojí za šum.
    "výjimka": ("s výjimkou", "kromě"),
    "absolutní tvrzení": (
        "vždy", "nikdy", "pouze", "výhradně", "za všech okolností",
        "v žádném případě",
    ),
}


def _bare(text: str) -> str:
    """Text bez interpunkce a velkých písmen — na porovnání „je to vůbec změna?"."""
    return re.sub(r"[^\w\s]", "", text, flags=re.UNICODE).lower().strip()


def word_diff(correct: str, distractor: str) -> list[tuple[str, str, str]]:
    """Rozdíl po slovech: [(operace, znění správné odpovědi, znění distraktoru)].

    Rozdíly jen v interpunkci se zahazují — „výstřelu," × „výstřelu" není past,
    jen by zaplevelila výpis a ukrojila z rozpočtu na zásahy.
    """
    a, b = correct.split(), distractor.split()
    out = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        left, right = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if _bare(left) == _bare(right):
            continue
        out.append((op, left, right))
    return out


def share_of_correct(correct: str, diffs: list[tuple[str, str, str]]) -> float:
    """Jaká část správné odpovědi zůstala v distraktoru nedotčená (0–1)."""
    words = max(1, len(correct.split()))
    changed = sum(max(len(a.split()), len(b.split())) for _, a, b in diffs)
    return max(0.0, 1 - changed / words)


def find_traps(question: dict) -> dict | None:
    """Vrátí popis pastí otázky, nebo None (když to chyták není)."""
    correct = question["options"][question["correct"]]
    traps, best_share = [], 0.0

    for key, text in question["options"].items():
        if key == question["correct"]:
            continue
        diffs = word_diff(correct, text)
        if not diffs or len(diffs) > MAX_OPS:
            continue
        share = share_of_correct(correct, diffs)
        if share < MIN_SHARE:
            continue
        best_share = max(best_share, share)
        traps.append({
            "shoda": round(share, 3),
            # Bez písmene možnosti — v aplikaci se pořadí A/B/C míchá.
            "zmeny": [
                {"typ": OP_LABEL[op], "spravne": a, "past": b}
                for op, a, b in diffs
            ],
        })

    if not traps:
        return None
    return {
        "shoda": round(best_share, 3),
        "spravne": correct,
        "pasti": sorted(traps, key=lambda t: -t["shoda"]),
    }


# --------------------------------------------------------------------------
# Pasti v zadání
# --------------------------------------------------------------------------


def stem_markers(question: dict) -> list[dict]:
    """Zápor, výjimka nebo absolutní tvrzení v zadání otázky."""
    text = question["question"].lower()
    found = []
    for kind, words in STEM_MARKERS.items():
        for word in words:
            if word in text:
                found.append({"typ": kind, "slovo": word.strip()})
                break  # jeden nález na druh stačí
    return found


def _stem_tokens(text: str) -> list[str]:
    flat = unicodedata.normalize("NFKD", text.lower())
    flat = "".join(c for c in flat if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", flat).split()


def find_twins(questions: list[dict]) -> dict[int, list[int]]:
    """Skupiny otázek se skoro totožným zadáním.

    Páruje se do souvislých skupin (kdo je dvojče dvojčete, patří do party),
    takže se řady variant jedné otázky drží pohromadě.
    """
    prepared = [(q["pdf_number"], _stem_tokens(q["question"])) for q in questions]
    counts = Counter(" ".join(t) for _, t in prepared)

    candidates = [
        (num, toks) for num, toks in prepared
        if len(toks) >= TEMPLATE_MIN_WORDS
        and counts[" ".join(toks)] < TEMPLATE_MIN_USES
    ]

    # Hrubé roztřídění, ať se neporovnává každý s každým.
    buckets: dict[tuple, list] = defaultdict(list)
    for num, toks in candidates:
        buckets[(len(toks) // 6, toks[0])].append((num, toks))

    parent: dict[int, int] = {num: num for num, _ in candidates}

    def root(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for group in buckets.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                (na, ta), (nb, tb) = group[i], group[j]
                if SequenceMatcher(None, ta, tb).ratio() >= TWIN_SIMILARITY:
                    parent[root(na)] = root(nb)

    families: dict[int, list[int]] = defaultdict(list)
    for num, _ in candidates:
        families[root(num)].append(num)

    twins: dict[int, list[int]] = {}
    for members in families.values():
        if len(members) < 2:
            continue
        for num in members:
            others = sorted(n for n in members if n != num)
            twins[num] = others[:MAX_TWINS_STORED]
    return twins


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--show", type=int, default=0, help="vypsat N ukázek")
    args = ap.parse_args()

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    twins = find_twins(questions)

    found: dict[str, dict] = {}
    tally = Counter()
    for q in questions:
        entry: dict = {}

        answers = find_traps(q)
        if answers:
            entry.update(answers)
            tally["v odpovědích"] += 1

        markers = stem_markers(q)
        if markers:
            entry["zadani"] = markers
            tally["v zadání"] += 1

        siblings = twins.get(q["pdf_number"])
        if siblings:
            entry["dvojnici"] = siblings
            tally["dvojčata"] += 1

        if entry:
            entry.setdefault("spravne", q["options"][q["correct"]])
            found[str(q["pdf_number"])] = entry

    payload = {
        "pozn": (
            "Chytáky — otázky, kde se dá snadno šlápnout vedle: distraktor je jen "
            "drobně upravená správná odpověď, v zadání je zápor/výjimka, nebo má "
            "otázka dvojče se skoro stejným zadáním. Generuje scripts/gen_traps.py "
            "z katalogu; znění zákona k tomu nepotřebuje."
        ),
        "prah": {
            "min_shoda": MIN_SHARE,
            "max_zasahu": MAX_OPS,
            "podobnost_dvojcat": TWIN_SIMILARITY,
        },
        "otazky": dict(sorted(found.items(), key=lambda kv: int(kv[0]))),
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"chytáků nalezeno: {len(found)} / {len(questions)}", file=sys.stderr)
    for kind, n in tally.most_common():
        print(f"    {kind:<16}{n}", file=sys.stderr)
    print(f"zapsáno: {OUT_PATH.relative_to(ROOT)}", file=sys.stderr)

    for number, trap in list(found.items())[: args.show]:
        head = f"shoda {trap['shoda']:.0%}" if "shoda" in trap else "jen zadání"
        print(f"\n#{number}  ({head})")
        print(f"    správně: {trap['spravne'][:100]}")
        for marker in trap.get("zadani", []):
            print(f"    zadání: {marker['typ']} — „{marker['slovo']}\"")
        if trap.get("dvojnici"):
            print(f"    dvojčata: {trap['dvojnici']}")
        for past in trap.get("pasti", []):
            for z in past["zmeny"]:
                if z["typ"] == "vsunuto":
                    print(f"    past: + vsunuto  „{z['past']}\"")
                elif z["typ"] == "vypuštěno":
                    print(f"    past: - vypuštěno „{z['spravne']}\"")
                else:
                    print(f"    past: ~ „{z['spravne']}\" → „{z['past']}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
