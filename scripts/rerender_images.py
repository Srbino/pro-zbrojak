#!/usr/bin/env python3
"""Přerenderuje obrázky otázek z oficiálního PDF — bez sahání na questions.json.

Proč samostatný skript: `parse_pdf.py` přegeneruje celý katalog. Když jde jen
o obrázky, je zbytečné riskovat změnu 837 otázek kvůli 71 souborům.

Opravovaná vada: některé otázky mají v PDF víc samostatných obrázků pod sebou
(otázka 609 má tři znehodnocovací značky). Původní extrakce brala jen první,
takže se u takové otázky ukázala jedna značka ze tří.

Použití:
    python scripts/rerender_images.py --dry-run     # jen ukáže, co by se změnilo
    python scripts/rerender_images.py               # přepíše images/
    python scripts/rerender_images.py --only 609
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from parse_pdf import IMAGE_CLIP_PAD, question_image_clip  # noqa: E402

QUESTIONS = ROOT / "data" / "questions.json"
IMAGES_DIR = ROOT / "images"
RENDER_DPI = 170


def find_pdf() -> Path:
    hits = sorted(ROOT.glob("docs/MV-Soubor*.pdf")) + sorted(ROOT.glob("MV-Soubor*.pdf"))
    if not hits:
        raise SystemExit("Zdrojové PDF MV ČR nenalezeno (docs/MV-Soubor*.pdf).")
    return hits[0]


def marker_tops(page, numbers: set[int]) -> dict[int, float]:
    """Kde na stránce začíná která otázka — podle značky `123.` u levého okraje."""
    out: dict[int, float] = {}
    for w in page.get_text("words"):
        x0, y0, _, _, text = w[0], w[1], w[2], w[3], w[4]
        if x0 > 120:                       # značka otázky je vlevo
            continue
        m = re.fullmatch(r"(\d{1,4})\.", text)
        if m:
            n = int(m.group(1))
            if n in numbers and n not in out:
                out[n] = y0
    return out


def image_rects(page) -> list:
    seen: set[tuple[int, int, int, int]] = set()
    rects = []
    for img in page.get_images(full=True):
        try:
            found = page.get_image_rects(img[0])
        except Exception:
            found = []
        for r in found:
            key = (int(r.x0), int(r.y0), int(r.x1), int(r.y1))
            if key not in seen:
                seen.add(key)
                rects.append(r)
    return sorted(rects, key=lambda r: r.y0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="nic nezapisovat")
    ap.add_argument("--only", type=int, action="append",
                    help="jen dané číslo otázky (lze opakovat)")
    args = ap.parse_args()

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    with_image = [q for q in questions if q.get("image")]
    if args.only:
        with_image = [q for q in with_image if q["pdf_number"] in set(args.only)]
    if not with_image:
        print("Žádné otázky s obrázkem ve výběru.")
        return 1

    doc = pymupdf.open(find_pdf())
    zoom = pymupdf.Matrix(RENDER_DPI / 72.0, RENDER_DPI / 72.0)

    by_page: dict[int, list[dict]] = {}
    for q in with_image:
        by_page.setdefault(q["source_page"], []).append(q)

    zmeny, beze_zmeny, chyby = [], 0, []

    for page_num, qs in sorted(by_page.items()):
        page = doc[page_num - 1]
        rects = image_rects(page)
        if not rects:
            chyby.append((page_num, "na stránce nejsou žádné obrázky"))
            continue

        # Značky VŠECH otázek na stránce — kvůli spodní hranici výřezu.
        on_page = {q["pdf_number"] for q in questions if q["source_page"] == page_num}
        tops = marker_tops(page, on_page)
        order = sorted(tops.items(), key=lambda kv: kv[1])

        used: set[int] = set()
        for idx, (num, top) in enumerate(order):
            nxt = order[idx + 1][1] if idx + 1 < len(order) else page.rect.height + 100
            mine = [(j, r) for j, r in enumerate(rects)
                    if j not in used and top - 5 <= r.y0 <= nxt]
            if not mine:
                continue
            used.update(j for j, _ in mine)
            if num not in {q["pdf_number"] for q in qs}:
                continue

            clip = question_image_clip([r for _, r in mine], page)
            out = IMAGES_DIR / f"q{num}.png"
            old = out.stat().st_size if out.exists() else 0
            old_dim = None
            if out.exists():
                try:
                    with Image.open(out) as im:
                        old_dim = im.size
                except Exception:
                    pass

            pix = page.get_pixmap(clip=clip, matrix=zoom, alpha=False)
            new_dim = (pix.width, pix.height)
            if args.dry_run:
                if old_dim and old_dim != new_dim:
                    zmeny.append((num, len(mine), old_dim, new_dim))
                else:
                    beze_zmeny += 1
                continue

            pix.save(str(out))
            try:
                with Image.open(out) as im:
                    im.save(out, "PNG", optimize=True)
            except Exception:
                pass
            if old_dim and old_dim != new_dim:
                zmeny.append((num, len(mine), old_dim, new_dim))
            else:
                beze_zmeny += 1
            del old

    doc.close()

    print(f"Otázek s obrázkem: {len(with_image)}   ·   pad {IMAGE_CLIP_PAD} bodů")
    print(f"Beze změny: {beze_zmeny}")
    if zmeny:
        print(f"Změněno: {len(zmeny)}")
        for num, n_img, old, new in zmeny:
            print(f"   č. {num:>4}: {n_img} obrázků   {old[0]}×{old[1]} -> {new[0]}×{new[1]}")
    if chyby:
        print(f"Problémy: {chyby}")
    if args.dry_run:
        print("\n(dry-run — nic se nezapsalo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
