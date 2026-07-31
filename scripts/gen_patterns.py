#!/usr/bin/env python3
"""Vzorce v testu — strukturní pravidla, která se dají pochopit a použít.

Nehledá slovní shody. Ty se sice v katalogu najdou po stovkách, ale při
1700 testovaných slovech je většina z nich náhoda: „stoprocentních" slov má
náhoda vyprodukovat kolem třiceti a přesně tolik se jich najde. Naučit se
takové slovo je navíc stejná práce jako naučit se rovnou ty otázky.

Místo toho popisuje pravidla plynoucí z toho, JAK se test píše — a u každého
měří, jak často platí a které otázky jsou výjimka. Součástí výstupu je
i seznam pravidel, která NEFUNGUJÍ, aby se jimi nikdo nezdržoval.

Použití:
    python scripts/gen_patterns.py
"""
from __future__ import annotations

import json
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "data" / "questions.json"
OUT = ROOT / "data" / "patterns.json"

PRAH_PODOBNOSTI = 0.70   # od kdy jsou dvě možnosti „skoro stejné"
PRAH_ODSTUPU = 0.08      # o kolik musí dvojice převyšovat druhou nejbližší

ABSOLUTNI = ("vždy", "nikdy", "pouze ", "výhradně", "za žádných", "v žádném případě")


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s).lower()


def podobna_dvojice(q: dict) -> tuple[str, str, str] | None:
    """(a, b, odlišná) když jsou právě dvě možnosti si zřetelně nejbližší."""
    o = list(q["options"].items())
    if len(o) != 3:
        return None
    par = sorted(
        (
            (SequenceMatcher(None, norm(a[1]), norm(b[1])).ratio(), a[0], b[0])
            for i, a in enumerate(o)
            for b in o[i + 1:]
        ),
        reverse=True,
    )
    shoda, k1, k2 = par[0]
    if shoda < PRAH_PODOBNOSTI or par[1][0] > shoda - PRAH_ODSTUPU:
        return None
    odlisna = next(k for k, _ in o if k not in (k1, k2))
    return k1, k2, odlisna


def vyluc_podle(q: dict, vzory: tuple[str, ...]) -> list[str]:
    return [k for k, v in q["options"].items() if any(x in norm(v) for x in vzory)]


def zmer_zuzeni(qs: list[dict]) -> dict:
    """Pravidlo, které zúží výběr ze tří možností na dvě."""
    otazky, vyjimky = [], []
    for q in qs:
        d = podobna_dvojice(q)
        if not d:
            continue
        (otazky if q["correct"] in (d[0], d[1]) else vyjimky).append(q["pdf_number"])
    pouzito = len(otazky) + len(vyjimky)
    return {
        "id": "podobna-dvojice",
        "nazev": "Dvě odpovědi si jsou skoro stejné",
        "typ": "zuz",
        "pravidlo": (
            "Když jsou dvě možnosti skoro stejné a třetí je jiná, správná je "
            "téměř vždy jedna z té dvojice. Odlišnou přeskoč a soustřeď se na "
            "rozdíl mezi zbylými dvěma."
        ),
        "proc": (
            "Autor testu vyrábí past tak, že správnou odpověď opíše a změní "
            "v ní jedno slovo. Třetí možnost bývá jen výplň, aby byly tři."
        ),
        "pozor": (
            "Dostane tě ze tří možností na dvě, ne na jednu. Zkoušel jsem zúžit "
            "dál — delší z dvojice sedí ve 48 %, kratší v 57 %, což je hod "
            "mincí. Rozdíl mezi nimi musíš znát."
        ),
        "pouzito": pouzito,
        "spolehlivost": round(len(otazky) / pouzito, 3) if pouzito else 0.0,
        "zaklad": round(2 / 3, 3),
        "otazky": sorted(otazky),
        "vyjimky": sorted(vyjimky),
    }


def zmer_vyluceni(qs: list[dict], vzory: tuple[str, ...], **meta) -> dict:
    otazky, vyjimky = [], []
    for q in qs:
        skrtnuto = vyluc_podle(q, vzory)
        if not skrtnuto or len(skrtnuto) == len(q["options"]):
            continue
        (vyjimky if q["correct"] in skrtnuto else otazky).append(q["pdf_number"])
    pouzito = len(otazky) + len(vyjimky)
    return {
        **meta,
        "typ": "vyluc",
        "vzory": list(vzory),
        "pouzito": pouzito,
        "spolehlivost": round(len(otazky) / pouzito, 3) if pouzito else 0.0,
        # Škrtnout naslepo je bezpečné ve dvou třetinách — tolik možností je
        # špatných. Vůči tomu se pravidlo poměřuje, ne vůči stu procent.
        "zaklad": round(2 / 3, 3),
        "otazky": sorted(otazky),
        "vyjimky": sorted(vyjimky),
    }


