"""Generátor tematických okruhů (scripts/gen_okruhy.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import gen_okruhy as go  # noqa: E402

VYKLADY = ROOT / "data" / "vyklady-okruhy.json"


@pytest.fixture(scope="module")
def par_info():
    return go.parse_law_structure()


@pytest.fixture(scope="module")
def questions():
    return json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def refs():
    return json.loads((ROOT / "data" / "law_refs.json").read_text(encoding="utf-8"))["otazky"]


@pytest.fixture(scope="module")
def traps():
    return json.loads((ROOT / "data" / "traps.json").read_text(encoding="utf-8"))["otazky"]


def test_struktura_zakona_se_precte(par_info):
    assert len(par_info) > 140, f"jen {len(par_info)} paragrafů — parser struktury selhal"
    s_nadpisem = sum(1 for v in par_info.values() if v["nadpis"])
    assert s_nadpisem > 100, f"jen {s_nadpisem} paragrafů má nadpis"


def test_kazdy_paragraf_zna_svou_cast(par_info):
    bez = [n for n, v in par_info.items() if not v["cast"]]
    assert not bez, f"paragrafy bez zařazení do ČÁSTI: {bez[:10]}"


def test_nadpis_okruhu_neni_holy_marker(par_info):
    """`HLAVA I` bez názvu znamená, že se přeskočil prázdný řádek špatně."""
    holé = []
    for v in par_info.values():
        for level in (v["dil"], v["hlava"]):
            if level and "—" not in level:
                holé.append(level)
    assert not holé, f"úrovně bez názvu: {sorted(set(holé))[:5]}"


def test_vsechny_otazky_s_odkazem_maji_okruh(questions, refs, par_info):
    ztracene = []
    for q in questions:
        ref = refs.get(str(q["pdf_number"]))
        if not ref:
            continue
        m = go.RE_PAR_REF.match(ref["ref"])
        if not m or m.group(1) not in par_info:
            ztracene.append((q["pdf_number"], ref["ref"]))
    assert not ztracene, f"odkaz mimo strukturu zákona: {ztracene[:10]}"


def test_rodiny_dvojcat_jsou_symetricke(traps):
    """Union-find musí dát stejné id všem členům rodiny."""
    fam = go.twin_families(traps)
    assert fam, "žádné rodiny — traps.json je prázdný?"
    for key, rec in traps.items():
        for other in rec.get("dvojnici", []):
            assert fam[int(key)] == fam[int(other)], (
                f"otázky {key} a {other} mají být v jedné rodině"
            )


def test_vyklady_okruhu_maji_platny_json():
    if not VYKLADY.exists():
        pytest.skip("data/vyklady-okruhy.json zatím není")
    obj = json.loads(VYKLADY.read_text(encoding="utf-8"))
    assert isinstance(obj, dict)
    for key, value in obj.items():
        if key.startswith("_"):
            continue
        assert isinstance(value, str) and value.strip(), f"prázdný výklad u {key!r}"


def test_zadny_vyklad_neni_osirely(questions, refs, par_info):
    """Výklad s klíčem mimo existující okruhy by se nikde neobjevil.

    Přesně tohle se stalo při psaní prvních výkladů — klíč se lišil o ČÁST
    a text se tiše ztratil.
    """
    if not VYKLADY.exists():
        pytest.skip("data/vyklady-okruhy.json zatím není")
    vyklady = json.loads(VYKLADY.read_text(encoding="utf-8"))
    vyklady = {k for k in vyklady if not k.startswith("_")}

    znamé = set()
    for q in questions:
        ref = refs.get(str(q["pdf_number"]))
        m = go.RE_PAR_REF.match(ref["ref"]) if ref else None
        info = par_info.get(m.group(1)) if m else None
        if info:
            znamé.add(go.topic_breadcrumb(go.topic_key(info)))

    osirele = sorted(vyklady - znamé)
    assert not osirele, f"výklad k neexistujícímu okruhu: {osirele}"


def test_slug_je_pouzitelny_jako_jmeno_souboru():
    assert go.slug("Podmínky zbrojního oprávnění") == "podminky-zbrojniho-opravneni"
    assert go.slug("Střelnice") == "strelnice"
    assert go.slug("") == "okruh"
    assert "/" not in go.slug("Díl 1 / Díl 2")


def test_rozbity_json_je_hlasna_chyba(tmp_path):
    bad = tmp_path / "v.json"
    bad.write_text('{"a": "rovná " uvozovka"}', encoding="utf-8")
    with pytest.raises(go.DataError):
        go.load_json(bad, {})
