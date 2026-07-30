"""
Regresní hlídač: lexikální shoda odpovědí se zněním zákona č. 90/2024 Sb.

Nekontroluje právní správnost — to skript neumí (viz docstring
`scripts/validate_vs_zakon.py`). Hlídá, že se PROTI DNEŠNÍMU STAVU nezhorší:
kdyby budoucí regenerace `data/questions.json` z nového PDF MV ČR rozbila
odpovědi nebo parser posunul přiřazení, počet doložených otázek klesne a počet
neshod stoupne — a test spadne.

Přeskočí se, když chybí PDF zákona nebo `pdftotext` (poppler).
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate_vs_zakon.py"

# Naměřený stav ke dni zavedení testu (837 otázek, zák. 90/2024 Sb. k 1. 1. 2026).
BASELINE_CONFIRMED = 227  # DOLOŽENO
BASELINE_MISMATCH = 42  # NESHODA
TOLERANCE = 5  # drobný posun při přeparsování PDF je v pořádku


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_vs_zakon", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_vs_zakon"] = module  # kvůli @dataclass
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def verdicts() -> Counter:
    validator = _load_validator()
    if not validator.ZAKON_PDF.exists() and not validator.ZAKON_TXT.exists():
        pytest.skip(f"chybí PDF zákona: {validator.ZAKON_PDF.name}")
    if not validator.ZAKON_TXT.exists() and not shutil.which("pdftotext"):
        pytest.skip("chybí pdftotext (poppler)")

    units = validator.build_units(validator.parse_law(validator.extract_law_text()))
    idf = validator.build_idf(units)
    questions = json.loads(validator.QUESTIONS.read_text(encoding="utf-8"))
    return Counter(validator.evaluate(q, units, idf).verdict for q in questions)


def test_law_parses_into_expected_structure() -> None:
    """Zákon má 152 paragrafů a 3 přílohy — když extrakce z PDF selže, pozná se to tady."""
    validator = _load_validator()
    if not validator.ZAKON_PDF.exists() and not validator.ZAKON_TXT.exists():
        pytest.skip(f"chybí PDF zákona: {validator.ZAKON_PDF.name}")
    if not validator.ZAKON_TXT.exists() and not shutil.which("pdftotext"):
        pytest.skip("chybí pdftotext (poppler)")

    sections = validator.parse_law(validator.extract_law_text())
    paragraphs = [s for s in sections if s.label.startswith("§")]
    annexes = [s for s in sections if s.label.startswith("Příloha")]

    assert len(paragraphs) == 152, f"očekáváno 152 §, nalezeno {len(paragraphs)}"
    assert len(annexes) == 3, f"očekávány 3 přílohy, nalezeno {len(annexes)}"
    assert all(s.text.strip() for s in sections), "některý blok zákona vyšel prázdný"


def test_confirmed_count_does_not_regress(verdicts: Counter) -> None:
    confirmed = verdicts["DOLOŽENO"]
    assert confirmed >= BASELINE_CONFIRMED - TOLERANCE, (
        f"doložených otázek ubylo: {confirmed} < {BASELINE_CONFIRMED - TOLERANCE}. "
        "Zkontroluj, jestli se nezměnily odpovědi v data/questions.json."
    )


def test_mismatch_count_does_not_grow(verdicts: Counter) -> None:
    mismatch = verdicts["NESHODA"]
    assert mismatch <= BASELINE_MISMATCH + TOLERANCE, (
        f"neshod se zákonem přibylo: {mismatch} > {BASELINE_MISMATCH + TOLERANCE}. "
        "Pusť `make validate-zakon` a projdi nové případy ručně."
    )


def test_paragraph_splits_into_units() -> None:
    """§ 7 musí jít rozebrat až na písmena podle kategorií a jejich body.

    Na tom stojí rozlišení otázek typu „osobou oprávněnou nakládat se zbraní
    kategorie R2 není…" — v celém § jsou doslova všechny nabízené možnosti, jen
    každá pod jinou kategorií.
    """
    validator = _load_validator()
    if not validator.ZAKON_PDF.exists() and not validator.ZAKON_TXT.exists():
        pytest.skip(f"chybí PDF zákona: {validator.ZAKON_PDF.name}")
    if not validator.ZAKON_TXT.exists() and not shutil.which("pdftotext"):
        pytest.skip("chybí pdftotext (poppler)")

    sections = validator.parse_law(validator.extract_law_text())
    s7 = next(s for s in sections if s.label == "§ 7")
    units = {u.label: u for u in validator.split_units(s7)}

    assert "§ 7 písm. b)" in units, "písmena § 7 se nerozpadla"
    assert units["§ 7 písm. b)"].own.strip() == "R2"
    assert "§ 7 písm. b) bod 2" in units, "body pod písmenem se nerozpadly"
    # návětí se dědí, aby bod dával smysl i vytržený z kontextu
    assert "Osobou oprávněnou" in units["§ 7 písm. b) bod 2"].lead
    # text nadřazené úrovně obsahuje i podstrom
    assert "zbrojní licence skupiny ZL1" in units["§ 7 písm. b)"].text


def test_trap_diff_finds_the_inserted_word() -> None:
    """Chyták = jedno vsunuté slovo. Diff ho musí ukázat, a nic víc."""
    validator = _load_validator()
    zakon = "palná zbraň, plynová zbraň a další zařízení nebo přístroj"
    chytak = "palná zbraň, plynová zbraň, chladná zbraň a další zařízení nebo přístroj"
    diffs = validator.trap_diff(zakon, chytak)

    assert len(diffs) == 1, f"očekáván jeden rozdíl, nalezeno {diffs}"
    op, _, inserted = diffs[0]
    assert op == "insert"
    assert "chladná" in inserted


def test_membership_negation_is_inverted() -> None:
    """Otázky typu „mezi X nepatří" se musí vyhodnocovat obráceně."""
    validator = _load_validator()
    assert validator.MEMBERSHIP_NEGATION_RE.search("Mezi regulované součásti nepatří:")
    assert not validator.MEMBERSHIP_NEGATION_RE.search("Zbraní je pro účely zákona:")


def test_alphanumeric_codes_survive_tokenization() -> None:
    """Kategorie zbraní (R1, ZL2, S4…) se nesmí rozpadnout na písmeno a číslo."""
    validator = _load_validator()
    tokens = validator.tokenize("Zbraně kategorie R1, R2 a ZL2.")
    assert "r1" in tokens and "r2" in tokens and "zl2" in tokens


def test_czech_numerals_normalize_to_digits() -> None:
    """„pěti let" v otázce a „5 let" v zákoně musí být totéž."""
    validator = _load_validator()
    assert validator.tokenize("po dobu pěti let") == ["po", "dobu", "5", "let"]
