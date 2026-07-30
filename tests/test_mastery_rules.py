"""Pravidlo zvládnutí oblasti.

Samotné „90 % z posledních 30" je zavádějící: Právo má 561 otázek, takže
třicet posledních odpovědí je z něj necelých 6 %. Dalo by se tedy oblast
„zvládnout" opakováním stejné hrstky otázek. Zdravotnické minimum má 38
otázek, tam těch třicet pokrývá skoro celou oblast a totéž číslo znamená
něco úplně jiného. Proto se vedle úspěšnosti hlídá i pokrytí.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ui.pages.mastery import (  # noqa: E402
    COVERAGE_PCT,
    SAMPLE_TARGET,
    THRESHOLD_PCT,
    is_mastered,
)


def test_uspesnost_bez_pokryti_nestaci():
    """Přesně ten případ z praxe: 561 otázek, viděno 33, 60 % z posledních 30."""
    assert not is_mastered(pct=95.0, n=30, coverage_pct=5.9)


def test_pokryti_bez_uspesnosti_nestaci():
    assert not is_mastered(pct=60.0, n=30, coverage_pct=100.0)


def test_maly_vzorek_nestaci_ani_pri_plnem_pokryti():
    """Pět odpovědí na pětiotázkovou oblast není zvládnutí."""
    assert not is_mastered(pct=100.0, n=5, coverage_pct=100.0)


def test_splneni_vsech_tri_podminek():
    """Zdravotnické minimum: 38 z 38 otázek, 96,7 % z posledních 30."""
    assert is_mastered(pct=96.7, n=30, coverage_pct=100.0)


def test_hranice_jsou_inkluzivni():
    assert is_mastered(pct=THRESHOLD_PCT, n=SAMPLE_TARGET, coverage_pct=COVERAGE_PCT)
    assert not is_mastered(pct=THRESHOLD_PCT - 0.1, n=SAMPLE_TARGET, coverage_pct=COVERAGE_PCT)
    assert not is_mastered(pct=THRESHOLD_PCT, n=SAMPLE_TARGET - 1, coverage_pct=COVERAGE_PCT)
    assert not is_mastered(pct=THRESHOLD_PCT, n=SAMPLE_TARGET, coverage_pct=COVERAGE_PCT - 0.1)


def test_prazdna_oblast_neni_zvladnuta():
    assert not is_mastered(pct=0.0, n=0, coverage_pct=0.0)


def test_opakovani_hrstky_otazek_nestaci():
    """Sto odpovědí na deset otázek z pětisetotázkové oblasti = 2 % pokrytí."""
    assert not is_mastered(pct=100.0, n=SAMPLE_TARGET, coverage_pct=10 / 500 * 100)