# Změřeno, nefunguje. Je v datech schválně — ať se tím nikdo nezdržuje.
NEFUNGUJE = [
    ("Vezmi nejdelší odpověď", 0.274, "Horší než náhoda — autoři rozepisují i pasti."),
    ("Vezmi nejkratší odpověď", 0.320, "Na úrovni náhody."),
    ("Ta s nejvíc slovy ze zadání", 0.315, "Na úrovni náhody."),
    ("Nejdelší výčet (nejvíc čárek)", 0.329, "Na úrovni náhody."),
    ("Nejvyšší číselná hodnota", 0.290, "Horší než náhoda."),
    ("Nejnižší číselná hodnota", 0.308, "Na úrovni náhody."),
    ("Ta s výhradou (není-li, pokud)", 0.316, "Na úrovni náhody."),
    ("Hádej vždycky B", 0.349, "Písmena jsou rozložená rovnoměrně a aplikace je navíc míchá."),
]


def main() -> int:
    qs = json.loads(QUESTIONS.read_text(encoding="utf-8"))

    pravidla = [
        zmer_zuzeni(qs),
        zmer_vyluceni(
            qs, ABSOLUTNI,
            id="absolutni-vyrazy",
            nazev="Absolutní výrazy",
            pravidlo=(
                "Škrtni možnost, která tvrdí něco bez výjimky: vždy, nikdy, "
                "pouze, výhradně, za žádných okolností."
            ),
            proc=(
                "Zákon je plný výjimek a podmínek, takže tvrzení bez jakékoli "
                "výhrady bývá přestřelené. Autoři testu to vědomě používají."
            ),
            pozor="Někdy zákon opravdu říká „pouze“ a pak je taková odpověď správná.",
        ),
        zmer_vyluceni(
            qs, ("v rámci",),
            id="v-ramci",
            nazev="Obrat „v rámci“",
            pravidlo="Škrtni možnost, kde je „v rámci“.",
            proc=(
                "Vazba, kterou zákon skoro nepoužívá — objevuje se hlavně "
                "ve volně formulovaných pastech."
            ),
            pozor="Jediná slovní shoda, která obstojí i v přísném statistickém testu.",
        ),
        zmer_vyluceni(
            qs, ("neboť", "protože"),
            id="zduvodneni",
            nazev="Odpověď, která se zdůvodňuje",
            pravidlo="Škrtni možnost obsahující „neboť“ nebo „protože“.",
            proc=(
                "Zákon pravidla stanoví, nezdůvodňuje je. Vysvětlující spojka "
                "prozrazuje větu, kterou dopsal autor testu."
            ),
            pozor="Ve zdravotnickém minimu to platí slaběji — tam se postupy vysvětlují.",
        ),
    ]

    OUT.write_text(json.dumps({
        "zdroj": "data/questions.json",
        "vygenerovano": date.today().isoformat(),
        "pozn": (
            "Strukturní pravidla plynoucí z toho, jak je test napsaný. Měřeno "
            "na všech 837 otázkách. Výjimky jsou otázky, kde pravidlo NEPLATÍ — "
            "ty se vyplatí znát jmenovitě."
        ),
        "pravidla": pravidla,
        "nefunguje": [
            {"nazev": nz, "uspesnost": u, "pozn": p} for nz, u, p in NEFUNGUJE
        ],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Zapsáno {OUT}\n")
    print(f"{'pravidlo':34} {'otázek':>7} {'pokrytí':>8} {'platí':>7} {'výjimek':>8}")
    print("-" * 70)
    for p in pravidla:
        print(f"{p['nazev']:34} {p['pouzito']:>7} {p['pouzito']/len(qs)*100:>7.0f}% "
              f"{p['spolehlivost']*100:>6.0f}% {len(p['vyjimky']):>8}")
    dotcene = {n for p in pravidla for n in p["otazky"] + p["vyjimky"]}
    vyj = {n for p in pravidla for n in p["vyjimky"]}
    print(f"\notázek, kde se aspoň jedno pravidlo uplatní: {len(dotcene)} z {len(qs)} "
          f"({len(dotcene)/len(qs)*100:.0f} %)")
    print(f"otázek, které jsou u některého pravidla výjimkou: {len(vyj)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
