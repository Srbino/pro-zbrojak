#!/usr/bin/env python3
"""Studijní příručka — ke každé otázce zadání, správná odpověď a ustanovení zákona.

Co skript dělá:

  1. vezme otázky z `data/questions.json` (ověřené proti oficiálnímu PDF MV ČR),
  2. přilepí ověřený odkaz do e-Sbírky z `data/law_refs.json` včetně citace,
  3. přilepí rozbor chytáku z `data/traps.json`, když u otázky je,
  4. na místo lidského výkladu vloží buď text z `data/vyklady.json`, nebo
     zřetelnou značku, že chybí.

**Výklady se drží MIMO markdown**, v `data/vyklady.json`. Markdown je odvozený
soubor — dá se kdykoli přegenerovat a ručně psaný text se tím nesmaže. Proto
se do něj taky nemá psát: co se napíše sem, to příští běh přepíše.

Použití:
    python scripts/gen_prirucka.py --all --out docs/studium/prirucka.md
    python scripts/gen_prirucka.py --section pravo --only-law
    python scripts/gen_prirucka.py --range 1-50
    python scripts/gen_prirucka.py --all --split docs/studium/prirucka/
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "data" / "questions.json"
LAW_REFS = ROOT / "data" / "law_refs.json"
TRAPS = ROOT / "data" / "traps.json"
VYKLADY = ROOT / "data" / "vyklady.json"

SECTION_LABEL = {
    "pravo": "Právo",
    "provadeci_predpisy": "Prováděcí předpisy",
    "jine_predpisy": "Jiné předpisy",
    "nauka_o_zbranich": "Nauka o zbraních a střelivu",
    "zdravotni_minimum": "Zdravotnické minimum",
}

# Pořadí oblastí v příručce — od nejobsáhlejší a nejvíc „zákonné".
SECTION_ORDER = ["pravo", "provadeci_predpisy", "jine_predpisy",
                 "nauka_o_zbranich", "zdravotni_minimum"]

TODO = "_(výklad zatím chybí — doplní se do `data/vyklady.json`)_"

VERDICT_NOTE = {
    "DOLOŽENO": "znění zákona podpírá právě tuhle odpověď",
    "K OVĚŘENÍ": "odpověď souhlasí, ale číselný údaj se v paragrafu nenašel",
    "NESHODA": "**pozor** — skript našel v zákoně větší oporu pro jinou možnost",
}


# --------------------------------------------------------------------------
# načtení dat
# --------------------------------------------------------------------------

class DataError(RuntimeError):
    pass


def load_json(path: Path, default, *, required: bool = False):
    """Načte JSON. Rozbitý soubor je hlášená chyba, ne tichý návrat výchozí hodnoty.

    Tiché spolknutí `JSONDecodeError` znamenalo, že překlep v `vyklady.json`
    vypadal jako „výklady zatím nikdo nenapsal" — hodiny práce se ztratily
    bez jediného slova. Chybějící soubor je v pořádku, rozbitý není.
    """
    if not path.exists():
        if required:
            raise DataError(f"{path} neexistuje")
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataError(
            f"{path} není platný JSON — {exc}\n"
            f"    (častá příčina: rovná uvozovka \" uvnitř textu; "
            f"použij české „ a “)"
        ) from exc
    except OSError as exc:
        raise DataError(f"{path} nejde přečíst — {exc}") from exc


def load_all() -> tuple[list[dict], dict, dict, dict]:
    questions = load_json(QUESTIONS, [])
    refs = load_json(LAW_REFS, {}).get("otazky", {})
    traps = load_json(TRAPS, {}).get("otazky", {})
    vyklady = load_json(VYKLADY, {})
    # Výklady smí být buď {"9": "text"} nebo {"otazky": {"9": "text"}}.
    vyklady = vyklady.get("otazky", vyklady) if isinstance(vyklady, dict) else {}
    # Klíče začínající podtržítkem jsou poznámky pro člověka, ne otázky.
    vyklady = {k: v for k, v in vyklady.items() if not k.startswith("_")}
    return questions, refs, traps, vyklady


# --------------------------------------------------------------------------
# výběr otázek
# --------------------------------------------------------------------------

def select(questions: list[dict], args, refs: dict, traps: dict) -> list[dict]:
    out = questions
    if args.section:
        out = [q for q in out if q.get("section") == args.section]
    if args.range:
        lo, _, hi = args.range.partition("-")
        lo, hi = int(lo), int(hi or lo)
        out = [q for q in out if lo <= q["pdf_number"] <= hi]
    if args.only_law:
        out = [q for q in out if str(q["pdf_number"]) in refs]
    if args.traps:
        out = [q for q in out if str(q["pdf_number"]) in traps]
    if args.missing:
        pass  # dořeší se ve volajícím, potřebuje výklady
    return sorted(out, key=lambda q: q["pdf_number"])


# --------------------------------------------------------------------------
# vykreslení jedné otázky
# --------------------------------------------------------------------------

def quote(text: str) -> str:
    """Text jako blokovou citaci — víceřádkové znění zákona nesmí rozbít odsazení."""
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return "\n".join(f"> {ln}" for ln in lines) if lines else "> —"


# České uvozovky jako konstanty — psát je přímo do f-stringu se nevyplácí,
# vizuálně splývají s ASCII " a rozbijí literál.
LQ = "„"   # „
RQ = "“"   # "
DASH = "—"  # —


def q(text: str) -> str:
    """Text v českých uvozovkách."""
    return f"{LQ}{text}{RQ}"


def render_trap(trap: dict) -> list[str]:
    """Co přesně je u otázky nastražené."""
    out: list[str] = []
    for marker in trap.get("zadani", []):
        out.append(
            f"- v **zadání** je {q(marker['slovo'])} ({marker['typ']}) "
            f"{DASH} obrací smysl otázky"
        )
    for past in trap.get("pasti", []):
        for zm in past.get("zmeny", []):
            typ = zm.get("typ")
            if typ == "vsunuto":
                out.append(f"- do špatné možnosti je **vsunuto** {q(zm['past'])}")
            elif typ == "vypuštěno":
                out.append(f"- ve špatné možnosti **chybí** {q(zm['spravne'])}")
            else:
                out.append(
                    f"- místo {q(zm['spravne'])} je ve špatné možnosti {q(zm['past'])}"
                )
    if trap.get("dvojnici"):
        others = ", ".join(f"č. {n}" for n in trap["dvojnici"])
        out.append(
            f"- skoro stejné zadání má i {others}, ale **jinou správnou odpověď** "
            f"{DASH} nespleť si je"
        )
    return out


def render_question(q: dict, refs: dict, traps: dict, vyklady: dict,
                    *, jen_spravne: bool = False) -> str:
    """Jedna otázka.

    `jen_spravne=True` je podklad pro předčítání (podcast): zadání, správná
    odpověď a zákon. Nesprávné možnosti se vynechají — bez vizuálního
    porovnání jsou při poslechu jen matoucí a je snadné si zapamatovat
    zrovna tu špatnou. Ze stejného důvodu odpadá i rozbor chytáku, který
    o distraktorech mluví.
    """
    num = q["pdf_number"]
    key = str(num)
    correct = q["correct"]
    sec = SECTION_LABEL.get(q.get("section"), q.get("section") or "—")

    parts: list[str] = []
    parts.append(f"### Otázka {num} · {sec}\n")

    parts.append("**Zadání**\n")
    parts.append(quote(q["question"]) + "\n")
    if q.get("image"):
        parts.append(f"*(k otázce patří obrázek: `{q['image']}`)*\n")

    parts.append(f"**Správná odpověď — {correct})**\n")
    parts.append(quote(q["options"][correct]) + "\n")

    if not jen_spravne:
        others = [k for k in ("A", "B", "C") if k != correct and k in q["options"]]
        if others:
            parts.append("<details>")
            parts.append("<summary>Nesprávné možnosti</summary>\n")
            for k in others:
                parts.append(f"- **{k})** {q['options'][k]}")
            parts.append("\n</details>\n")

    ref = refs.get(key)
    if ref:
        parts.append(f"**Ustanovení — [{ref['ref']}]({ref['url']})**\n")
        if ref.get("quote"):
            parts.append(quote(ref["quote"]) + "\n")
        note = VERDICT_NOTE.get(ref.get("verdict", ""))
        if note and not jen_spravne:
            parts.append(f"*Strojová kontrola: {note}.*\n")
    elif not jen_spravne:
        parts.append("**Ustanovení** — ověřený odkaz zatím nemáme.\n")

    if not jen_spravne:
        trap = traps.get(key)
        if trap:
            lines = render_trap(trap)
            if lines:
                parts.append("**Chyták**\n")
                parts.extend(lines)
                parts.append("")

    vyklad = (vyklady.get(key) or "").strip()
    if vyklad or not jen_spravne:
        parts.append("**Co to znamená**\n")
        parts.append(vyklad if vyklad else TODO)
        parts.append("")

    return "\n".join(parts)


# --------------------------------------------------------------------------
# klíč správných odpovědí
# --------------------------------------------------------------------------

def build_klic(questions: list[dict], scope: str) -> str:
    """Soupis `číslo → písmeno` ke kontrole proti oficiální příručce.

    Písmeno je KANONICKÉ z katalogu, tedy přesně to z oficiálního PDF.
    Aplikace si pořadí možností při zobrazení míchá (viz src/ui/shuffle.py),
    ale to je jen prezentace — do dat ani sem se to nepromítá. Kdyby se sem
    dostalo zobrazené písmeno, kontrola proti příručce by nevyšla.
    """
    rows = sorted(questions, key=lambda q: q["pdf_number"])
    dist: dict[str, int] = {}
    for q in rows:
        dist[q["correct"]] = dist.get(q["correct"], 0) + 1

    numbers = [q["pdf_number"] for q in rows]
    mezery = [n for n in range(min(numbers), max(numbers) + 1)
              if n not in set(numbers)] if numbers else []

    out = [
        "# Klíč správných odpovědí — ZOZ",
        "",
        f"Vygenerováno {date.today().isoformat()} · {scope}",
        "",
        "> Písmena jsou z oficiálního souboru otázek MV ČR. Aplikace si při",
        "> zobrazení pořadí možností míchá, ale tady je vždycky původní písmeno",
        "> z příručky — jinak by kontrola nedávala smysl.",
        "",
        f"Otázek: **{len(rows)}**"
        + (f" (chybí čísla: {', '.join(map(str, mezery[:20]))})" if mezery else ""),
        "",
        "Rozložení: " + " · ".join(
            f"**{k}** {dist.get(k, 0)}×" for k in ("A", "B", "C")
        ),
        "",
        "```",
    ]
    for i, q in enumerate(rows):
        # Prázdný řádek po každé desítce — oko líp drží místo při kontrole.
        if i and i % 10 == 0:
            out.append("")
        out.append(f"{q['pdf_number']:>3}  {q['correct']}")
    out += ["```", ""]
    return "\n".join(out)


# --------------------------------------------------------------------------
# hlavička dokumentu
# --------------------------------------------------------------------------

def chunk_evenly(items: list, max_size: int) -> list[list]:
    """Rozdělí na nejmenší počet dílů, z nichž žádný nepřesáhne `max_size`.

    Dělí rovnoměrně, ne po plných padesátkách. 151 otázek po 50 by dalo
    50+50+50+1 a poslední díl s jedinou otázkou je k ničemu — rovnoměrně
    z toho vyjde 38+38+38+37.
    """
    if max_size <= 0 or not items:
        return [items] if items else []
    pocet = math.ceil(len(items) / max_size)
    zaklad, zbytek = divmod(len(items), pocet)
    out, i = [], 0
    for k in range(pocet):
        velikost = zaklad + (1 if k < zbytek else 0)
        out.append(items[i:i + velikost])
        i += velikost
    return out


def header(n_questions: int, n_law: int, n_vyklad: int, scope: str,
           *, jen_spravne: bool = False) -> str:
    pct_law = round(n_law / n_questions * 100) if n_questions else 0
    pct_vyk = round(n_vyklad / n_questions * 100) if n_questions else 0
    title = "Studijní příručka — ZOZ"
    lines = [
        f"# {title}",
        "",
        f"Vygenerováno {date.today().isoformat()} · {scope}",
        "",
    ]
    if jen_spravne:
        lines += [
            "> **Jen správné odpovědi.** Nesprávné možnosti tu schválně nejsou —",
            "> tenhle soubor je podklad k předčítání a při poslechu se snadno",
            "> zapamatuje zrovna ta špatná varianta.",
            "",
        ]
    lines += [
        "> **Tenhle soubor se generuje.** Needituj ho — příští běh",
        "> `scripts/gen_prirucka.py` ho přepíše. Lidský výklad patří do",
        "> `data/vyklady.json`, odkud se sem vkládá.",
        "",
        "| | |",
        "|---|---|",
        f"| Otázek v příručce | {n_questions} |",
        f"| S ověřeným odkazem do e-Sbírky | {n_law} ({pct_law} %) |",
        f"| S lidským výkladem | {n_vyklad} ({pct_vyk} %) |",
        "",
        "Znění otázek a správné odpovědi jsou převzaté z oficiálního souboru",
        "otázek MV ČR a strojově ověřené proti němu. Odkazy na paragrafy míří",
        "do e-Sbírky na zák. č. 90/2024 Sb. ve znění k 1. 1. 2026.",
        "",
        "Studijní pomůcka — nenahrazuje oficiální zdroje MV ČR a platnou legislativu.",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def build(questions: list[dict], refs: dict, traps: dict, vyklady: dict,
          scope: str, *, jen_spravne: bool = False) -> str:
    n_law = sum(1 for q in questions if str(q["pdf_number"]) in refs)
    n_vyk = sum(1 for q in questions if (vyklady.get(str(q["pdf_number"])) or "").strip())

    body: list[str] = [header(len(questions), n_law, n_vyk, scope,
                              jen_spravne=jen_spravne)]

    by_sec: dict[str, list[dict]] = {}
    for q in questions:
        by_sec.setdefault(q.get("section") or "—", []).append(q)

    for sec in SECTION_ORDER + [s for s in by_sec if s not in SECTION_ORDER]:
        group = by_sec.get(sec)
        if not group:
            continue
        body.append(f"## {SECTION_LABEL.get(sec, sec)} ({len(group)})\n")
        for q in group:
            body.append(render_question(q, refs, traps, vyklady,
                                        jen_spravne=jen_spravne))
            body.append("---\n")

    return "\n".join(body)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--all", action="store_true", help="všech 837 otázek")
    g.add_argument("--range", help="rozsah čísel otázek, např. 1-50")
    ap.add_argument("--section", choices=list(SECTION_LABEL), help="jen daná oblast")
    ap.add_argument("--only-law", action="store_true",
                    help="jen otázky s ověřeným odkazem do e-Sbírky")
    ap.add_argument("--traps", action="store_true", help="jen chytáky")
    ap.add_argument("--missing", action="store_true",
                    help="jen otázky, kterým výklad zatím chybí")
    ap.add_argument("--jen-spravne", action="store_true",
                    help="bez nesprávných možností a bez rozboru chytáku — "
                         "podklad k předčítání (podcast)")
    ap.add_argument("--klic", action="store_true",
                    help="jen soupis číslo → správné písmeno (ke kontrole)")
    ap.add_argument("--chunk", type=int, metavar="N",
                    help="se --split: rozdělit každou oblast na díly nejvýš po N "
                         "otázkách (rovnoměrně, bez zbytkového dílu o jedné otázce)")
    ap.add_argument("--out", help="cílový soubor (jinak na standardní výstup)")
    ap.add_argument("--split", help="adresář — jeden soubor na oblast")
    args = ap.parse_args()

    try:
        questions, refs, traps, vyklady = load_all()
    except DataError as exc:
        print(f"CHYBA: {exc}")
        return 1
    if not questions:
        print("data/questions.json chybí nebo je prázdný.")
        return 1

    if not (args.all or args.range or args.section or args.only_law or args.traps):
        args.all = True

    picked = select(questions, args, refs, traps)
    if args.missing:
        picked = [q for q in picked if not (vyklady.get(str(q["pdf_number"])) or "").strip()]

    if not picked:
        print("Výběr je prázdný.")
        return 1

    bits = []
    if args.section:
        bits.append(SECTION_LABEL[args.section])
    if args.range:
        bits.append(f"otázky {args.range}")
    if args.only_law:
        bits.append("jen s odkazem do e-Sbírky")
    if args.traps:
        bits.append("jen chytáky")
    if args.missing:
        bits.append("jen bez výkladu")
    if args.jen_spravne:
        bits.append("jen správné odpovědi")
    scope = " · ".join(bits) if bits else "všechny otázky"

    if args.split:
        outdir = Path(args.split)
        outdir.mkdir(parents=True, exist_ok=True)
        written = []
        for sec in SECTION_ORDER:
            group = [q for q in picked if q.get("section") == sec]
            if not group:
                continue

            if args.chunk:
                dily = chunk_evenly(group, args.chunk)
                for i, dil in enumerate(dily, start=1):
                    od, do = dil[0]["pdf_number"], dil[-1]["pdf_number"]
                    popis = (
                        f"{SECTION_LABEL[sec]} — díl {i}/{len(dily)}, otázky {od}–{do}"
                    )
                    text = build(dil, refs, traps, vyklady, popis,
                                 jen_spravne=args.jen_spravne)
                    path = outdir / f"{sec}-{i}z{len(dily)}-otazky-{od}-{do}.md"
                    path.write_text(text, encoding="utf-8")
                    written.append(f"  {path}  ({len(dil)} otázek, č. {od}–{do})")
                continue

            text = build(group, refs, traps, vyklady, SECTION_LABEL[sec],
                         jen_spravne=args.jen_spravne)
            path = outdir / f"{sec}.md"
            path.write_text(text, encoding="utf-8")
            written.append(f"  {path}  ({len(group)} otázek)")
        print("Zapsáno:")
        print("\n".join(written))
        return 0

    if args.klic:
        text = build_klic(picked, scope)
    else:
        text = build(picked, refs, traps, vyklady, scope, jen_spravne=args.jen_spravne)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        n_law = sum(1 for q in picked if str(q["pdf_number"]) in refs)
        n_vyk = sum(1 for q in picked if (vyklady.get(str(q["pdf_number"])) or "").strip())
        print(f"Zapsáno {path}  ·  {len(picked)} otázek  ·  "
              f"{n_law} s paragrafem  ·  {n_vyk} s výkladem")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
