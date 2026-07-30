"""Odkazy z otázek do e-Sbírky — konzistence dat.

Běží offline nad `data/law_refs.json`; na síť nechodí. Ověřuje, že odkazy míří
na skutečné otázky, mají tvar, který e-Sbírka používá, a že se kotva shoduje
s citovaným ustanovením (to je jediné, co se dá zkontrolovat bez sítě, ale chytí
to překlep i posun při přegenerování).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LAW_REFS = ROOT / "data" / "law_refs.json"
QUESTIONS = ROOT / "data" / "questions.json"

BASE = "https://e-sbirka.gov.cz/sb/2024/90/2026-01-01#"
REF_RE = re.compile(r"^§ \d+[a-z]?( odst\. \d+)?( písm\. [a-z]\))?( bod \d+)?$")


@pytest.fixture(scope="module")
def refs() -> dict:
    if not LAW_REFS.exists():
        pytest.skip("data/law_refs.json chybí — spusť `make law-links`")
    return json.loads(LAW_REFS.read_text(encoding="utf-8"))["otazky"]


@pytest.fixture(scope="module")
def question_numbers() -> set[int]:
    return {q["pdf_number"] for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}


def test_refs_point_to_existing_questions(refs, question_numbers) -> None:
    unknown = [n for n in refs if int(n) not in question_numbers]
    assert not unknown, f"odkazy na neexistující otázky: {unknown[:10]}"


def test_urls_have_official_shape(refs) -> None:
    bad = [(n, r["url"]) for n, r in refs.items() if not r["url"].startswith(BASE)]
    assert not bad, f"odkazy mimo e-Sbírku: {bad[:5]}"


def test_citations_are_well_formed(refs) -> None:
    bad = [(n, r["ref"]) for n, r in refs.items() if not REF_RE.match(r["ref"])]
    assert not bad, f"označení ustanovení v nečekaném tvaru: {bad[:5]}"


def test_anchor_matches_citation(refs) -> None:
    """„§ 7 písm. b) bod 2" musí odkazovat na #par_7-pism_b-bod_2."""
    for number, ref in refs.items():
        anchor = ref["url"].split("#", 1)[1]
        m = REF_RE.match(ref["ref"])
        assert m, ref["ref"]
        parts = ref["ref"].replace("§ ", "par_").replace(" odst. ", "-odst_")
        parts = parts.replace(" písm. ", "-pism_").replace(")", "").replace(" bod ", "-bod_")
        assert anchor == parts, (
            f"otázka #{number}: citace {ref['ref']!r} → čekána kotva {parts!r}, "
            f"ale je {anchor!r}"
        )


def test_every_ref_has_a_quote(refs) -> None:
    empty = [n for n, r in refs.items() if not r.get("quote", "").strip()]
    assert not empty, f"odkazy bez citace znění: {empty[:10]}"


def test_coverage_does_not_regress(refs) -> None:
    """Ke dni zavedení mělo odkaz 224 otázek. Výrazný propad = něco se rozbilo."""
    assert len(refs) >= 210, f"odkazů jen {len(refs)}, čekáno ~224"
