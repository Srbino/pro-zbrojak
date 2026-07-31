"""Vzorce v testu — pravidla a jejich výjimky.

Hlídá dvě věci:
  * čísla v `data/patterns.json` opravdu sedí s katalogem (spočítá se to znovu),
  * pravidlo je lepší než náhoda — jinak nemá na stránce co dělat.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import gen_patterns as gp  # noqa: E402

from src.db import patterns as pat  # noqa: E402

QUESTIONS = ROOT / "data" / "questions.json"


@pytest.fixture(scope="module")
def questions():
    return json.loads(QUESTIONS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def by_num(questions):
    return {q["pdf_number"]: q for q in questions}


def test_pravidla_existuji():
    assert pat.count() >= 1, "žádná pravidla — spusť `make patterns`"


def test_kazde_pravidlo_ma_povinne_udaje():
    for p in pat.rules():
        for klic in ("id", "nazev", "typ", "pravidlo", "proc", "pouzito",
                     "spolehlivost", "otazky", "vyjimky"):
            assert klic in p, f"{p.get('id')} nemá {klic}"
        assert p["typ"] in ("zuz", "vyluc")


def test_pravidlo_je_lepsi_nez_nahoda():
    """Pravidlo na úrovni náhody na stránku nepatří — mátlo by."""
    for p in pat.rules():
        assert p["spolehlivost"] > p["zaklad"] + 0.05, (
            f"{p['id']}: {p['spolehlivost']} není dost nad {p['zaklad']}"
        )


def test_vyjimky_a_otazky_se_neprekryvaji():
    for p in pat.rules():
        assert not set(p["otazky"]) & set(p["vyjimky"]), (
            f"{p['id']}: otázka je zároveň případ i výjimka"
        )
        assert len(p["otazky"]) + len(p["vyjimky"]) == p["pouzito"]


def test_vsechna_cisla_otazek_existuji(by_num):
    for p in pat.rules():
        neznama = [n for n in p["otazky"] + p["vyjimky"] if n not in by_num]
        assert not neznama, f"{p['id']} odkazuje na neexistující otázky: {neznama[:5]}"


# --------------------------------------------------------------- přepočet

def test_podobna_dvojice_sedi_s_katalogem(questions, by_num):
    """Přepočítá pravidlo znovu a porovná s uloženými daty."""
    p = pat.rule("podobna-dvojice")
    assert p, "pravidlo chybí"
    otazky, vyjimky = [], []
    for q in questions:
        d = gp.podobna_dvojice(q)
        if not d:
            continue
        (otazky if q["correct"] in (d[0], d[1]) else vyjimky).append(q["pdf_number"])
    assert sorted(otazky) == p["otazky"]
    assert sorted(vyjimky) == p["vyjimky"]


def test_vylucovaci_pravidla_sedi_s_katalogem(questions):
    for p in pat.rules():
        if p["typ"] != "vyluc":
            continue
        vzory = tuple(p["vzory"])
        otazky, vyjimky = [], []
        for q in questions:
            skrtnuto = gp.vyluc_podle(q, vzory)
            if not skrtnuto or len(skrtnuto) == len(q["options"]):
                continue
            (vyjimky if q["correct"] in skrtnuto else otazky).append(q["pdf_number"])
        assert sorted(otazky) == p["otazky"], f"{p['id']}: nesedí případy"
        assert sorted(vyjimky) == p["vyjimky"], f"{p['id']}: nesedí výjimky"


def test_vyjimka_opravdu_porusuje_pravidlo(questions, by_num):
    """U výjimky musí pravidlo skutečně selhat — jinak by se cvičilo nazdařbůh."""
    p = pat.rule("v-ramci")
    assert p
    for num in p["vyjimky"]:
        q = by_num[num]
        skrtnuto = gp.vyluc_podle(q, tuple(p["vzory"]))
        assert q["correct"] in skrtnuto, (
            f"otázka {num} je vedená jako výjimka, ale pravidlo ji neškrtá"
        )


def test_pravidlo_plati_u_uvedenych_otazek(questions, by_num):
    p = pat.rule("v-ramci")
    for num in p["otazky"][:20]:
        q = by_num[num]
        skrtnuto = gp.vyluc_podle(q, tuple(p["vzory"]))
        assert skrtnuto and q["correct"] not in skrtnuto


# --------------------------------------------------------------- ostatní

def test_seznam_nefunkcnich_je_vyplneny():
    """Bez něj by si každý zkusil „nejdelší odpověď" a přišel na to sám, jen dráž."""
    n = pat.not_working()
    assert len(n) >= 5
    for item in n:
        assert 0 < item["uspesnost"] < 0.5, item
        assert item["pozn"]


def test_exception_numbers_bez_id_vrati_vse():
    vsechny = pat.exception_numbers()
    soucet = set()
    for p in pat.rules():
        soucet |= pat.exception_numbers(p["id"])
    assert vsechny == soucet


def test_neznamé_pravidlo_nevrati_nic():
    assert pat.rule("neexistuje") is None
    assert pat.exception_numbers("neexistuje") == set()
