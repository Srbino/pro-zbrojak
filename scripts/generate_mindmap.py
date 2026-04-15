#!/usr/bin/env python3
"""Vygeneruje mysckovou mapu vsech otazek do QUESTIONS_MINDMAP.md.

Struktura:
1. Souhrn (counts, distribuce)
2. Per-oblast sekce (pravo / nauka / zdrávo / ...)
3. Obrázková mapa (thumbnail + question text)
4. Validation summary
5. Known PDF duplicates
6. TOC s odkazy
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from hashlib import md5
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ui.components import SECTION_LABEL


def main():
    qs = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    by_num = {q["pdf_number"]: q for q in qs}

    # Basic stats
    total = len(qs)
    by_section = Counter(q["section"] for q in qs)
    by_correct = Counter(q["correct"] for q in qs)
    image_qs = [q for q in qs if q.get("image")]
    n_images = len(image_qs)
    pages = Counter(q["source_page"] for q in qs)
    page_range = (min(pages), max(pages))

    # Duplicates (by hash)
    hashes = defaultdict(list)
    for q in qs:
        hashes[q["id"]].append(q["pdf_number"])
    dup_groups = {h: nums for h, nums in hashes.items() if len(nums) > 1}

    # Image hashes dedup
    img_hashes = defaultdict(list)
    for q in image_qs:
        p = ROOT / q["image"]
        if p.exists():
            h = md5(p.read_bytes()).hexdigest()
            img_hashes[h].append(q["pdf_number"])
    img_dup_groups = {h: nums for h, nums in img_hashes.items() if len(nums) > 1}

    lines: list[str] = []
    lines += [
        "# Myšlenková mapa testových otázek",
        "",
        "Kompletní přehled **všech 837 otázek** ze Souboru testových otázek MV ČR (15. 12. 2025).",
        "Vygenerováno automaticky z `data/questions.json`. Umožňuje **ručně ověřit správnost proti PDF**.",
        "",
        "## Obsah",
        "1. [Souhrnné statistiky](#souhrnne-statistiky)",
        "2. [Oblasti otázek](#oblasti-otazek)",
    ]
    for sec in SECTION_LABEL:
        if sec in by_section:
            lines.append(f"   - [{SECTION_LABEL[sec]}](#{sec})")
    lines += [
        "3. [Obrázkové otázky](#obrazkove-otazky)",
        "4. [Známé duplicity v PDF](#zname-duplicity-v-pdf)",
        "5. [Distribuce správných odpovědí](#distribuce-spravnych-odpovedi)",
        "",
        "---",
        "",
        "## Souhrnné statistiky",
        "",
        f"| Metrika | Hodnota |",
        f"|---|---|",
        f"| **Celkem otázek** | {total} |",
        f"| **Otázek s obrázkem** | {n_images} ({n_images*100//total} %) |",
        f"| **Stránky PDF** | {page_range[0]} – {page_range[1]} |",
        f"| **Oblastí** | {len(by_section)} |",
        f"| **Duplicitních otázek v PDF** | {sum(len(v)-1 for v in dup_groups.values())} (ve {len(dup_groups)} skupinách) |",
        f"| **Duplicitních obrázků** (sdílené) | {sum(len(v)-1 for v in img_dup_groups.values())} (v {len(img_dup_groups)} skupinách) |",
        "",
        "### Rozložení podle oblasti",
        "",
        f"| Oblast | Otázek | Stránky PDF | S obrázkem |",
        f"|---|---:|---:|---:|",
    ]
    for sec, label in SECTION_LABEL.items():
        if sec not in by_section:
            continue
        sec_qs = [q for q in qs if q["section"] == sec]
        sec_pages = sorted({q["source_page"] for q in sec_qs})
        sec_imgs = sum(1 for q in sec_qs if q.get("image"))
        pages_str = f"{sec_pages[0]}–{sec_pages[-1]}"
        lines.append(f"| {label} | {len(sec_qs)} | {pages_str} | {sec_imgs} |")

    lines += [
        "",
        "## Oblasti otázek",
        "",
    ]

    for sec, label in SECTION_LABEL.items():
        if sec not in by_section:
            continue
        sec_qs = sorted([q for q in qs if q["section"] == sec], key=lambda q: q["pdf_number"])
        lines += [
            f"### {sec}",
            "",
            f"<details open><summary><b>{label}</b> — {len(sec_qs)} otázek "
            f"(č. {sec_qs[0]['pdf_number']}–{sec_qs[-1]['pdf_number']}, "
            f"strany {sec_qs[0]['source_page']}–{sec_qs[-1]['source_page']})</summary>",
            "",
            f"| Č. | Strana | Správná | Náhled otázky |",
            f"|---:|---:|:---:|:---|",
        ]
        for q in sec_qs:
            img_mark = " 🖼" if q.get("image") else ""
            # Truncate question text for readability
            preview = q["question"][:100].replace("|", "\\|").replace("\n", " ")
            if len(q["question"]) > 100:
                preview += "…"
            lines.append(
                f"| {q['pdf_number']} | {q['source_page']} | "
                f"**{q['correct']}** | {preview}{img_mark} |"
            )
        lines += ["", "</details>", ""]

    # Image gallery
    lines += [
        "## Obrázkové otázky",
        "",
        f"Celkem **{n_images} otázek s obrázkem**, většinou v oblasti *Nauka o zbraních a střelivu*.",
        "Obrázky jsou rasterizovány z PDF včetně overlay čísel (1–6) a anotací.",
        "",
    ]

    # Group image questions by page (many share page/image context)
    img_by_page: dict[int, list[dict]] = defaultdict(list)
    for q in image_qs:
        img_by_page[q["source_page"]].append(q)

    for page_num in sorted(img_by_page):
        qs_on_page = sorted(img_by_page[page_num], key=lambda q: q["pdf_number"])
        lines += [
            f"### Strana PDF č. {page_num}",
            "",
        ]
        for q in qs_on_page:
            img_url = q["image"]
            preview = q["question"][:200].replace("\n", " ")
            opts_preview = "  ".join(
                f"**{k})** {q['options'][k][:80]}"
                for k in "ABC"
            )
            lines += [
                f"#### Otázka č. {q['pdf_number']}  —  správná: **{q['correct']}**",
                "",
                f"<img src=\"{img_url}\" alt=\"Q{q['pdf_number']}\" width=\"420\">",
                "",
                f"**Otázka:** {preview}",
                "",
                f"- **A)** {q['options']['A']}",
                f"- **B)** {q['options']['B']}",
                f"- **C)** {q['options']['C']}",
                "",
                "---",
                "",
            ]

    # Known duplicates
    lines += [
        "## Známé duplicity v PDF",
        "",
        "Některé otázky jsou v PDF MV ČR **faktické duplikáty** (stejný text + stejné odpovědi).",
        "Parser je detekuje a sdílí jim hash-ID. Pro učení to nevadí — uživatel na duplikát odpoví stejně.",
        "",
    ]
    if dup_groups:
        lines += [f"| Hash | Pořadová čísla v PDF |", "|---|---|"]
        for h, nums in sorted(dup_groups.items(), key=lambda x: min(x[1])):
            lines.append(f"| `{h[:12]}` | {', '.join(str(n) for n in nums)} |")
    else:
        lines.append("Žádné duplicity nenalezeny.")
    lines += ["", ""]

    # Image duplicates (shared images for question series)
    if img_dup_groups:
        lines += [
            "### Sdílené obrázky",
            "",
            "Některé otázky odkazují na **stejný obrázek** v PDF (série otázek o jedné pistoli).",
            "Parser rasterizuje zvlášť pro každou, ale obsah může být vizuálně identický.",
            "",
            "| Obrázek (md5) | Otázky které ho sdílí |",
            "|---|---|",
        ]
        for h, nums in sorted(img_dup_groups.items(), key=lambda x: min(x[1])):
            lines.append(f"| `{h[:12]}` | Q{', Q'.join(str(n) for n in nums)} |")
        lines += [""]

    # Correct answer distribution
    lines += [
        "## Distribuce správných odpovědí",
        "",
        "Ideálně by distribuce A/B/C měla být přibližně uniformní. "
        "Výrazná nerovnováha by indikovala systematickou chybu v parseru.",
        "",
        "| Odpověď | Počet | Podíl |",
        "|---|---:|---:|",
    ]
    for letter in "ABC":
        pct = by_correct[letter] * 100 // total
        lines.append(f"| **{letter}** | {by_correct[letter]} | {pct} % |")
    lines += [""]

    # Footer
    lines += [
        "---",
        "",
        "## Jak ověřit ručně",
        "",
        "1. Otevři si PDF `MV-Soubor_testovych_otazek_...pdf` v PDF prohlížeči.",
        "2. Vyber si náhodně 10–20 otázek z tabulek výše.",
        "3. Pro každou zkontroluj:",
        "   - **Text otázky** se shoduje (přes první věty).",
        '   - **Správná odpověď** (šedé podbarvení v PDF) = sloupec "Správná" v tabulce.',
        "   - **Obrázek** (🖼) se reálně v PDF objevuje nad touto otázkou.",
        "4. Pokud najdeš chybu, otevři issue s číslem otázky a popisem.",
        "",
        f"_Vygenerováno {__file__.split('/')[-1]} z {total} otázek._",
    ]

    out = ROOT / "QUESTIONS_MINDMAP.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Ulozeno: {out} ({len(lines)} radku)")
    return out


if __name__ == "__main__":
    main()
