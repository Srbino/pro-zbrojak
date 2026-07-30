#!/usr/bin/env python3
"""Tematické okruhy — otázky seskupené podle toho, co v zákoně řeší.

Proč ne podle oblastí z příručky: ty jsou jen čtyři a „Právo" má 561 otázek,
což k ničemu nevede. Zákon má vlastní členění (ČÁST → HLAVA → Díl → §)
a nadpisy jako *Podmínky zbrojního oprávnění* nebo *Zabezpečení zbraní
a střeliva*. To jsou ty skutečné okruhy — a rovnou dávají pořadí dílů
podcastu podle toho, kolik otázek na ně u zkoušky padá.

Co skript dělá:
  1. z `data/zakon_90_2024.txt` přečte strukturu zákona a nadpisy paragrafů,
  2. otázky s ověřeným odkazem (`data/law_refs.json`) rozdělí do okruhů,
  3. skoro shodné otázky (`data/traps.json`, pole `dvojnici`) sloučí do rodin,
     aby se v podkladu neopakovala desetkrát tatáž věc jinými slovy,
  4. na výklad okruhu vloží text z `data/vyklady-okruhy.json`, nebo značku,
     že chybí.

Výklady se drží MIMO markdown, ve `data/vyklady-okruhy.json` — markdown je
odvozený soubor a přegenerování ho přepíše.

Použití:
    python scripts/gen_okruhy.py                 # zapíše docs/okruhy/
    python scripts/gen_okruhy.py --min-otazek 3
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

QUESTIONS = ROOT / "data" / "questions.json"
LAW_REFS = ROOT / "data" / "law_refs.json"
LAW_TEXT = ROOT / "data" / "zakon_90_2024.txt"
TRAPS = ROOT / "data" / "traps.json"
VYKLADY_OKRUHY = ROOT / "data" / "vyklady-okruhy.json"
OUTDIR = ROOT / "docs" / "studium" / "okruhy"

SECTION_LABEL = {
    "pravo": "Právo",
    "provadeci_predpisy": "Prováděcí předpisy",
    "jine_predpisy": "Jiné předpisy",
    "nauka_o_zbranich": "Nauka o zbraních a střelivu",
    "zdravotni_minimum": "Zdravotnické minimum",
}

TODO = "_(výklad okruhu zatím chybí — doplní se do `data/vyklady-okruhy.json`)_"

RE_STRUCT = re.compile(r"^(ČÁST\s+\S+|HLAVA\s+[IVXL]+|Díl\s+\d+)\s*$")
RE_PAR_HEAD = re.compile(r"^§\s*(\d+[a-z]?)\s*$")
RE_PAR_REF = re.compile(r"§\s*(\d+[a-z]?)")


class DataError(RuntimeError):
    pass


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataError(
            f"{path} není platný JSON — {exc}\n"
            f"    (častá příčina: rovná uvozovka \" uvnitř textu; použij české „ a “)"
        ) from exc


# --------------------------------------------------------------------------
# struktura zákona
# --------------------------------------------------------------------------

def parse_law_structure() -> dict[str, dict]:
    """{číslo §: {nadpis, cast, hlava, dil}} ze znění zákona."""
    if not LAW_TEXT.exists():
        raise DataError(f"{LAW_TEXT} chybí — spusť `make validate-zakon` nebo dodej text zákona.")
    lines = LAW_TEXT.read_text(encoding="utf-8").splitlines()

    def nadpis_po(i: int) -> str:
        """První neprázdný řádek za pozicí `i`.

        Mezi značkou (`HLAVA I`) a jejím názvem někdy stojí prázdný řádek —
        bez přeskakování by okruh zůstal bez názvu a jmenoval se `HLAVA I`.
        """
        for j in range(i + 1, min(i + 4, len(lines))):
            t = lines[j].strip()
            if t:
                return t
        return ""

    cast = hlava = dil = ""
    out: dict[str, dict] = {}
    for i, line in enumerate(lines):
        text = line.strip()
        m = RE_STRUCT.match(text)
        if m:
            nazev = nadpis_po(i)
            # Za značkou může rovnou následovat další úroveň členění.
            if RE_STRUCT.match(nazev) or RE_PAR_HEAD.match(nazev):
                nazev = ""
            if text.startswith("ČÁST"):
                cast, hlava, dil = f"{text} — {nazev}".strip(" —"), "", ""
            elif text.startswith("HLAVA"):
                hlava, dil = f"{text} — {nazev}".strip(" —"), ""
            else:
                dil = f"{text} — {nazev}".strip(" —")
            continue
        m = RE_PAR_HEAD.match(text)
        if m:
            nxt = nadpis_po(i)
            nadpis = nxt if nxt and not nxt.startswith("(") and len(nxt) < 120 else ""
            out[m.group(1)] = {"nadpis": nadpis, "cast": cast, "hlava": hlava, "dil": dil}
    return out


def topic_key(info: dict) -> tuple[str, str, str]:
    """Okruh = nejužší neprázdná úroveň členění. Duplicitní `Díl 1` napříč
    hlavami se rozliší tím, že klíč nese i nadřazené úrovně."""
    return (info["cast"], info["hlava"], info["dil"])


def topic_title(key: tuple[str, str, str]) -> str:
    cast, hlava, dil = key
    for level in (dil, hlava, cast):
        if level and "—" in level:
            return level.split("—", 1)[1].strip()
        if level:
            return level
    return "Ostatní"


def topic_breadcrumb(key: tuple[str, str, str]) -> str:
    return " › ".join(p for p in key if p)


# --------------------------------------------------------------------------
# rodiny skoro shodných otázek
# --------------------------------------------------------------------------

def twin_families(traps: dict) -> dict[int, int]:
    """{číslo otázky: id rodiny}. Rodina = otázky se skoro stejným zadáním."""
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for key, rec in traps.items():
        for other in rec.get("dvojnici", []):
            union(int(key), int(other))
    return {n: find(n) for n in parent}


# --------------------------------------------------------------------------
# vykreslení
# --------------------------------------------------------------------------

LQ, RQ = "„", "“"


def quote(text: str) -> str:
    lines = [ln.strip() for ln in str(text).strip().splitlines() if ln.strip()]
    return "\n".join(f"> {ln}" for ln in lines) if lines else "> —"


def slug(text: str, maxlen: int = 48) -> str:
    s = unicodedata.normalize("NFKD", text.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:maxlen].rstrip("-") or "okruh"


def render_question(q: dict, ref: dict | None, *, rodina: list[dict] | None = None) -> str:
    parts = [f"#### Otázka {q['pdf_number']}\n"]
    parts.append(quote(q["question"]) + "\n")
    parts.append(f"**Správně ({q['correct']}):** {q['options'][q['correct']]}\n")
    if ref and ref.get("ref"):
        parts.append(f"*Plyne z:* [{ref['ref']}]({ref['url']})\n")
    if rodina:
        cisla = ", ".join(str(x["pdf_number"]) for x in rodina)
        parts.append(
            f"*Skoro stejně se ptají i otázky {cisla}* — liší se formulací, "
            "ale odpověď se odvíjí od stejného ustanovení.\n"
        )
    return "\n".join(parts)


def render_topic(key, questions, refs, par_info, families, vyklady) -> str:
    title = topic_title(key)
    breadcrumb = topic_breadcrumb(key)

    out = [
        f"# {title}",
        "",
        f"*{breadcrumb}*" if breadcrumb else "",
        "",
        f"**{len(questions)} otázek** z oficiálního souboru MV ČR.",
        "",
        "> Generovaný soubor — needituj ho. Výklad okruhu patří do",
        "> `data/vyklady-okruhy.json`.",
        "",
        "## Co tenhle okruh řeší",
        "",
        (vyklady.get(breadcrumb) or "").strip() or TODO,
        "",
    ]

    # paragrafy okruhu s citací — zákon jednou nahoře, ne u každé otázky znovu
    pars: dict[str, dict] = {}
    for q in questions:
        ref = refs.get(str(q["pdf_number"]))
        if not ref:
            continue
        m = RE_PAR_REF.match(ref["ref"])
        if not m:
            continue
        pars.setdefault(m.group(1), {"refs": [], "info": par_info.get(m.group(1), {})})
        pars[m.group(1)]["refs"].append(ref)

    if pars:
        out += ["## Ustanovení, o která jde", ""]
        for num in sorted(pars, key=lambda s: (int(re.sub(r"\D", "", s) or 0), s)):
            info = pars[num]["info"]
            nadpis = info.get("nadpis") or ""
            out.append(f"### § {num}" + (f" — {nadpis}" if nadpis else ""))
            out.append("")
            videno = set()
            for ref in pars[num]["refs"]:
                if ref["ref"] in videno or not ref.get("quote"):
                    continue
                videno.add(ref["ref"])
                out.append(f"**{ref['ref']}**")
                out.append("")
                out.append(quote(ref["quote"]))
                out.append("")

    # otázky — rodiny skoro shodných se sloučí do jedné
    out += ["## Otázky", ""]
    videno: set[int] = set()
    poradi = sorted(questions, key=lambda q: q["pdf_number"])
    for q in poradi:
        num = q["pdf_number"]
        if num in videno:
            continue
        fam_id = families.get(num)
        sourozenci = [
            x for x in poradi
            if x["pdf_number"] != num and families.get(x["pdf_number"]) == fam_id
        ] if fam_id is not None else []
        videno.add(num)
        videno.update(x["pdf_number"] for x in sourozenci)
        out.append(render_question(q, refs.get(str(num)), rodina=sourozenci or None))
        out.append("---")
        out.append("")

    return "\n".join(out)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-otazek", type=int, default=3,
                    help="okruhy s méně otázkami se slijí do jednoho (výchozí 3)")
    ap.add_argument("--out", default=str(OUTDIR), help="cílový adresář")
    args = ap.parse_args()

    try:
        questions = load_json(QUESTIONS, [])
        refs = load_json(LAW_REFS, {}).get("otazky", {})
        traps = load_json(TRAPS, {}).get("otazky", {})
        vyklady = load_json(VYKLADY_OKRUHY, {})
        par_info = parse_law_structure()
    except DataError as exc:
        print(f"CHYBA: {exc}")
        return 1

    vyklady = {k: v for k, v in vyklady.items() if not k.startswith("_")}
    families = twin_families(traps)

    # roztřídění do okruhů
    topics: dict[tuple, list[dict]] = defaultdict(list)
    bez_zakona: dict[str, list[dict]] = defaultdict(list)
    for q in questions:
        ref = refs.get(str(q["pdf_number"]))
        m = RE_PAR_REF.match(ref["ref"]) if ref else None
        info = par_info.get(m.group(1)) if m else None
        if info:
            topics[topic_key(info)].append(q)
        else:
            bez_zakona[q.get("section") or "—"].append(q)

    # drobné okruhy se slijí, ať nevznikne patnáct jednootázkových souborů
    drobne: list[dict] = []
    hlavni = {}
    for key, qs in topics.items():
        if len(qs) < args.min_otazek:
            drobne.extend(qs)
        else:
            hlavni[key] = qs

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("*.md"):
        old.unlink()

    poradi = sorted(hlavni.items(), key=lambda kv: -len(kv[1]))
    index_rows = []
    for i, (key, qs) in enumerate(poradi, start=1):
        title = topic_title(key)
        name = f"{i:02d}-{slug(title)}.md"
        (outdir / name).write_text(
            render_topic(key, qs, refs, par_info, families, vyklady), encoding="utf-8"
        )
        má_vyklad = bool((vyklady.get(topic_breadcrumb(key)) or "").strip())
        index_rows.append((name, title, len(qs), má_vyklad))

    if drobne:
        name = f"{len(poradi) + 1:02d}-ostatni-ustanoveni.md"
        (outdir / name).write_text(
            render_topic(("", "", "Ostatní ustanovení"), drobne, refs, par_info,
                         families, vyklady),
            encoding="utf-8",
        )
        index_rows.append((name, "Ostatní ustanovení", len(drobne), False))

    # otázky bez opory v zákoně 90/2024
    poradi_bez = sorted(bez_zakona.items(), key=lambda kv: -len(kv[1]))
    for j, (sec, qs) in enumerate(poradi_bez, start=len(index_rows) + 1):
        label = SECTION_LABEL.get(sec, sec)
        name = f"{j:02d}-bez-zakona-{slug(label)}.md"
        (outdir / name).write_text(
            render_topic(("", "", f"{label} — bez odkazu na zákon"), qs, refs,
                         par_info, families, vyklady),
            encoding="utf-8",
        )
        index_rows.append((name, f"{label} (bez odkazu na zákon)", len(qs), False))

    _write_index(outdir, index_rows, len(questions), len(refs), len(vyklady))
    print(f"Zapsáno {outdir}  ·  {len(index_rows)} okruhů")
    for name, _title, n, ma in index_rows:
        print(f"   {n:4} otázek  {'✓' if ma else ' '}  {name}")

    # Výklad s klíčem, který na žádný okruh nesedí, se nikde neobjeví.
    # Bez upozornění to vypadá, že se text ztratil.
    znamé = {topic_breadcrumb(k) for k in topics}
    osirele = [k for k in vyklady if k not in znamé]
    if osirele:
        print("\nPOZOR — výklad, který na žádný okruh nesedí (překlep v klíči?):")
        for k in osirele:
            print(f"   {k}")
        print("   Klíč je drobečková navigace ze 3. řádku souboru okruhu.")
        return 2
    return 0


def _write_index(outdir: Path, rows, n_q: int, n_ref: int, n_vyk: int) -> None:
    lines = [
        "# Tematické okruhy — ZOZ",
        "",
        f"Vygenerováno {date.today().isoformat()}",
        "",
        "Otázky rozdělené podle toho, co v zákoně řeší — členění je převzaté",
        "ze zákona samotného (ČÁST → HLAVA → Díl), ne vymyšlené. Pořadí je podle",
        "počtu otázek, takže shora jsou okruhy, na které u zkoušky padá nejvíc.",
        "",
        "> Generované soubory — needituj je. Výklady okruhů patří do",
        "> `data/vyklady-okruhy.json`, odkud se sem vkládají.",
        "",
        "| # | Okruh | Otázek | Výklad |",
        "|---|---|---:|:---:|",
    ]
    for i, (name, title, n, ma) in enumerate(rows, start=1):
        lines.append(f"| {i} | [{title}]({name}) | {n} | {'ano' if ma else '—'} |")
    lines += [
        "",
        f"Celkem **{n_q}** otázek, z toho **{n_ref}** má ověřený odkaz do e-Sbírky.",
        f"Výkladů okruhů napsáno: **{n_vyk}**.",
        "",
        "Otázky se skoro shodným zadáním jsou v okruzích sloučené do jedné položky",
        "— u zkoušky se tatáž věc ptá víckrát jinými slovy a nemá smysl si ji",
        "poslouchat desetkrát.",
        "",
        "Studijní pomůcka — nenahrazuje oficiální zdroje MV ČR a platnou legislativu.",
        "",
    ]
    (outdir / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
