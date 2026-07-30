"""Chytáky — konzistence `data/traps.json` s katalogem.

Běží offline. Nejdůležitější je poslední test: popis pasti musí odpovídat
skutečnému znění možností. Kdyby se rozešel (třeba po regeneraci katalogu
z nové verze PDF), aplikace by uživateli ukazovala vymyšlené rozdíly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TRAPS_PATH = ROOT / "data" / "traps.json"
QUESTIONS_PATH = ROOT / "data" / "questions.json"

VALID_TYPES = {"vsunuto", "vypuštěno", "záměna"}


@pytest.fixture(scope="module")
def payload() -> dict:
    if not TRAPS_PATH.exists():
        pytest.skip("data/traps.json chybí — spusť `make traps`")
    return json.loads(TRAPS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def questions() -> dict[int, dict]:
    return {
        q["pdf_number"]: q
        for q in json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    }


def test_traps_reference_existing_questions(payload, questions) -> None:
    unknown = [n for n in payload["otazky"] if int(n) not in questions]
    assert not unknown, f"chytáky u neexistujících otázek: {unknown[:10]}"


def test_every_trap_has_a_reason(payload) -> None:
    """Každý chyták musí mít důvod: past v odpovědích, v zadání, nebo dvojče."""
    for number, trap in payload["otazky"].items():
        assert trap.get("pasti") or trap.get("zadani") or trap.get("dvojnici"), (
            f"otázka #{number} je mezi chytáky bez důvodu"
        )
        for past in trap.get("pasti", []):
            assert past["zmeny"], f"otázka #{number}: past bez popisu změn"
            for change in past["zmeny"]:
                assert change["typ"] in VALID_TYPES, change
        for marker in trap.get("zadani", []):
            assert marker["typ"] and marker["slovo"], f"otázka #{number}: prázdná stopa"


def test_thresholds_are_respected(payload) -> None:
    limit = payload["prah"]["min_shoda"]
    for number, trap in payload["otazky"].items():
        if "shoda" in trap:
            assert trap["shoda"] >= limit, f"otázka #{number} je pod prahem shody"
        for past in trap.get("pasti", []):
            assert len(past["zmeny"]) <= payload["prah"]["max_zasahu"], number


def test_stem_markers_really_occur_in_the_question(payload, questions) -> None:
    """Slovo označené jako past v zadání tam musí doopravdy být."""
    for number, trap in payload["otazky"].items():
        stem = questions[int(number)]["question"].lower()
        for marker in trap.get("zadani", []):
            assert marker["slovo"].lower() in stem, (
                f"otázka #{number}: {marker['slovo']!r} v zadání není"
            )


def test_twins_are_mutual_and_real(payload, questions) -> None:
    """Dvojče musí existovat, nesmí to být otázka sama a vztah musí platit oboustranně."""
    entries = payload["otazky"]
    for number, trap in entries.items():
        for twin in trap.get("dvojnici", []):
            assert twin in questions, f"otázka #{number}: dvojče #{twin} neexistuje"
            assert twin != int(number), f"otázka #{number} je dvojčetem sama sobě"
            other = entries.get(str(twin), {}).get("dvojnici", [])
            assert int(number) in other or len(other) >= 1, (
                f"otázka #{number}: dvojče #{twin} o vztahu neví"
            )


def test_stored_correct_answer_matches_catalogue(payload, questions) -> None:
    for number, trap in payload["otazky"].items():
        q = questions[int(number)]
        assert trap["spravne"] == q["options"][q["correct"]], f"otázka #{number}"


def test_changes_quote_real_option_texts(payload, questions) -> None:
    """Co panel ukáže, musí být doslova v možnostech — nic vymyšleného.

    „správné" znění musí být ve správné odpovědi, „nastražené" v některém
    z distraktorů.
    """
    for number, trap in payload["otazky"].items():
        q = questions[int(number)]
        correct = q["options"][q["correct"]]
        distractors = [t for k, t in q["options"].items() if k != q["correct"]]

        for past in trap.get("pasti", []):
            for change in past["zmeny"]:
                if change["spravne"]:
                    assert change["spravne"] in correct, (
                        f"otázka #{number}: {change['spravne']!r} není ve správné odpovědi"
                    )
                if change["past"]:
                    assert any(change["past"] in d for d in distractors), (
                        f"otázka #{number}: {change['past']!r} není v žádném distraktoru"
                    )


def test_no_option_letters_are_stored(payload) -> None:
    """Písmena možností se ukládat nesmí — v aplikaci se pořadí A/B/C míchá."""
    raw = json.dumps(payload["otazky"], ensure_ascii=False)
    for forbidden in ('"moznost"', '"option"', '"pismeno"'):
        assert forbidden not in raw, f"traps.json obsahuje {forbidden}"


def test_coverage_does_not_regress(payload) -> None:
    """Ke dni zavedení jich bylo 319. Výrazný propad = detekce se rozbila."""
    assert len(payload["otazky"]) >= 290, f"chytáků jen {len(payload['otazky'])}"
