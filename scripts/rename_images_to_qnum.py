#!/usr/bin/env python3
"""Jednoraza migrace: prejmenuj images/<hash>.png na images/q<pdf_number>.png.

Aktualizuje i `image` pole v data/questions.json.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "images"
Q_JSON = ROOT / "data" / "questions.json"


def main():
    qs = json.loads(Q_JSON.read_text(encoding="utf-8"))

    renamed = 0
    skipped = 0
    missing: list[int] = []

    for q in qs:
        if not q.get("image"):
            continue
        old_rel = q["image"]            # "images/<hash>.png"
        old_path = ROOT / old_rel
        new_rel = f"images/q{q['pdf_number']}.png"
        new_path = ROOT / new_rel

        if not old_path.exists():
            # Already renamed from previous run?
            if new_path.exists():
                q["image"] = new_rel
                skipped += 1
                continue
            missing.append(q["pdf_number"])
            continue

        if old_path == new_path:
            skipped += 1
            continue

        # Rename
        old_path.rename(new_path)
        q["image"] = new_rel
        renamed += 1

    Q_JSON.write_text(
        json.dumps(qs, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Přejmenováno: {renamed}")
    print(f"Přeskočeno (už bylo OK): {skipped}")
    if missing:
        print(f"Chybějící soubory: {missing}")

    # Sanity check
    remaining_hash_files = [
        p for p in IMAGES.glob("*.png")
        if not p.name.startswith("q") or not p.stem[1:].isdigit()
    ]
    if remaining_hash_files:
        print(f"POZOR: zbylo {len(remaining_hash_files)} souborů se starým názvem:")
        for p in remaining_hash_files[:5]:
            print(f"  {p.name}")


if __name__ == "__main__":
    main()
