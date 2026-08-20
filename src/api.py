"""Čtecí JSON API — aby si aktuální stav mohl vzít nástroj, ne jen člověk.

K čemu to je: pustit na svůj postup AI a nechat si poradit, co doučit.
Bez tohohle by se musely statistiky opisovat ručně nebo exportovat.

Bezpečnost:
  * API je **vypnuté**, dokud není nastavený `PRO_ZBROJAK_API_TOKEN`.
    Zapomenutá proměnná tedy neznamená otevřená data, ale nedostupné API.
  * Jen čtení. Žádný endpoint nic nemění.
  * Token se posílá hlavičkou `Authorization: Bearer …`. Query parametr
    `?token=` je povolený kvůli nástrojům, které hlavičky neumí, ale
    zapisuje se do logů proxy — proto je hlavička doporučená.
  * Porovnání tokenu je v konstantním čase (`secrets.compare_digest`),
    aby se nedal uhodnout po znacích.
"""
from __future__ import annotations

import os
import secrets

from fastapi import HTTPException, Query, Request

from src.db import law_refs, patterns, traps
from src.db.questions import load_questions
from src.db.store import get_db, mistake_stats, stats_overall, stats_per_section
from src.learning import heatmap as hm
from src.learning import srs as srs_mod
from src.version import VERSION

SECTION_LABEL = {
    "pravo": "Právo",
    "provadeci_predpisy": "Prováděcí předpisy",
    "jine_predpisy": "Jiné předpisy",
    "nauka_o_zbranich": "Nauka o zbraních a střelivu",
    "zdravotni_minimum": "Zdravotnické minimum",
}


def token() -> str:
    return os.environ.get("PRO_ZBROJAK_API_TOKEN", "").strip()


def enabled() -> bool:
    return bool(token())


def _overit(request: Request, token_param: str | None) -> None:
    ocekavany = token()
    if not ocekavany:
        # Nenastavený token neznamená volný přístup, ale vypnuté API.
        raise HTTPException(404, "API není zapnuté (chybí PRO_ZBROJAK_API_TOKEN)")
    hlavicka = request.headers.get("authorization", "")
    dodany = (
        hlavicka[7:].strip() if hlavicka.lower().startswith("bearer ")
        else (token_param or "")
    )
    if not dodany or not secrets.compare_digest(dodany, ocekavany):
        raise HTTPException(401, "Neplatný token")


def _uzivatel(email: str | None) -> str:
    if email:
        return email.strip().lower()
    admini = [e.strip().lower() for e in os.environ.get("PRO_ZBROJAK_ADMINS", "").split(",") if e.strip()]
    if not admini:
        raise HTTPException(400, "Chybí ?email= a není nastavený žádný admin")
    return admini[0]


def register(app) -> None:
    """Zaregistruje endpointy na FastAPI instanci NiceGUI."""

    @app.get("/api")
    def _rozcestnik(request: Request, token: str | None = Query(None)):
        _overit(request, token)
        return {
            "verze": VERSION,
            "endpointy": {
                "/api/stav": "souhrn postupu — úspěšnost, oblasti, série",
                "/api/chyby": "otázky, kde uživatel chybuje, i se zněním a paragrafem",
                "/api/kontext": "vše podstatné v jednom balíku pro AI",
            },
            "parametry": {
                "email": "čí data (výchozí: první admin)",
                "limit": "kolik otázek vrátit (jen /api/chyby a /api/kontext)",
            },
        }

    @app.get("/api/stav")
    def _stav(request: Request, token: str | None = Query(None),
              email: str | None = Query(None)):
        _overit(request, token)
        return _sestav_stav(_uzivatel(email))

    @app.get("/api/chyby")
    def _chyby(request: Request, token: str | None = Query(None),
               email: str | None = Query(None), limit: int = Query(30, ge=1, le=300)):
        _overit(request, token)
        return {"uzivatel": _uzivatel(email),
                "chyby": _sestav_chyby(_uzivatel(email), limit)}

    @app.get("/api/kontext")
    def _kontext(request: Request, token: str | None = Query(None),
                 email: str | None = Query(None), limit: int = Query(20, ge=1, le=100)):
        _overit(request, token)
        who = _uzivatel(email)
        return {
            "pokyn": (
                "Tohle je skutečný postup jednoho člověka v přípravě na zkoušku "
                "odborné způsobilosti (ZOZ, zbrojní průkaz). Poraď, co doučit "
                "a v jakém pořadí. Vycházej z uvedených paragrafů; nedomýšlej "
                "lhůty ani počty, které tu nejsou."
            ),
            "hranice_uspechu": "26 správných z 30 (standardní oprávnění)",
            "stav": _sestav_stav(who),
            "nejcastejsi_chyby": _sestav_chyby(who, limit),
        }


def _sestav_stav(email: str) -> dict:
    db = get_db()
    otazky = load_questions()
    celkem = stats_overall(db, email)
    po_oblastech = stats_per_section(db, otazky, email)
    staty = mistake_stats(db, email)

    videno: dict[str, set] = {}
    for q in otazky:
        videno.setdefault(q.get("section") or "?", set())
    odpovezeno = {r["question_id"] for r in db.query(
        "SELECT DISTINCT question_id FROM attempts WHERE user_email=?", [email])}
    qid_sekce = {q["id"]: q.get("section") for q in otazky}
    for qid in odpovezeno:
        s = qid_sekce.get(qid)
        if s:
            videno[s].add(qid)

    return {
        "uzivatel": email,
        "otazek_v_katalogu": len(otazky),
        "pokusu": celkem["attempts"],
        "spravne": celkem["correct"],
        "uspesnost_pct": celkem["pct"],
        "dni_v_rade": hm.current_streak(db, email),
        "k_opakovani_dnes": len(srs_mod.due_today(db, email, limit=999)),
        "chybnych_otazek": len(staty),
        "oblasti": [
            {
                "oblast": SECTION_LABEL.get(k, k),
                "otazek": sum(1 for q in otazky if q.get("section") == k),
                "videno": len(videno.get(k, ())),
                "pokusu": v["attempts"],
                "uspesnost_pct": v["pct"],
            }
            for k, v in po_oblastech.items()
        ],
    }


def _sestav_chyby(email: str, limit: int) -> list[dict]:
    db = get_db()
    staty = mistake_stats(db, email)
    podle_id = {q["id"]: q for q in load_questions()}
    serazene = sorted(
        (qid for qid in staty if qid in podle_id),
        key=lambda qid: (-staty[qid]["chyb"], -staty[qid]["podil"]),
    )[:limit]

    out = []
    for qid in serazene:
        q = podle_id[qid]
        ref = law_refs.ref_for(q["pdf_number"])
        out.append({
            "cislo": q["pdf_number"],
            "oblast": SECTION_LABEL.get(q.get("section"), q.get("section")),
            "zadani": q["question"],
            "spravna_odpoved": q["options"][q["correct"]],
            "chyb": staty[qid]["chyb"],
            "pokusu": staty[qid]["pokusu"],
            "ustanoveni": ref["ref"] if ref else None,
            "zneni_zakona": ref.get("quote") if ref else None,
            "odkaz": ref["url"] if ref else None,
            "je_chytak": bool(traps.trap_for(q["pdf_number"])),
            "vzorce": [
                p["nazev"] for p in patterns.rules()
                if q["pdf_number"] in p.get("otazky", [])
            ],
        })
    return out
