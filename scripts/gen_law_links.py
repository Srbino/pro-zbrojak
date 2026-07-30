#!/usr/bin/env python3
"""
Vygeneruje ke každé otázce odkaz do e-Sbírky (MV ČR) na konkrétní ustanovení.

PROČ
----
Aplikace nemusí držet znění zákona. Stačí u otázky vědět, které ustanovení ji
zakládá, a odkázat se na oficiální text na e-Sbírce. Zdrojem pravdy zůstává stát,
my držíme jen otázky a odkaz.

JAK
---
`validate_vs_zakon.py` už u doložených otázek určuje přesnou jednotku zákona
(„§ 7 písm. b) bod 2"). Ukazuje se, že tenhle zápis je ZNAK PO ZNAKU shodný
s oficiální citací v e-Sbírce, a ta zároveň publikuje i URL svého fragmentu:

    GET …/dokument/norma/cast_3/par_7/pism_b/bod_2   (Accept: application/ld+json)
    → citace-označení-fragmentu-znění-právního-aktu : "§ 7 písm. b) bod 2"
    → url-fragmentu-znění                           : "/sb/2024/90/2026-01-01#par_7-pism_b-bod_2"

Do ELI cesty patří i členění, které se v citaci neobjevuje (`cast_4/hlava_1/dil_1
/par_12`), takže cestu nelze z označení odvodit. Zato KOTVA v URL vzniká prostě
spojením úrovní par/odst/pism/bod pomlčkou — a ta členění ignoruje.

Skript proto stáhne JEDNÍM dotazem seznam všech fragmentů zákona (RDF kořenového
dokumentu, ~1400 položek) a k našemu označení dohledá odpovídající fragment v něm.
Odkaz se tedy nehádá — buď v oficiálním seznamu je, nebo otázka odkaz nedostane.

VÝSTUP
------
`data/law_refs.json` — mapa číslo otázky → { ref, url, quote, verdict }.
Soubor je verzovaný; aplikace ho jen čte, takže odkazy fungují i offline
(otevřou se až kliknutím). Přegenerování je potřeba jen při nové verzi zákona
nebo katalogu otázek.

POUŽITÍ
-------
    python3 scripts/gen_law_links.py                 # ověří online a zapíše
    python3 scripts/gen_law_links.py --offline       # bez sítě, jen ze cache
    python3 scripts/gen_law_links.py --limit 20      # zkouška na pár otázkách
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = Path(__file__).resolve().parent / "validate_vs_zakon.py"
OUT_PATH = ROOT / "data" / "law_refs.json"
FRAGMENTS_PATH = ROOT / "data" / "eli_fragmenty.html"  # cache seznamu (gitignored)

# Znění zákona č. 90/2024 Sb. účinné od 1. 1. 2026.
ELI_DOC = "eli/cz/sb/2024/90/2026-01-01"
ELI_ROOT = f"https://opendata.eselpoint.gov.cz/esel-esb/{ELI_DOC}"
ELI_BASE = f"{ELI_ROOT}/dokument/norma"
PUBLIC_BASE = "https://e-sbirka.gov.cz"
PUBLIC_DOC = "/sb/2024/90/2026-01-01"
URL_KEY = "l-sgov-dat-sbirka-pojem:url-fragmentu-znění"

REQUEST_PAUSE = 0.25  # vteřiny mezi dotazy — na cizí server se nemá tlačit
VERIFY_SAMPLE = 12  # kolik odkazů se namátkou ověří proti API


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_vs_zakon", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_vs_zakon"] = module  # kvůli @dataclass
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# Označení jednotky  →  ELI cesta
# --------------------------------------------------------------------------

LABEL_RE = re.compile(
    r"^§\s*(?P<par>\d+[a-z]?)"
    r"(?:\s+odst\.\s*(?P<odst>\d+))?"
    r"(?:\s+písm\.\s*(?P<pism>[a-z])\))?"
    r"(?:\s+bod\s*(?P<bod>\d+))?\s*$"
)


def label_to_segments(label: str) -> list[str] | None:
    """“§ 7 písm. b) bod 2” → ['par_7', 'pism_b', 'bod_2']. None u příloh apod."""
    m = LABEL_RE.match(label.split(" — ")[0].strip())
    if not m:
        return None
    segments = [f"par_{m.group('par')}"]
    for key, prefix in (("odst", "odst"), ("pism", "pism"), ("bod", "bod")):
        if m.group(key):
            segments.append(f"{prefix}_{m.group(key)}")
    return segments


# --------------------------------------------------------------------------
# Ověření proti e-Sbírce
# --------------------------------------------------------------------------


def fetch(url: str, accept: str) -> bytes | None:
    req = urllib.request.Request(
        url,
        headers={"Accept": accept,
                 "User-Agent": "pro-zbrojak/0.5 (+github.com/Srbino/pro-zbrojak)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


# Úrovně, které se promítají do kotvy v URL. Členění (cast/hlava/dil/oddil)
# a nepojmenované textové fragmenty (frag_…) se do ní nedávají.
ANCHOR_LEVELS = ("par_", "odst_", "pism_", "bod_")


def load_fragment_index(offline: bool) -> dict[str, str]:
    """Stáhne (jednou) seznam všech fragmentů zákona → mapa kotva → ELI cesta."""
    if not FRAGMENTS_PATH.exists() and not offline:
        print("Stahuji seznam ustanovení z e-Sbírky…", file=sys.stderr)
        body = fetch(ELI_ROOT, "text/html")
        if body is None:
            sys.exit("CHYBA: seznam ustanovení se nepodařilo stáhnout.")
        FRAGMENTS_PATH.write_bytes(body)

    if not FRAGMENTS_PATH.exists():
        sys.exit("CHYBA: chybí cache seznamu ustanovení, spusť bez --offline.")

    raw = FRAGMENTS_PATH.read_text(encoding="utf-8", errors="replace")
    paths = set(re.findall(r"dokument/norma/([a-z0-9_/]+)", raw))

    index: dict[str, str] = {}
    for path in paths:
        segments = [s for s in path.split("/") if s.startswith(ANCHOR_LEVELS)]
        if not segments or not segments[0].startswith("par_"):
            continue
        index.setdefault("-".join(segments), path)
    return index


def resolve(label: str, index: dict[str, str]) -> dict | None:
    """Označení jednotky → odkaz do e-Sbírky, nebo None (když ustanovení neexistuje).

    Raději žádný odkaz než odkaz vedle: kotva musí být v oficiálním seznamu.
    """
    segments = label_to_segments(label)
    if not segments:
        return None
    anchor = "-".join(segments)
    if anchor not in index:
        return None
    return {
        "ref": label,
        "url": f"{PUBLIC_BASE}{PUBLIC_DOC}#{anchor}",
        "eli": index[anchor],
    }


def verify_sample(index: dict[str, str], anchors: list[str]) -> tuple[int, int]:
    """Namátkou ověří proti API, že kotva i citace sedí. Vrací (ověřeno, neshod)."""
    ok = bad = 0
    for anchor in anchors:
        body = fetch(f"{ELI_BASE}/{index[anchor]}", "application/ld+json")
        time.sleep(REQUEST_PAUSE)
        if body is None:
            continue
        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            continue
        url = (data.get(URL_KEY) or "").strip()
        if url == f"{PUBLIC_DOC}#{anchor}":
            ok += 1
        else:
            bad += 1
            print(f"  NESEDÍ: {anchor} → e-Sbírka uvádí {url!r}", file=sys.stderr)
    return ok, bad


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="nechodit na síť, použít jen cache")
    ap.add_argument("--limit", type=int, help="zpracovat jen prvních N otázek (zkouška)")
    args = ap.parse_args()

    validator = load_validator()
    print("Načítám zákon a vyhodnocuji otázky…", file=sys.stderr)
    units = validator.build_units(validator.parse_law(validator.extract_law_text()))
    idf = validator.build_idf(units)
    questions = json.loads(validator.QUESTIONS.read_text(encoding="utf-8"))
    if args.limit:
        questions = questions[: args.limit]

    index = load_fragment_index(args.offline)
    print(f"  {len(index)} ustanovení v oficiálním seznamu", file=sys.stderr)

    refs: dict[str, dict] = {}
    used_anchors: list[str] = []
    stats = {"doloženo": 0, "odkaz": 0, "bez odkazu": 0}

    for q in questions:
        result = validator.evaluate(q, units, idf)
        if result.verdict not in {"DOLOŽENO", "K OVĚŘENÍ"}:
            continue
        stats["doloženo"] += 1

        label = result.anchor.split(" — ")[0].strip()
        entry = resolve(label, index)
        if not entry:
            stats["bez odkazu"] += 1
            continue

        stats["odkaz"] += 1
        used_anchors.append(entry["url"].split("#", 1)[1])
        refs[str(q["pdf_number"])] = {
            "ref": entry["ref"],
            "url": entry["url"],
            "quote": result.anchor_quote,
            "verdict": result.verdict,
        }

    # Namátková kontrola proti API — jestli se pravidlo pro kotvu nezměnilo.
    if not args.offline and used_anchors:
        unique = sorted(set(used_anchors))
        step = max(1, len(unique) // VERIFY_SAMPLE)
        sample = unique[::step][:VERIFY_SAMPLE]
        print(f"Namátkou ověřuji {len(sample)} odkazů proti e-Sbírce…", file=sys.stderr)
        ok, bad = verify_sample(index, sample)
        print(f"  potvrzeno {ok}, neshod {bad}", file=sys.stderr)
        if bad:
            sys.exit("CHYBA: e-Sbírka vrací jiné kotvy — nezapisuji.")
    payload = {
        "zdroj": "e-Sbírka MV ČR — zákon č. 90/2024 Sb., znění od 1. 1. 2026",
        "eli": "eli/cz/sb/2024/90/2026-01-01",
        "pozn": (
            "Odkazy jsou strojově odvozené z lexikálního ověření "
            "(scripts/validate_vs_zakon.py) a potvrzené proti e-Sbírce. "
            "Nejde o právní výklad — ustanovení je vodítko, ne autorita."
        ),
        "otazky": dict(sorted(refs.items(), key=lambda kv: int(kv[0]))),
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\ndoložených otázek:  {stats['doloženo']}", file=sys.stderr)
    print(f"z toho s odkazem:   {stats['odkaz']}", file=sys.stderr)
    print(f"nepotvrzeno:        {stats['bez odkazu']}", file=sys.stderr)
    print(f"zapsáno:            {OUT_PATH.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
