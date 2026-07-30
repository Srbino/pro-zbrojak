"""Generátor studijní příručky (scripts/gen_prirucka.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import gen_prirucka as gp  # noqa: E402


@pytest.fixture(scope="module")
def data():
    return gp.load_all()


@pytest.fixture(scope="module")
def questions(data):
    return data[0]


def _one(questions, number: int) -> dict:
    return next(q for q in questions if q["pdf_number"] == number)


def test_data_soubory_se_nactou(data):
    questions, refs, traps, vyklady = data
    assert len(questions) == 837
    assert refs, "chybí data/law_refs.json"
    assert traps, "chybí data/traps.json"


def test_blok_obsahuje_zadani_odpoved_i_moznosti(data):
    questions, refs, traps, vyklady = data
    q = _one(questions, 6)
    md = gp.render_question(q, refs, traps, vyklady)

    assert "### Otázka 6" in md
    assert f"**Správná odpověď — {q['correct']})**" in md
    # celé znění správné odpovědi, ne jen písmeno
    assert q["options"][q["correct"]] in md
    # i nesprávné možnosti, aby se dalo porovnat
    for key, text in q["options"].items():
        assert text in md, f"chybí znění možnosti {key}"


def test_odkaz_na_paragraf_a_citace(data):
    questions, refs, traps, vyklady = data
    q = _one(questions, 2)
    md = gp.render_question(q, refs, traps, vyklady)
    ref = refs["2"]
    assert ref["ref"] in md
    assert ref["url"] in md
    assert ref["quote"][:60] in md


def test_chybejici_paragraf_se_prizna(data):
    """Otázka bez ověřeného odkazu to musí říct, ne mlčet."""
    questions, refs, traps, vyklady = data
    q = next(q for q in questions if str(q["pdf_number"]) not in refs)
    md = gp.render_question(q, refs, traps, vyklady)
    assert "ověřený odkaz zatím nemáme" in md


def test_vyklad_se_vlozi_z_json(data):
    questions, refs, traps, vyklady = data
    assert "6" in vyklady, "ukázkový výklad k otázce 6 zmizel z data/vyklady.json"
    md = gp.render_question(_one(questions, 6), refs, traps, vyklady)
    assert vyklady["6"].splitlines()[0] in md
    assert gp.TODO not in md


def test_chybejici_vyklad_ma_zretelnou_znacku(data):
    questions, refs, traps, vyklady = data
    q = next(q for q in questions if str(q["pdf_number"]) not in vyklady)
    md = gp.render_question(q, refs, traps, vyklady)
    assert gp.TODO in md


def test_poznamkove_klice_nejsou_otazky(data):
    """Klíče jako `_pozn` jsou pro člověka, ne čísla otázek."""
    _, _, _, vyklady = data
    assert not [k for k in vyklady if k.startswith("_")]


def test_rozbity_json_je_hlasna_chyba(tmp_path):
    """Tiché spolknutí by vypadalo jako `výklady nikdo nenapsal`."""
    bad = tmp_path / "vyklady.json"
    bad.write_text('{"9": "rovná " uvozovka"}', encoding="utf-8")
    with pytest.raises(gp.DataError) as exc:
        gp.load_json(bad, {})
    assert "není platný JSON" in str(exc.value)


def test_chybejici_soubor_je_v_poradku(tmp_path):
    assert gp.load_json(tmp_path / "neni.json", {"x": 1}) == {"x": 1}


def test_prirucka_je_odvozeny_soubor(data):
    """Markdown se smí přegenerovat kdykoli — zdroj výkladů je JSON.

    Kdyby se výklady braly z markdownu, každé `make prirucka` by je smazalo.
    """
    questions, refs, traps, vyklady = data
    sample = [q for q in questions if q["pdf_number"] in (2, 6, 9)]
    first = gp.build(sample, refs, traps, vyklady, "test")
    second = gp.build(sample, refs, traps, vyklady, "test")
    assert first == second, "generátor není deterministický"
    assert vyklady["6"].splitlines()[0] in second


def test_jen_spravne_vynecha_distraktory(data):
    """Podklad k předčítání nesmí obsahovat nesprávné možnosti.

    Při poslechu není vidět, která z variant byla ta špatná — je snadné si
    zapamatovat zrovna ji.
    """
    questions, refs, traps, vyklady = data
    q = _one(questions, 6)
    md = gp.render_question(q, refs, traps, vyklady, jen_spravne=True)

    assert q["options"][q["correct"]] in md, "správná odpověď musí zůstat"
    for key, text in q["options"].items():
        if key != q["correct"]:
            assert text not in md, f"možnost {key} se do podcastu dostala"
    assert "Nesprávné možnosti" not in md
    assert "Chyták" not in md, "rozbor chytáku mluví o distraktorech"


def test_jen_spravne_zachova_zakon_i_vyklad(data):
    questions, refs, traps, vyklady = data
    md = gp.render_question(_one(questions, 6), refs, traps, vyklady, jen_spravne=True)
    assert refs["6"]["ref"] in md
    assert refs["6"]["quote"][:60] in md
    assert vyklady["6"].splitlines()[0] in md


def test_jen_spravne_neplni_soubor_hlaskami_o_chybejicim_vykladu(data):
    """Bez výkladu se blok vynechá — 833× stejná poznámka je pro předčítání šum."""
    questions, refs, traps, vyklady = data
    q = next(q for q in questions if str(q["pdf_number"]) not in vyklady)
    md = gp.render_question(q, refs, traps, vyklady, jen_spravne=True)
    assert gp.TODO not in md
    assert "ověřený odkaz zatím nemáme" not in md


def test_jen_spravne_ma_v_hlavicce_upozorneni(data):
    questions, refs, traps, vyklady = data
    md = gp.build([_one(questions, 6)], refs, traps, vyklady, "test", jen_spravne=True)
    assert "Jen správné odpovědi" in md


def _parse_klic(text: str) -> dict[int, str]:
    """Vytáhne dvojice číslo → písmeno z bloku ```…```."""
    out: dict[int, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1] in ("A", "B", "C"):
            out[int(parts[0])] = parts[1]
    return out


def test_klic_obsahuje_vsech_837_otazek(questions):
    klic = _parse_klic(gp.build_klic(questions, "test"))
    assert len(klic) == 837
    assert set(klic) == {q["pdf_number"] for q in questions}


def test_klic_sedi_s_katalogem(questions):
    """Každé písmeno se musí shodovat s `correct` v questions.json."""
    klic = _parse_klic(gp.build_klic(questions, "test"))
    rozdily = [
        (q["pdf_number"], q["correct"], klic[q["pdf_number"]])
        for q in questions if klic[q["pdf_number"]] != q["correct"]
    ]
    assert not rozdily, f"klíč nesedí s katalogem: {rozdily[:10]}"


def test_klic_neni_ovlivnen_michanim_moznosti(questions):
    """Klíč musí nést KANONICKÉ písmeno, ne to zobrazené.

    Aplikace pořadí A/B/C při zobrazení míchá (src/ui/shuffle.py). Kdyby se
    to promítlo sem, kontrola proti oficiální příručce by nevycházela.
    """
    from src.ui.shuffle import display_letter, option_order

    klic = _parse_klic(gp.build_klic(questions, "test"))
    lisi_se = 0
    for q in questions[:200]:
        order = option_order(q, user_email="kontrola@example.com")
        zobrazene = display_letter(order.index(q["correct"]))
        assert klic[q["pdf_number"]] == q["correct"]
        if zobrazene != q["correct"]:
            lisi_se += 1
    assert lisi_se > 0, "míchání se vůbec neprojevilo — test by nic nedokázal"


def test_klic_je_serazeny_vzestupne(questions):
    klic = gp.build_klic(questions, "test")
    cisla = [int(ln.split()[0]) for ln in klic.splitlines()
             if len(ln.split()) == 2 and ln.split()[0].isdigit()]
    assert cisla == sorted(cisla)


def test_klic_hlasi_rozlozeni_pismen(questions):
    text = gp.build_klic(questions, "test")
    for letter in ("A", "B", "C"):
        n = sum(1 for q in questions if q["correct"] == letter)
        assert f"**{letter}** {n}×" in text


def test_hlavicka_varuje_pred_editaci(data):
    questions, refs, traps, vyklady = data
    md = gp.build([_one(questions, 2)], refs, traps, vyklady, "test")
    assert "Needituj ho" in md
    assert "data/vyklady.json" in md


def test_json_vykladu_je_platny():
    """Skutečný data/vyklady.json v repu musí jít načíst."""
    path = ROOT / "data" / "vyklady.json"
    if not path.exists():
        pytest.skip("data/vyklady.json zatím není")
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(obj, dict)
    for key, value in obj.items():
        if key.startswith("_"):
            continue
        assert key.isdigit(), f"klíč {key!r} není číslo otázky"
        assert isinstance(value, str) and value.strip(), f"prázdný výklad u {key}"


def test_vyklady_odkazuji_na_existujici_otazky(data):
    questions, _, _, vyklady = data
    known = {str(q["pdf_number"]) for q in questions}
    unknown = [k for k in vyklady if k not in known]
    assert not unknown, f"výklad k neexistující otázce: {unknown}"
